#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import configparser
import errno
import multiprocessing
import os
import shutil
import signal

from shipmi import config as shipmi_config
from shipmi import exception
from shipmi import log
from shipmi import utils
from shipmi.provider import get_provider
from shipmi.vbmc import VirtualBMC

LOG = log.get_logger()

# BMC status
RUNNING = 'running'
DOWN = 'down'
ERROR = 'error'

DEFAULT_SECTION = 'VirtualBMC'

CONF = shipmi_config.get_config()


class VirtualBMCManager(object):
    VBMC_OPTIONS = ['username', 'password', 'address', 'port', 'name', 'provider', 'comment', 'active']

    def __init__(self):
        super(VirtualBMCManager, self).__init__()
        self.config_dir = CONF['default']['config_dir']
        self._running_virtualbmcs = {}

    def _parse_config(self, name):
        config_path = os.path.join(self.config_dir, name, 'config')
        if not os.path.exists(config_path):
            raise exception.VirtualBMCNotFound(name=name)

        try:
            config = configparser.ConfigParser()
            config.read(config_path)

            bmc = {}
            for item in self.VBMC_OPTIONS:
                try:
                    value = config.get(DEFAULT_SECTION, item)
                except configparser.NoOptionError:
                    value = None

                bmc[item] = value

            # Port needs to be int
            bmc['port'] = config.getint(DEFAULT_SECTION, 'port')

            return bmc

        except OSError:
            raise exception.VirtualBMCNotFound(name=name)

    def _store_config(self, **options):
        config = configparser.ConfigParser()
        config.add_section(DEFAULT_SECTION)

        for option, value in options.items():
            if value is not None:
                config.set(DEFAULT_SECTION, option, str(value))

        config_path = os.path.join(
            self.config_dir, options['name'], 'config'
        )

        with open(config_path, 'w') as f:
            config.write(f)

    def _vbmc_enabled(self, name, lets_enable=None, config=None):
        if not config:
            config = self._parse_config(name)

        try:
            currently_enabled = utils.str2bool(config['active'])

        except Exception:
            currently_enabled = False

        if (lets_enable is not None
                and lets_enable != currently_enabled):
            config.update(active=lets_enable)
            self._store_config(**config)
            currently_enabled = lets_enable

        return currently_enabled

    def _sync_vbmc_states(self, shutdown=False):
        """Starts/stops virtual BMC instances

        Walks over virtual BMC instances configuration, starts
        enabled but dead instances, kills non-configured
        but alive ones.
        """

        def vbmc_runner(bmc_config):
            # The manager process installs a signal handler for SIGTERM to
            # propagate it to children. Return to the default handler.
            signal.signal(signal.SIGTERM, signal.SIG_DFL)

            show_passwords = CONF['default']['show_passwords']

            if show_passwords:
                show_options = bmc_config
            else:
                show_options = utils.mask_dict_password(bmc_config)

            try:
                vbmc = VirtualBMC(**bmc_config)

            except Exception as ex:
                LOG.exception(
                    'Error running virtual BMC with configuration '
                    '%(opts)s: %(error)s', {'opts': show_options,
                                            'error': ex}
                )
                return

            try:
                vbmc.listen(timeout=CONF['ipmi']['session_timeout'])

            except Exception as ex:
                LOG.exception(
                    'Shutdown virtual BMC %(name)s, cause '
                    '%(error)s', {'name': show_options['name'],
                                  'error': ex}
                )
                return

        for name in os.listdir(self.config_dir):
            if not os.path.isdir(
                    os.path.join(self.config_dir, name)
            ):
                continue

            try:
                bmc_config = self._parse_config(name)

            except exception.VirtualBMCNotFound:
                continue

            if shutdown:
                lets_enable = False
            else:
                lets_enable = self._vbmc_enabled(
                    name, config=bmc_config
                )

            instance = self._running_virtualbmcs.get(name)

            if lets_enable:

                if not instance or not instance.is_alive():
                    instance = multiprocessing.Process(
                        name='shipmid-managing-%s' % name,
                        target=vbmc_runner,
                        args=(bmc_config,)
                    )

                    instance.daemon = True
                    instance.start()

                    self._running_virtualbmcs[name] = instance

                    LOG.info(
                        'Started virtual BMC instance %(name)s',
                        {'name': name}
                    )

                if not instance.is_alive():
                    LOG.debug(
                        'Found dead virtual BMC instance %(name)s (rc %(rc)s)',
                        {'name': name, 'rc': instance.exitcode}
                    )

            else:
                if instance:
                    if instance.is_alive():
                        instance.terminate()
                        LOG.info(
                            'Terminated virtual BMC instance %(name)s',
                            {'name': name}
                        )

                    self._running_virtualbmcs.pop(name, None)

    def _show(self, name):
        bmc_config = self._parse_config(name)

        show_passwords = CONF['default']['show_passwords']

        if show_passwords:
            show_options = bmc_config
        else:
            show_options = utils.mask_dict_password(bmc_config)

        instance = self._running_virtualbmcs.get(name)

        if instance and instance.is_alive():
            show_options['status'] = RUNNING
        elif instance and not instance.is_alive():
            show_options['status'] = ERROR
        else:
            show_options['status'] = DOWN

        return show_options

    def periodic(self, shutdown=False):
        self._sync_vbmc_states(shutdown)

    def add(self, username, password, port, address, name, comment, provider, **kwargs):

        get_provider(provider)

        config_path = os.path.join(self.config_dir, name)

        try:
            os.makedirs(config_path)
        except OSError as ex:
            if ex.errno == errno.EEXIST:
                return 1, str(ex)

            msg = ('Failed to create %(name)s. Error: %(error)s' % {'name': name, 'error': ex})
            LOG.error(msg)
            return 1, msg

        try:
            self._store_config(name=name,
                               username=username,
                               password=password,
                               port=str(port),
                               address=address,
                               provider=provider,
                               comment=comment,
                               active=False)
        except Exception as ex:
            shutil.rmtree(config_path)
            return 1, str(ex)

        return 0, ''

    def delete(self, name):
        config_path = os.path.join(self.config_dir, name)
        if not os.path.exists(config_path):
            raise exception.VirtualBMCNotFound(name=name)

        try:
            self.stop(name)
        except exception.ShIPMIError:
            pass

        shutil.rmtree(config_path)

        return 0, ''

    def start(self, name):
        try:
            bmc_config = self._parse_config(name)

        except Exception as ex:
            return 1, str(ex)

        if name in self._running_virtualbmcs:

            self._sync_vbmc_states()

            if name in self._running_virtualbmcs:
                LOG.warning(
                    'virtual BMC %(name)s already running, ignoring '
                    '"start" command' % {'name': name})
                return 0, ''

        try:
            self._vbmc_enabled(name,
                               config=bmc_config,
                               lets_enable=True)

        except Exception as e:
            LOG.exception('Failed to start virtual BMC %s', name)
            return 1, ('Failed to start virtual BMC %(name)s. Error: '
                       '%(error)s' % {'name': name, 'error': e})

        self._sync_vbmc_states()

        return 0, ''

    def stop(self, name):
        try:
            self._vbmc_enabled(name, lets_enable=False)

        except Exception as ex:
            LOG.exception('Failed to stop virtual BMC %s', name)
            return 1, str(ex)

        self._sync_vbmc_states()

        return 0, ''

    def list(self):
        rc = 0
        tables = []
        try:
            for name in os.listdir(self.config_dir):
                if os.path.isdir(os.path.join(self.config_dir, name)):
                    tables.append(self._show(name))

        except OSError as e:
            if e.errno == errno.EEXIST:
                rc = 1

        return rc, tables

    def show(self, name):
        return 0, list(self._show(name).items())

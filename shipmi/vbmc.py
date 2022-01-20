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
import os.path
import subprocess
from time import sleep

import pyghmi.ipmi.bmc as bmc

from shipmi import log
from shipmi.exception import VirtualBMCCommandFailed
from shipmi.provider import get_provider

LOG = log.get_logger()


class VirtualBMC(bmc.Bmc):

    def __init__(self, username, password, port, address, name, provider, **kwargs):
        super(VirtualBMC, self).__init__({username: password},
                                         port=port, address=address)
        self.name = name
        self.provider_config = get_provider(provider)

    def cmdline(self, section, option, kwargs=None):
        cmd = self.provider_config.get(section, option)
        if not cmd:
            raise NotImplementedError

        workingdir = os.path.dirname(self.provider_config.path)
        substitutions = {'name': self.name}
        if kwargs:
            substitutions.update(kwargs)

        cmdline = ['sh', '-c', cmd % substitutions]
        LOG.debug('Cmdline arguments: %(cmdline)s', {'cmdline': cmdline})

        process = subprocess.run(cmdline,
                                 cwd=workingdir,
                                 stdout=subprocess.PIPE,
                                 universal_newlines=True)

        if process.returncode != 0:
            raise VirtualBMCCommandFailed(command=' '.join(cmdline), exitcode=process.returncode)

        output = process.stdout.strip()
        LOG.debug('Cmdline output   : %(output)s', {'output': output})
        return output

    def cold_reset(self):
        LOG.info('BMC reset called for VirtualBMC %(name)s', {'name': self.name})

    def power_off(self):
        LOG.info('Power off called for %(name)s', {'name': self.name})
        self.cmdline('POWER', 'off')

    def power_on(self):
        LOG.info('Power on called for %(name)s', {'name': self.name})
        self.cmdline('POWER', 'on')

    def power_cycle(self):
        self.power_off()
        for i in range(10):
            if self.get_power_state() == 'off':
                break
            else:
                sleep(1)

        self.power_on()

    def power_reset(self):
        LOG.info('Power reset called for %(name)s', {'name': self.name})
        self.cmdline('POWER', 'reset')

    def pulse_diag(self):
        LOG.info('Power diag called for %(name)s', {'name': self.name})
        self.cmdline('POWER', 'diag')

    def power_shutdown(self):
        LOG.info('Soft power off called for %(name)s', {'name': self.name})
        self.cmdline('POWER', 'shutdown')

    def get_power_state(self):
        LOG.info('Get power state called for %(name)s', {'name': self.name})
        return self.cmdline('POWER', 'status')

    def is_active(self):
        return self.get_power_state() == 'on'

    def get_boot_device(self):
        LOG.info('Get boot device called for %(name)s', {'name': self.name})
        boot_device = self.cmdline('BOOT', 'get')
        return boot_device

    def set_boot_device(self, bootdev):
        LOG.info('Set boot device called for %(name)s with boot device "%(bootdev)s"',
                 {'name': self.name, 'bootdev': bootdev})
        self.cmdline('BOOT', 'set', {'bootdev': bootdev})

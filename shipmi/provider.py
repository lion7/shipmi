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
import os
import pathlib

from shipmi.exception import ProviderMissingSection, ProviderMissingOption
from shipmi.exception import ProviderNotFound


class ProviderConfig(object):

    def __init__(self, paths):
        config = configparser.ConfigParser(interpolation=None)
        read_files = config.read(paths)
        if len(read_files) == 0:
            raise ProviderMissingOption(name='unknown', section=config.default_section, option='name')
        self.name = str(pathlib.Path(os.path.basename(read_files[0])).with_suffix(""))
        self._config = config
        self._validate()

    def _validate(self):
        if not self._config.has_section('BOOT'):
            raise ProviderMissingSection(name=self.name, section='BOOT')
        boot = self._config['BOOT']
        if 'get' not in boot:
            raise ProviderMissingOption(name=self.name, section='BOOT', option='get')
        if 'set' not in boot:
            raise ProviderMissingOption(name=self.name, section='BOOT', option='set')

        if not self._config.has_section('POWER'):
            raise ProviderMissingSection(name=self.name, section='POWER')
        power = self._config['POWER']
        if 'status' not in power:
            raise ProviderMissingOption(name=self.name, section='POWER', option='status')
        if 'on' not in power:
            raise ProviderMissingOption(name=self.name, section='POWER', option='on')
        if 'off' not in power:
            raise ProviderMissingOption(name=self.name, section='POWER', option='off')
        if 'diag' not in power:
            raise ProviderMissingOption(name=self.name, section='POWER', option='diag')
        if 'reset' not in power:
            raise ProviderMissingOption(name=self.name, section='POWER', option='reset')
        if 'shutdown' not in power:
            raise ProviderMissingOption(name=self.name, section='POWER', option='shutdown')

    def get(self, section, option):
        if not self._config.has_section(section):
            return None
        s = self._config[section]
        if option not in s:
            return None
        return s[option]

    def __getitem__(self, key):
        section, option = str.split(key, '.', 2)
        return self.get(section, option)


_PROVIDERS_PATHS = [
    os.environ.get('SHIPMI_PROVIDERS', ''),
    os.path.join(os.path.expanduser('~'), '.shipmi', 'providers'),
    '/etc/shipmi/providers'
]
_PROVIDERS = {}


def _discover_providers():
    if len(_PROVIDERS) == 0:
        for path in _PROVIDERS_PATHS:
            if os.path.exists(path):
                files = map(lambda file: os.path.join(path, file), os.listdir(path))
                files = filter(lambda file: file and str.endswith(file, '.conf'), files)
                files = list(files)
                if len(files) > 0:
                    provider = ProviderConfig(files)
                    _PROVIDERS[provider.name] = provider


def get_provider(name):
    if name and str.endswith(name, '.conf'):
        path = os.path.join(os.curdir, name)
        return ProviderConfig(path)
    else:
        _discover_providers()
        provider = _PROVIDERS.get(name)
        if provider:
            return provider
        else:
            raise ProviderNotFound(name=name)


def names():
    _discover_providers()
    return list(_PROVIDERS.keys())

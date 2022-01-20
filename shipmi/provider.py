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

from shipmi.exception import ProviderNotFound


class ProviderConfig(object):

    def __init__(self, file):
        self.name = str(pathlib.Path(file).with_suffix("").name)
        self.path = file
        config = configparser.ConfigParser(interpolation=None)
        read_files = config.read(file)
        if len(read_files) == 0:
            raise ProviderNotFound(name=self.name)
        self._config = config

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
    os.path.join(os.path.dirname(__file__), 'providers'),
    '/etc/shipmi/providers',
    os.path.join(os.path.expanduser('~'), '.shipmi', 'providers'),
    os.environ.get('SHIPMI_PROVIDERS', ''),
]
_PROVIDERS = {}


def discover_providers():
    global _PROVIDERS
    _PROVIDERS = {}
    files = []
    for path in _PROVIDERS_PATHS:
        if os.path.exists(path):
            for dirpath, _, filenames in os.walk(path):
                for file in filenames:
                    if str.endswith(file, '.conf'):
                        subpath = os.path.join(dirpath, file)
                        files.append(subpath)

    if len(files) > 0:
        for file in files:
            provider = ProviderConfig(file)
            _PROVIDERS[provider.name] = provider


def get_provider(name):
    if name and str.endswith(name, '.conf'):
        path = os.path.join(os.curdir, name)
        return ProviderConfig(path)
    else:
        if len(_PROVIDERS) == 0:
            discover_providers()
        provider = _PROVIDERS.get(name)
        if provider:
            return provider
        else:
            raise ProviderNotFound(name=name)


def names():
    if len(_PROVIDERS) == 0:
        discover_providers()
    return list(_PROVIDERS.keys())

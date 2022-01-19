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
import subprocess

import pyghmi.ipmi.bmc as bmc

from shipmi import log
from shipmi.exception import VirtualBMCCommandFailed
from shipmi.provider import get_provider

LOG = log.get_logger()

# Power states
POWEROFF = 0
POWERON = 1

# From the IPMI - Intelligent Platform Management Interface Specification
# Second Generation v2.0 Document Revision 1.1 October 1, 2013
# https://www.intel.com/content/dam/www/public/us/en/documents/product-briefs/ipmi-second-gen-interface-spec-v2-rev1-1.pdf
#
# Command failed and can be retried
IPMI_COMMAND_NODE_BUSY = 0xC0
# Invalid data field in request
IPMI_INVALID_DATA = 0xcc

# Boot devices
VALID_BOOT_DEVICES = [
    'network',
    'hd',
    'optical'
]


class VirtualBMC(bmc.Bmc):

    def __init__(self, username, password, port, address, name, provider, **kwargs):
        super(VirtualBMC, self).__init__({username: password},
                                         port=port, address=address)
        self.name = name
        self.provider_config = get_provider(provider)

    def cmdline(self, section, option, substitutions):
        cmdline = ['sh', '-c', self.provider_config.get(section, option) % substitutions]
        LOG.debug('Cmdline arguments: %(cmdline)s',
                  {'cmdline': cmdline})

        process = subprocess.run(cmdline,
                                 stdout=subprocess.PIPE,
                                 universal_newlines=True)

        if process.returncode != 0:
            raise VirtualBMCCommandFailed(command=' '.join(cmdline), exitcode=process.returncode)

        output = process.stdout.strip()
        LOG.debug('Cmdline output   : %(output)s',
                  {'output': output})
        return output

    def get_boot_device(self):
        LOG.debug('Get boot device called for %(name)s',
                  {'name': self.name})
        boot_device = self.cmdline('BOOT', 'get', {'name': self.name})
        LOG.debug('Got boot device: %(bootdev)s',
                  {'bootdev': boot_device})

        if boot_device not in VALID_BOOT_DEVICES:
            # Invalid data field in request
            return IPMI_INVALID_DATA

        return boot_device

    def set_boot_device(self, boot_device):
        LOG.debug('Set boot device called for %(name)s with boot device "%(bootdev)s"',
                  {'name': self.name, 'bootdev': boot_device})
        if boot_device not in VALID_BOOT_DEVICES:
            # Invalid data field in request
            return IPMI_INVALID_DATA

        self.cmdline('BOOT', 'set', {'name': self.name, 'boot_device': boot_device})

    def get_power_state(self):
        LOG.debug('Get power state called for %(name)s',
                  {'name': self.name})
        power_state = self.cmdline('POWER', 'status', {'name': self.name})
        if power_state == "0" or power_state == "off":
            return POWEROFF
        elif power_state == "1" or power_state == "on":
            return POWERON
        else:
            return IPMI_INVALID_DATA

    def pulse_diag(self):
        LOG.debug('Power diag called for %(name)s',
                  {'name': self.name})

        self.cmdline('POWER', 'diag', {'name': self.name})

    def power_off(self):
        LOG.debug('Power off called for %(name)s',
                  {'name': self.name})
        self.cmdline('POWER', 'off', {'name': self.name})

    def power_on(self):
        LOG.debug('Power on called for %(name)s',
                  {'name': self.name})
        self.cmdline('POWER', 'on', {'name': self.name})

    def power_shutdown(self):
        LOG.debug('Soft power off called for %(name)s',
                  {'name': self.name})
        self.cmdline('POWER', 'shutdown', {'name': self.name})

    def power_reset(self):
        LOG.debug('Power reset called for %(name)s',
                  {'name': self.name})
        self.cmdline('POWER', 'reset', {'name': self.name})

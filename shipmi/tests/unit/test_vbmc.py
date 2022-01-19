# Copyright 2016 Red Hat, Inc.
# All Rights Reserved.
#
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
from unittest import mock

from shipmi import vbmc
from shipmi.tests.unit import base
from shipmi.tests.unit import utils as test_utils


class VirtualBMCTestCase(base.TestCase):

    def setUp(self):
        super(VirtualBMCTestCase, self).setUp()
        vbmc_config = test_utils.get_vbmc_config()
        # NOTE(lucasagomes): pyghmi's Bmc does create a socket in the
        # constructor, so we need to mock it here
        mock.patch('pyghmi.ipmi.bmc.Bmc.__init__', lambda *args, **kwargs: None).start()
        mock.patch('shipmi.provider._PROVIDERS', test_utils.TEST_PROVIDERS).start()
        self.vbmc = vbmc.VirtualBMC(**vbmc_config)

    def test_get_boot_device(self):
        ret = self.vbmc.get_boot_device()

        self.assertEqual("optical", ret)

    def test_set_boot_device(self):
        for boot_device in vbmc.VALID_BOOT_DEVICES:
            self.vbmc.set_boot_device(boot_device)

    def test_set_boot_device_unknown_device_error(self):
        ret = self.vbmc.set_boot_device('device-foo-bar')
        self.assertEqual(vbmc.IPMI_INVALID_DATA, ret)

    def _test_get_power_state(self):
        ret = self.vbmc.get_power_state()
        self.assertEqual(vbmc.POWERON, ret)

    def test_pulse_diag(self):
        self.vbmc.pulse_diag()

    def test_power_off(self):
        self.vbmc.power_off()

    def test_power_on(self):
        self.vbmc.power_on()

    def test_power_reset(self):
        self.vbmc.power_reset()

    def test_power_shutdown(self):
        self.vbmc.power_shutdown()

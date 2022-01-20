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
import pathlib
import uuid
from unittest import mock

from pyghmi.ipmi import command

from shipmi import vbmc, provider
from shipmi.tests.unit import base
from shipmi.tests.unit import utils as test_utils


class VirtualBMCTestCase(base.TestCase):

    def setUp(self):
        super(VirtualBMCTestCase, self).setUp()
        vbmc_config = test_utils.get_vbmc_config(name=str(uuid.uuid4()))
        # NOTE(lucasagomes): pyghmi's Bmc does create a socket in the
        # constructor, so we need to mock it here
        mock.patch('pyghmi.ipmi.bmc.Bmc.__init__', lambda *args, **kwargs: None).start()
        with mock.patch('shipmi.provider._PROVIDERS_PATHS', test_utils.TEST_PROVIDERS_PATHS):
            provider.discover_providers()
        self.vbmc = vbmc.VirtualBMC(**vbmc_config)
        self.power_state_file = pathlib.Path(__file__).parent.joinpath('providers', self.vbmc.name + '.powerstate~')
        self.bootdev_file = pathlib.Path(__file__).parent.joinpath('providers', self.vbmc.name + '.bootdev~')
        self.addCleanup(self._cleanup_files)
        self._write_bootdev('default')
        self._write_power_state('off')

    def test_cold_reset(self):
        self.vbmc.cold_reset()

    def test_power_off(self):
        self.vbmc.power_off()
        self._assert_power_state('off')

    def test_power_on(self):
        self.vbmc.power_on()
        self._assert_power_state('on')

    def test_power_cycle(self):
        self._write_power_state('on')
        self.vbmc.power_cycle()
        self._assert_power_state('on')

    def test_power_reset(self):
        self.vbmc.power_reset()
        self._assert_power_state('reset')

    def test_pulse_diag(self):
        self.vbmc.pulse_diag()
        self._assert_power_state('diag')

    def test_power_shutdown(self):
        self.vbmc.power_shutdown()
        self._assert_power_state('shutdown')

    def test_get_power_state(self):
        for power_state in command.power_states.keys():
            self._write_power_state(power_state)
            ret = self.vbmc.get_power_state()
            self.assertEqual(power_state, ret)

    def test_is_active_true(self):
        self._write_power_state('on')
        ret = self.vbmc.is_active()
        self.assertEqual(True, ret)

    def test_is_active_false(self):
        self._write_power_state('off')
        ret = self.vbmc.is_active()
        self.assertEqual(False, ret)

    def test_get_boot_device(self):
        for bootdev in command.boot_devices.keys():
            self._write_bootdev(str(bootdev))
            ret = self.vbmc.get_boot_device()
            self.assertEqual(str(bootdev), ret)

    def test_set_boot_device(self):
        for bootdev in command.boot_devices.keys():
            self.vbmc.set_boot_device(bootdev)
            self._assert_bootdev(str(bootdev))

    def _cleanup_files(self):
        self.power_state_file.unlink()
        self.bootdev_file.unlink()

    def _write_power_state(self, power_state):
        self.power_state_file.write_text(power_state)

    def _write_bootdev(self, bootdev):
        self.bootdev_file.write_text(bootdev)

    def _assert_power_state(self, power_state):
        actual = self.power_state_file.read_text().strip()
        self.assertEqual(power_state, actual)

    def _assert_bootdev(self, bootdev):
        actual = self.bootdev_file.read_text().strip()
        self.assertEqual(bootdev, actual)

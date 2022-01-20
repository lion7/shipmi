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

import builtins
import configparser
import copy
import errno
import multiprocessing
import os
import shutil
from unittest import mock


from shipmi import exception, provider
from shipmi import manager
from shipmi.tests.unit import base
from shipmi.tests.unit import utils as test_utils

_CONFIG_PATH = '/foo'


class VirtualBMCManagerTestCase(base.TestCase):

    def setUp(self):
        super(VirtualBMCManagerTestCase, self).setUp()
        self.manager = manager.VirtualBMCManager()
        self.manager.config_dir = _CONFIG_PATH
        self.vbmc_config0 = test_utils.get_vbmc_config()
        self.vbmc_config1 = test_utils.get_vbmc_config(name='Patrick', port=321)
        self.name0 = self.vbmc_config0['name']
        self.name1 = self.vbmc_config1['name']
        self.path0 = os.path.join(_CONFIG_PATH, self.name0)
        self.path1 = os.path.join(_CONFIG_PATH, self.name1)
        self.add_params = {'username': 'admin', 'password': 'pass',
                           'port': '777', 'address': '::',
                           'name': 'Squidward Tentacles',
                           'provider': 'test',
                           'active': 'False'}
        with mock.patch('shipmi.provider._PROVIDERS_PATHS', test_utils.TEST_PROVIDERS_PATHS):
            provider._discover_providers()

    def _get_config(self, section, item):
        return self.vbmc_config0.get(item)

    @mock.patch.object(os.path, 'exists')
    @mock.patch.object(configparser, 'ConfigParser')
    def test__parse_config(self, mock_configparser, mock_exists):
        mock_exists.return_value = True
        config = mock_configparser.return_value
        config.get.side_effect = self._get_config
        config.getint.side_effect = self._get_config
        ret = self.manager._parse_config(self.name0)

        self.assertEqual(self.vbmc_config0, ret)
        config.getint.assert_called_once_with('VirtualBMC', 'port')
        mock_configparser.assert_called_once_with()

        expected_get_calls = [mock.call('VirtualBMC', i)
                              for i in ('username', 'password', 'address', 'port',
                                        'name', 'provider', 'active')]
        self.assertEqual(expected_get_calls, config.get.call_args_list)

    @mock.patch.object(os.path, 'exists')
    def test__parse_config_vbmc_not_found(self, mock_exists):
        mock_exists.return_value = False
        self.assertRaises(exception.VirtualBMCNotFound,
                          self.manager._parse_config, self.name0)
        mock_exists.assert_called_once_with(self.path0 + '/config')

    @mock.patch.object(builtins, 'open')
    @mock.patch.object(manager.VirtualBMCManager, '_parse_config')
    def _test__show(self, mock__parse_config, mock_open, expected=None):
        mock__parse_config.return_value = self.vbmc_config0
        f = mock.MagicMock()
        f.read.return_value = self.vbmc_config0['port']
        mock_open.return_value.__enter__.return_value = f

        if expected is None:
            expected = self.vbmc_config0.copy()
            expected['status'] = manager.DOWN

        ret = self.manager._show(self.name0)
        self.assertEqual(expected, ret)

    def test__show(self):
        conf = {'default': {'show_passwords': True}}
        with mock.patch('shipmi.manager.CONF', conf):
            self._test__show()

    def test__show_mask_passwords(self):
        conf = {'default': {'show_passwords': False}}
        with mock.patch('shipmi.manager.CONF', conf):
            expected = self.vbmc_config0.copy()
            expected['password'] = '***'
            expected['status'] = manager.DOWN
            self._test__show(expected=expected)

    @mock.mock_open()
    @mock.patch.object(configparser, 'ConfigParser')
    @mock.patch.object(os, 'makedirs')
    def test_add(self, mock_open, mock_configparser, mock_makedirs):
        config = mock_configparser.return_value
        params = copy.copy(self.add_params)
        self.manager.add(**params)

        expected_calls = [mock.call('VirtualBMC', i, self.add_params[i])
                          for i in self.add_params]
        self.assertEqual(sorted(expected_calls),
                         sorted(config.set.call_args_list))
        config.add_section.assert_called_once_with('VirtualBMC')
        config.write.assert_called_once_with(mock.ANY)
        mock_makedirs.assert_called_once_with(os.path.join(_CONFIG_PATH, self.add_params['name']))
        mock_configparser.assert_called_once_with()

    @mock.mock_open()
    @mock.patch.object(configparser, 'ConfigParser')
    @mock.patch.object(os, 'makedirs')
    def test_add_with_port_as_int(self, mock_open, mock_configparser, mock_makedirs):
        config = mock_configparser.return_value
        params = copy.copy(self.add_params)
        params['port'] = int(params['port'])
        self.manager.add(**params)

        expected_calls = [mock.call('VirtualBMC', i, self.add_params[i])
                          for i in self.add_params]
        self.assertEqual(sorted(expected_calls),
                         sorted(config.set.call_args_list))
        config.add_section.assert_called_once_with('VirtualBMC')
        config.write.assert_called_once_with(mock.ANY)
        mock_makedirs.assert_called_once_with(
            os.path.join(_CONFIG_PATH, self.add_params['name']))
        mock_configparser.assert_called_once_with()

    @mock.patch.object(os, 'makedirs')
    def test_add_vbmc_already_exist(self, mock_makedirs):
        os_error = OSError()
        os_error.errno = errno.EEXIST
        mock_makedirs.side_effect = os_error

        ret, _ = self.manager.add(**self.add_params)

        expected_ret = 1

        self.assertEqual(ret, expected_ret)

    @mock.patch.object(os, 'makedirs')
    def test_add_oserror(self, mock_makedirs):
        mock_makedirs.side_effect = OSError

        ret, _ = self.manager.add(**self.add_params)
        expected_ret = 1
        self.assertEqual(ret, expected_ret)

    @mock.patch.object(shutil, 'rmtree')
    @mock.patch.object(os.path, 'exists')
    @mock.patch.object(manager.VirtualBMCManager, 'stop')
    def test_delete(self, mock_stop, mock_exists, mock_rmtree):
        mock_exists.return_value = True
        self.manager.delete(self.name0)

        mock_exists.assert_called_once_with(self.path0)
        mock_stop.assert_called_once_with(self.name0)
        mock_rmtree.assert_called_once_with(self.path0)

    @mock.patch.object(os.path, 'exists')
    def test_delete_vbmc_not_found(self, mock_exists):
        mock_exists.return_value = False
        self.assertRaises(exception.VirtualBMCNotFound,
                          self.manager.delete, self.name0)
        mock_exists.assert_called_once_with(self.path0)

    @mock.mock_open()
    @mock.patch.object(manager.VirtualBMCManager, '_parse_config')
    @mock.patch.object(os.path, 'exists')
    @mock.patch.object(os.path, 'isdir')
    @mock.patch.object(os, 'listdir')
    @mock.patch.object(multiprocessing, 'Process')
    def test_start(self, mock_open, mock__parse_config, mock_exists, mock_isdir, mock_listdir, mock_process):
        conf = {'ipmi': {'session_timeout': 10},
                'default': {'show_passwords': False}}
        with mock.patch('shipmi.manager.CONF', conf):
            mock_listdir.return_value = [self.name0]
            mock_isdir.return_value = True
            mock_exists.return_value = True
            vbmc0_conf = self.vbmc_config0.copy()
            vbmc0_conf.update(active='False')
            mock__parse_config.return_value = vbmc0_conf
            file_handler = mock_open.return_value.__enter__.return_value
            self.manager.start(self.name0)
            mock__parse_config.assert_called_with(self.name0)
            self.assertEqual(file_handler.write.call_count, 9)

    @mock.mock_open()
    @mock.patch.object(manager.VirtualBMCManager, '_parse_config')
    @mock.patch.object(os.path, 'isdir')
    @mock.patch.object(os, 'listdir')
    def test_stop(self, mock_open, mock__parse_config, mock_listdir, mock_isdir):
        conf = {'ipmi': {'session_timeout': 10},
                'default': {'show_passwords': False}}
        with mock.patch('shipmi.manager.CONF', conf):
            mock_listdir.return_value = [self.name0]
            mock_isdir.return_value = True
            vbmc0_conf = self.vbmc_config0.copy()
            vbmc0_conf.update(active='True')
            mock__parse_config.return_value = vbmc0_conf
            file_handler = mock_open.return_value.__enter__.return_value
            self.manager.stop(self.name0)
            mock_isdir.assert_called_once_with(self.path0)
            mock__parse_config.assert_called_with(self.name0)
            self.assertEqual(file_handler.write.call_count, 9)

    @mock.patch.object(os.path, 'exists')
    def test_stop_vbmc_not_found(self, mock_exists):
        mock_exists.return_value = False
        ret = self.manager.stop(self.name0)
        expected_ret = 1, 'No virtual BMC with matching name "SpongeBob" was found'
        self.assertEqual(ret, expected_ret)
        mock_exists.assert_called_once_with(
            os.path.join(self.path0, 'config')
        )

    @mock.patch.object(os.path, 'isdir')
    @mock.patch.object(os, 'listdir')
    @mock.patch.object(manager.VirtualBMCManager, '_show')
    def test_list(self, mock__show, mock_listdir, mock_isdir):
        mock_isdir.return_value = True
        mock_listdir.return_value = (self.name0, self.name1)

        ret, _ = self.manager.list()
        expected_ret = 0
        self.assertEqual(ret, expected_ret)
        self.assertEqual(self.manager.config_dir, _CONFIG_PATH) # FIXME
        mock_listdir.assert_called_once_with(_CONFIG_PATH)
        expected_calls = [mock.call(self.path0),
                          mock.call(self.path1)]
        self.assertEqual(expected_calls, mock_isdir.call_args_list)
        expected_calls = [mock.call(self.name0),
                          mock.call(self.name1)]
        self.assertEqual(expected_calls, mock__show.call_args_list)

    @mock.patch.object(manager.VirtualBMCManager, '_show')
    def test_show(self, mock__show):
        self.manager.show(self.vbmc_config0)
        mock__show.assert_called_once_with(self.vbmc_config0)

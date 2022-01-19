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

import os
from unittest import mock

from shipmi import exception
from shipmi.tests.unit import base
from shipmi import utils


class MiscUtilsTestCase(base.TestCase):

    @mock.patch.object(os, 'kill')
    def test_is_pid_running(self, mock_kill):
        self.assertTrue(utils.is_pid_running(123))
        mock_kill.assert_called_once_with(123, 0)

    @mock.patch.object(os, 'kill')
    def test_is_pid_running_not_running(self, mock_kill):
        mock_kill.side_effect = OSError('boom')
        self.assertFalse(utils.is_pid_running(123))
        mock_kill.assert_called_once_with(123, 0)

    def test_str2bool(self):
        for b in ('TRUE', 'true', 'True'):
            self.assertTrue(utils.str2bool(b))

        for b in ('FALSE', 'false', 'False'):
            self.assertFalse(utils.str2bool(b))

        self.assertRaises(ValueError, utils.str2bool, 'bogus value')

    def test_mask_dict_password(self):
        input_dict = {'foo': 'bar', 'password': 'SpongeBob SquarePants'}
        output_dict = utils.mask_dict_password(input_dict)
        expected = {'foo': 'bar', 'password': '***'}
        self.assertEqual(expected, output_dict)


@mock.patch.object(utils, 'os')
class DetachProcessUtilsTestCase(base.TestCase):

    def test_detach_process(self, mock_os):

        # 2nd value > 0 so _exit get called and we can assert that we've
        # killed the parent's process
        mock_os.fork.side_effect = (0, 999)
        mock_os.devnull = os.devnull

        with utils.detach_process() as pid:
            self.assertEqual(0, pid)

        # assert fork() has been called twice
        expected_fork_calls = [mock.call()] * 2
        self.assertEqual(expected_fork_calls, mock_os.fork.call_args_list)

        mock_os.setsid.assert_called_once_with()
        mock_os.chdir.assert_called_once_with('/')
        mock_os.umask.assert_called_once_with(0)
        mock_os._exit.assert_called_once_with(0)

    def test_detach_process_fork_fail(self, mock_os):
        error_msg = 'Kare-a-tay!'
        mock_os.fork.side_effect = OSError(error_msg)

        with self.assertRaisesRegex(exception.DetachProcessError, error_msg):
            with utils.detach_process():
                pass

        mock_os.fork.assert_called_once_with()
        self.assertFalse(mock_os.setsid.called)
        self.assertFalse(mock_os.chdir.called)
        self.assertFalse(mock_os.umask.called)
        self.assertFalse(mock_os._exit.called)

    def test_detach_process_chdir_fail(self, mock_os):
        # 2nd value > 0 so _exit get called and we can assert that we've
        # killed the parent's process
        mock_os.fork.side_effect = (0, 999)

        error_msg = 'Fish paste!'
        mock_os.chdir.side_effect = Exception(error_msg)

        with self.assertRaisesRegex(exception.DetachProcessError, error_msg):
            with utils.detach_process():
                pass

        # assert fork() has been called twice
        expected_fork_calls = [mock.call()] * 2
        self.assertEqual(expected_fork_calls, mock_os.fork.call_args_list)

        mock_os.setsid.assert_called_once_with()
        mock_os.chdir.assert_called_once_with('/')
        mock_os._exit.assert_called_once_with(0)
        self.assertFalse(mock_os.umask.called)

    def test_detach_process_umask_fail(self, mock_os):
        # 2nd value > 0 so _exit get called and we can assert that we've
        # killed the parent's process
        mock_os.fork.side_effect = (0, 999)

        error_msg = 'Barnacles!'
        mock_os.umask.side_effect = Exception(error_msg)

        with self.assertRaisesRegex(exception.DetachProcessError, error_msg):
            with utils.detach_process():
                pass

        # assert fork() has been called twice
        expected_fork_calls = [mock.call()] * 2
        self.assertEqual(expected_fork_calls, mock_os.fork.call_args_list)

        mock_os.setsid.assert_called_once_with()
        mock_os.chdir.assert_called_once_with('/')
        mock_os._exit.assert_called_once_with(0)
        mock_os.umask.assert_called_once_with(0)

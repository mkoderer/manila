# Copyright 2016 Mirantis, Inc.
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
"""Unit tests for the Protocol helper module."""

import functools
import mock

from manila import exception
from manila.share.drivers.container import protocol_helper
from manila import test
from manila.tests.share.drivers.container.fakes import fake_share


class DockerCIFSHelperTestCase(test.TestCase):
    """Tests ContainerShareDriver"""

    def setUp(self):
        super(DockerCIFSHelperTestCase, self).setUp()
        self._helper = mock.Mock()
        self.fake_conf = mock.Mock()
        self.fake_conf.container_cifs_guest_ok = "yes"
        self.DockerCIFSHelper = protocol_helper.DockerCIFSHelper(
            self._helper, share=fake_share(), config=self.fake_conf)

    def fake_exec_sync(self, *args, **kwargs):
        kwargs['execute_arguments'].append(args)
        try:
            ret_val = kwargs['ret_val']
        except KeyError:
            ret_val = None
        return [ret_val]

    def test_create_share_guest_ok(self):
        expected_arguments = [
            ('fakeserver', ['net', 'conf', 'addshare', 'fakeshareid',
             '/shares/fakeshareid', 'writeable=y', 'guest_ok=y']),
            ('fakeserver', ['net', 'conf', 'setparm', 'fakeshareid',
             'browseable', 'yes']),
            ('fakeserver', ['net', 'conf', 'setparm', 'fakeshareid',
             'hosts allow', '127.0.0.1']),
            ('fakeserver', ['net', 'conf', 'setparm', 'fakeshareid',
             'read only', 'no']),
            ('fakeserver', ['net', 'conf', 'setparm', 'fakeshareid',
             'hosts deny', '0.0.0.0/0']),
            ('fakeserver', ['net', 'conf', 'setparm', 'fakeshareid',
             'create mask', '0755'])]
        actual_arguments = []
        self._helper.execute_sync = functools.partial(
            self.fake_exec_sync, execute_arguments=actual_arguments,
            ret_val=" fake 192.0.2.2/24 more fake \n" * 20)
        self.DockerCIFSHelper.share = fake_share()
        self.DockerCIFSHelper.create_share("fakeserver")
        self.assertEqual(expected_arguments.sort(), actual_arguments.sort())

    def test_create_share_guest_not_ok(self):
        self.DockerCIFSHelper.conf = mock.Mock()
        self.DockerCIFSHelper.conf.container_cifs_guest_ok = "no"
        expected_arguments = [
            ('fakeserver', ['net', 'conf', 'addshare', 'fakeshareid',
             '/shares/fakeshareid', 'writeable=y', 'guest_ok=n']),
            ('fakeserver', ['net', 'conf', 'setparm', 'fakeshareid',
             'browseable', 'yes']),
            ('fakeserver', ['net', 'conf', 'setparm', 'fakeshareid',
             'hosts allow', '192.0.2.2']),
            ('fakeserver', ['net', 'conf', 'setparm', 'fakeshareid',
             'read only', 'no']),
            ('fakeserver', ['net', 'conf', 'setparm', 'fakeshareid',
             'hosts deny', '0.0.0.0/0']),
            ('fakeserver', ['net', 'conf', 'setparm', 'fakeshareid',
             'create mask', '0755'])]
        actual_arguments = []
        self._helper.execute_sync = functools.partial(
            self.fake_exec_sync, execute_arguments=actual_arguments,
            ret_val=" fake 192.0.2.2/24 more fake \n" * 20)
        self.DockerCIFSHelper.share = fake_share()
        self.DockerCIFSHelper.create_share("fakeserver")
        self.assertEqual(expected_arguments.sort(), actual_arguments.sort())

    def test_delete_share(self):
        self.DockerCIFSHelper.share = fake_share()
        self.DockerCIFSHelper.delete_share("fakeserver")
        self.DockerCIFSHelper.container.execute_sync.assert_called_with(
            'fakeserver',
            ['net', 'conf', 'delshare', 'fakeshareid'])

    def test__deny_access_host_present(self):
        self._helper.execute_sync.side_effect = ['192.0.2.2', ""]
        self.DockerCIFSHelper.share = fake_share()
        self.DockerCIFSHelper._deny_access("fakeserver", "192.0.2.2")
        self.DockerCIFSHelper.container.execute_sync.assert_called_with(
            'fakeserver',
            ['net', 'conf', 'getparm', 'fakeshareid', 'hosts allow'])

    def test__deny_access_no_host(self):
        self._helper.execute_sync.side_effect = ['192.0.2.2', ""]
        self.DockerCIFSHelper.share = fake_share()
        self.DockerCIFSHelper._deny_access("fakeserver", "192.0.2.3")
        self.DockerCIFSHelper.container.execute_sync.assert_called_with(
            'fakeserver',
            ['net', 'conf', 'getparm', 'fakeshareid', 'hosts allow'])

    def test__allow_access_host_present(self):
        self._helper.execute_sync.side_effect = [['192.0.2.2'], ""]
        self.DockerCIFSHelper._allow_access("fakeshareid", "fakeserver",
                                            "192.0.2.2", "rw")
        self.DockerCIFSHelper.container.execute_sync.assert_called_with(
            'fakeserver',
            ['net', 'conf', 'getparm', 'fakeshareid', 'hosts allow'])

    def test__allow_access_no_host(self):
        self._helper.execute_sync.side_effect = [[''], ""]
        self.DockerCIFSHelper._allow_access("fakeshareid", "fakeserver",
                                            "192.0.2.2", "rw")
        self.DockerCIFSHelper.container.execute_sync.assert_called_with(
            'fakeserver',
            ['net', 'conf', 'setparm', 'fakeshareid', 'hosts allow',
             '192.0.2.2, '])

    def test_allow_access_ro_guest_ok(self):
        self.DockerCIFSHelper.conf = mock.Mock()
        self.DockerCIFSHelper.conf.container_cifs_guest_ok = "yes"
        self.DockerCIFSHelper._allow_access("fakeshareid", "fakeserver",
                                            "192.0.2.2", "ro")
        self.assertFalse(self._helper.execute_sync.called)

    def test_allow_access_ro_guest_not_ok(self):
        self.DockerCIFSHelper.conf = mock.Mock()
        self.DockerCIFSHelper.conf.container_cifs_guest_ok = "no"
        self.assertRaises(exception.ManilaException,
                          self.DockerCIFSHelper._allow_access, "fakeshareid",
                          "fakeserver", "192.0.2.2", "ro")

    def test_allow_user_access_ok(self):
        self.DockerCIFSHelper._allow_user_access("fakeshareid", "fakeserver",
                                                 "fakeuser", "ro")
        self.DockerCIFSHelper.container.execute_sync.assert_called_with(
            'fakeserver',
            ['net', 'conf', 'setparm', 'fakeshareid', 'read list', 'fakeuser'])

    def test_allow_user_access_not_ok(self):
        self.assertRaises(exception.InvalidShareAccessLevel,
                          self.DockerCIFSHelper._allow_user_access,
                          "fakeshareid", "fakeserver", "fakeuser", "rx")

    def test_update_access_access_rules_ok(self):
        allow_rules = [{
            'access_to': '192.0.2.2',
            'access_level': 'ro',
            'access_type': 'ip'
        }]
        self.mock_object(self.DockerCIFSHelper, "_allow_access")
        self.DockerCIFSHelper.update_access("fakeshareid", "fakeserver",
                                            allow_rules, [], [])
        self.DockerCIFSHelper._allow_access.assert_called_once_with(
            "fakeshareid",
            "fakeserver",
            "192.0.2.2",
            "ro")

    def test_update_access_access_rules_ok_user(self):
        allow_rules = [{
            'access_to': 'fakeuser',
            'access_level': 'ro',
            'access_type': 'user'
        }]
        self.mock_object(self.DockerCIFSHelper, "_allow_user_access")
        self.DockerCIFSHelper.update_access("fakeshareid", "fakeserver",
                                            allow_rules, [], [])
        self.DockerCIFSHelper._allow_user_access.assert_called_once_with(
            "fakeshareid",
            "fakeserver",
            "fakeuser",
            "ro")

    def test_update_access_access_rules_wrong_type(self):
        allow_rules = [{
            'access_to': '192.0.2.2',
            'access_level': 'ro',
            'access_type': 'fake'
        }]
        self.mock_object(self.DockerCIFSHelper, "_allow_access")
        self.assertRaises(exception.InvalidShareAccess,
                          self.DockerCIFSHelper.update_access, "fakeshareid",
                          "fakeserver", allow_rules, [], [])

    def test_update_access_add_rules_ok(self):
        add_rules = [{
            'access_to': '192.0.2.2',
            'access_level': 'ro',
            'access_type': 'ip'
        }]
        self.mock_object(self.DockerCIFSHelper, "_allow_access")
        self.DockerCIFSHelper.update_access("fakeshareid", "fakeserver", [],
                                            add_rules, [])
        self.DockerCIFSHelper._allow_access.assert_called_once_with(
            "fakeshareid",
            "fakeserver",
            "192.0.2.2",
            "ro")

    def test_update_access_add_rules_ok_user(self):
        add_rules = [{
            'access_to': 'fakeuser',
            'access_level': 'ro',
            'access_type': 'user'
        }]
        self.mock_object(self.DockerCIFSHelper, "_allow_user_access")
        self.DockerCIFSHelper.update_access("fakeshareid", "fakeserver", [],
                                            add_rules, [])
        self.DockerCIFSHelper._allow_user_access.assert_called_once_with(
            "fakeshareid",
            "fakeserver",
            "fakeuser",
            "ro")

    def test_update_access_add_rules_wrong_type(self):
        add_rules = [{
            'access_to': '192.0.2.2',
            'access_level': 'ro',
            'access_type': 'fake'
        }]
        self.mock_object(self.DockerCIFSHelper, "_allow_access")
        self.assertRaises(exception.InvalidShareAccess,
                          self.DockerCIFSHelper.update_access, "fakeshareid",
                          "fakeserver", [], add_rules, [])

    def test_update_access_delete_rules_ok(self):
        delete_rules = [{
            'access_to': '192.0.2.2',
            'access_level': 'ro',
            'access_type': 'ip'
        }]
        self.mock_object(self.DockerCIFSHelper, "_deny_access")
        self.DockerCIFSHelper.update_access("fakeshareid", "fakeserver", [],
                                            [], delete_rules)
        self.DockerCIFSHelper._deny_access.assert_called_once_with(
            "fakeserver",
            "192.0.2.2")

    def test_update_access_delete_rules_not_ok(self):
        delete_rules = [{
            'access_to': '192.0.2.2',
            'access_level': 'ro',
            'access_type': 'user'
        }]
        self.mock_object(self.DockerCIFSHelper, "_deny_access")
        self.DockerCIFSHelper.update_access("fakeshareid", "fakeserver", [],
                                            [], delete_rules)
        self.assertFalse(self.DockerCIFSHelper._deny_access.called)

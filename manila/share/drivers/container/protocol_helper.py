# Copyright (c) 2016 Mirantis, Inc.
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

import re

from oslo_log import log

from manila.common import constants as const
from manila import exception
from manila.i18n import _
from manila.i18n import _LW

LOG = log.getLogger(__name__)


class DockerCIFSHelper(object):
    def __init__(self, container_helper, *args, **kwargs):
        super(DockerCIFSHelper, self).__init__()
        self.share = kwargs.get("share")
        self.conf = kwargs.get("config")
        self.container = container_helper

    def create_share(self, server_id):
        share_name = self.share.share_id
        cmd = ["net", "conf", "addshare", share_name,
               "/shares/%s" % share_name, "writeable=y"]
        if self.conf.container_cifs_guest_ok == "yes":
            cmd.append("guest_ok=y")
        else:
            cmd.append("guest_ok=n")
        self.container.execute_sync(server_id, cmd)
        parameters = {
            "browseable": "yes",
            "create mask": "0755",
            "hosts deny": "0.0.0.0/0",
            "hosts allow": "127.0.0.1",
            "read only": "no",
        }
        for param, value in parameters.items():
            self.container.execute_sync(
                server_id,
                ["net", "conf", "setparm", share_name, param, value]
            )
        result = self.container.execute_sync(
            server_id,
            ["ip", "addr", "show", "eth0"]
        )[0].split('\n')[2]
        address = re.findall("\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", result)[0]
        location = "\\\\%(addr)s\\/shares/%(name)s" % {"addr": address,
                                                       "name": share_name}
        return location

    def delete_share(self, server_id):
        self.container.execute_sync(
            server_id,
            ["net", "conf", "delshare", self.share.share_id]
        )

    def _deny_access(self, server_id, host_to_deny):
        share_name = self.share.share_id
        allowed_hosts = self.container.execute_sync(
            server_id,
            ["net", "conf", "getparm", share_name, "hosts allow"]
        )[0]
        if allowed_hosts.count(host_to_deny) == 0:
            LOG.debug("Access for host %s is already denied.", host_to_deny)
            return
        pruned_hosts = filter(lambda x: not x.startswith(host_to_deny),
                              allowed_hosts.split())
        allowed_hosts = " ".join(pruned_hosts)
        self.container.execute_sync(
            server_id,
            ["net", "conf", "setparm", share_name, "hosts allow",
             allowed_hosts]
        )

    def _allow_access(self, share_name, server_id, host_to_allow,
                      access_level):
        if access_level == const.ACCESS_LEVEL_RO:
            msg_dict = {"host": host_to_allow, "share": share_name}
            if self.conf.container_cifs_guest_ok != "yes":
                raise exception.ManilaException(
                    _("Can't provide 'ro' access for %(host)s to %(share)s.") %
                    msg_dict)
            LOG.debug("Share %(share)s is accessible for %(host)s for reading "
                      "data." % msg_dict)
            return
        elif access_level == const.ACCESS_LEVEL_RW:
            allowed_hosts = self.container.execute_sync(
                server_id,
                ["net", "conf", "getparm", share_name, "hosts allow"]
            )[0]
            if allowed_hosts.count(host_to_allow) != 0:
                LOG.debug("Access for host %s is already allowed.",
                          host_to_allow)
                return

            allowed_hosts = ", ".join([host_to_allow, allowed_hosts])
            self.container.execute_sync(
                server_id,
                ["net", "conf", "setparm", share_name, "hosts allow",
                 allowed_hosts]
            )
        else:
            raise exception.InvalidShareAccessLevel(level=access_level)

    def _allow_user_access(self, share_name, server_id, user_to_allow,
                           access_level):
        if access_level == const.ACCESS_LEVEL_RO:
            access = 'read list'
        elif access_level == const.ACCESS_LEVEL_RW:
            access = 'valid users'
        else:
            raise exception.InvalidShareAccessLevel(level=access_level)
        self.container.execute_sync(
            server_id,
            ["net", "conf", "setparm", share_name, access,
             user_to_allow]
        )

    def update_access(self, share_name, server_id, access_rules,
                      add_rules=None, delete_rules=None):
        def _rule_updater(rules):
            for rule in rules:
                host_to_allow = rule['access_to']
                access_level = rule['access_level']
                access_type = rule['access_type']
                if access_type == 'ip':
                    self._allow_access(share_name, server_id, host_to_allow,
                                       access_level)
                elif access_type == 'user':
                    self._allow_user_access(share_name, server_id,
                                            rule['access_to'], access_level)
                else:
                    msg = _("Access type '%s' is not supported by the "
                            "driver.") % access_type
                    raise exception.InvalidShareAccess(reason=msg)
        if not (add_rules or delete_rules):
            # clean all hosts from allowed hosts list first.
            self.container.execute_sync(
                server_id,
                ["net", "conf", "setparm", share_name, "hosts allow", ""]
            )
            _rule_updater(access_rules or [])
            return
        _rule_updater(add_rules or [])
        for rule in delete_rules:
            host_to_deny = rule['access_to']
            access_type = rule['access_type']
            if access_type == 'ip':
                self._deny_access(server_id, host_to_deny)
            else:
                LOG.warning(_LW("Attempt to use access type %s has been "
                                "blocked.") % access_type)

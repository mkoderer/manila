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

import pdb

from oslo_config import cfg
from oslo_log import log

from manila.share import driver


LOG = log.getLogger(__name__)


NOOP_OPTS = [
    cfg.BoolOpt('noop_break_everywhere',
                default=False,
                help='User name for the EMC server.'),
]

CONF = cfg.CONF
CONF.register_opts(NOOP_OPTS)


class NoopDriver(driver.ShareDriver):

    def __init__(self, *args, **kwargs):
        self.configuration = kwargs.get('configuration', None)
        super(NoopDriver, self).__init__(True, *args, **kwargs)

    """Noop driver"""
    def create_share(self, context, share, share_server=None):
        """Is called to create share."""
        return "Cool/export/location"

    def create_share_from_snapshot(self, context, share, snapshot,
                                   share_server=None):
        """Is called to create share from snapshot."""
        if CONF.noop_break_everywhere:
            pdb.set_trace()
        else:
            pass

    def extend_share(self, share, new_size, share_server=None):
        """Is called to extend share."""
        if CONF.noop_break_everywhere:
            pdb.set_trace()
        else:
            pass

    def create_snapshot(self, context, snapshot, share_server=None):
        """Is called to create snapshot."""
        if CONF.noop_break_everywhere:
            pdb.set_trace()
        else:
            pass

    def delete_share(self, context, share, share_server=None):
        """Is called to remove share."""
        if CONF.noop_break_everywhere:
            pdb.set_trace()
        else:
            pass

    def delete_snapshot(self, context, snapshot, share_server=None):
        """Is called to remove snapshot."""
        if CONF.noop_break_everywhere:
            pdb.set_trace()
        else:
            pass

    def ensure_share(self, context, share, share_server=None):
        """Invoked to sure that share is exported."""
        if CONF.noop_break_everywhere:
            pdb.set_trace()
        else:
            pass

    def allow_access(self, context, share, access, share_server=None):
        """Allow access to the share."""
        if CONF.noop_break_everywhere:
            pdb.set_trace()
        else:
            pass

    def deny_access(self, context, share, access, share_server=None):
        """Deny access to the share."""
        if CONF.noop_break_everywhere:
            pdb.set_trace()
        else:
            pass

    def check_for_setup_error(self):
        """Check for setup error."""
        if CONF.noop_break_everywhere:
            pdb.set_trace()
        else:
            pass

    def do_setup(self, context):
        """Any initialization the share driver does while starting."""
        if CONF.noop_break_everywhere:
            pdb.set_trace()
        else:
            pass

    def get_network_allocations_number(self):
        """Returns number of network allocations for creating VIFs."""
        return 1

    def _setup_server(self, network_info, metadata=None):
        """Set up and configures share server with given network parameters."""
        if CONF.noop_break_everywhere:
            pdb.set_trace()
        else:
            pass

    def _teardown_server(self, server_details, security_services=None):
        """Teardown share server."""
        if CONF.noop_break_everywhere:
            pdb.set_trace()
        else:
            pass

# pylint: disable=wrong-import-position
#
# Copyright (c) 2017, Arista Networks, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#   Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
#
#   Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
#
#   Neither the name of Arista Networks nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# 'AS IS' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL ARISTA NETWORKS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
# IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

""" Unit tests for the CvpAPI class
"""
import unittest
from itertools import cycle
from cvprac.cvp_client import CvpClient
from cvprac.cvp_api import CvpApi


class TestAPI(unittest.TestCase):
    """Unit test cases for CvpAPI"""

    # pylint: disable=protected-access
    # pylint: disable=invalid-name
    # pylint: disable=too-many-statements

    def setUp(self):
        """Setup for CvpAPI unittests"""
        self.clnt = CvpClient()
        nodes = ["1.1.1.1"]
        self.clnt.nodes = nodes
        self.clnt.node_cnt = len(nodes)
        self.clnt.node_pool = cycle(nodes)
        self.api = CvpApi(self.clnt)

    def test_sanitize_warnings(self):
        """Test sanitization if warnings are split"""
        input = {
            "warnings": [
                "! Change will take effect only after switch reboot at line 11\\n\\n",
                "! \\nWARNING!\\nChanging TCAM profile will cause forwarding agent(s) to exit and restart.\\nAll traffic through the forwarding chip managed by the restarting\\nforwarding agent will be dropped.\\n at line 392",
                "! portfast should only be enabled on ports connected to a single host. Connecting hubs",
                "concentrators",
                "switches",
                "bridges",
                "etc. to this interface when portfast is enabled can cause temporary bridging loops. Use with CAUTION. at line 2\\n\\n",
                "! portfast should only be enabled on ports connected to a single host. Connecting hubs",
                "concentrators",
                "switches",
                "bridges",
                "etc. to this interface when portfast is enabled can cause temporary bridging loops. Use with CAUTION. at line 4\\n",
                "! portfast should only be enabled on ports connected to a single host. Connecting hubs, concentrators, switches, bridges, etc. to this interface when portfast is enabled can cause temporary bridging loops. Use with CAUTION. at line 6\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n",
                "! Interface does not exist. The configuration will not take effect until the module is inserted. at line 2799\\n\\n\\n\\n\\n\\n",
                "! portfast should only be enabled on ports connected to a single host. Connecting hubs, concentrators, switches, bridges, etc. to this interface when portfast is enabled can cause temporary bridging loops. Use with CAUTION. at line 1247\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n"

            ],
            "warningCount": 14,
            "errors": [
                {
                    "lineNo": " 6",
                    "error": "> ruter bgp 1512% Invalid input (at token 0: 'ruter') at line 6",
                }
            ],
            "errorCount": 1,
        }
        expected = {
            "warnings": [
                "! Change will take effect only after switch reboot at line 11\\n\\n",
                "! \\nWARNING!\\nChanging TCAM profile will cause forwarding agent(s) to exit and restart.\\nAll traffic through the forwarding chip managed by the restarting\\nforwarding agent will be dropped.\\n at line 392",
                "! portfast should only be enabled on ports connected to a single host. Connecting hubs, concentrators, switches, bridges, etc. to this interface when portfast is enabled can cause temporary bridging loops. Use with CAUTION. at line 2\\n\\n",
                "! portfast should only be enabled on ports connected to a single host. Connecting hubs, concentrators, switches, bridges, etc. to this interface when portfast is enabled can cause temporary bridging loops. Use with CAUTION. at line 4\\n",
                "! portfast should only be enabled on ports connected to a single host. Connecting hubs, concentrators, switches, bridges, etc. to this interface when portfast is enabled can cause temporary bridging loops. Use with CAUTION. at line 6\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n",
                "! Interface does not exist. The configuration will not take effect until the module is inserted. at line 2799\\n\\n\\n\\n\\n\\n",
                "! portfast should only be enabled on ports connected to a single host. Connecting hubs, concentrators, switches, bridges, etc. to this interface when portfast is enabled can cause temporary bridging loops. Use with CAUTION. at line 1247\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n"
            ],
            "warningCount": 7,
            "errors": [
                {
                    "lineNo": " 6",
                    "error": "> ruter bgp 1512% Invalid input (at token 0: 'ruter') at line 6",
                }
            ],
            "errorCount": 1,
        }
        assert self.api.sanitize_warnings(input) == expected

    def test_sanitize_warnings_skip(self):
        """Test sanitization if no warnings need changing"""
        input = {
            "result": [
                {
                    "output": "enter input line by line; when done enter one or more control-d\n\n> spanning-tree portfast\n! portfast should only be enabled on ports connected to a single host. Connecting hubs, concentrators, switches, bridges, etc. to this interface when portfast is enabled can cause temporary bridging loops. Use with CAUTION. at line 2\nCopy completed successfully.\n",
                    "messages": ["Copy completed successfully."],
                },
                {
                    "output": "! Command: show session-configuration named capiVerify-2002-f8a137cac96e11ed89be020000000000\n! device: tp-avd-leaf2 (vEOS-lab, EOS-4.29.1F)\n!\n! boot system flash:/vEOS-lab-4.29.1F.swi\n!\nno aaa root\n!\ntransceiver qsfp default-mode 4x10G\n!\nservice routing protocols model ribd\n!\nspanning-tree mode mstp\n!\ninterface Ethernet1\n   spanning-tree portfast\n!\ninterface Ethernet2\n!\ninterface Ethernet3\n!\ninterface Ethernet4\n!\ninterface Ethernet5\n!\ninterface Management1\n!\nno ip routing\n!\nend\n"
                },
            ],
            "warnings": [
                "! portfast should only be enabled on ports connected to a single host. Connecting hubs, concentrators, switches, bridges, etc. to this interface when portfast is enabled can cause temporary bridging loops. Use with CAUTION. at line 2"
            ],
            "id": "Arista-3-4826123409839743",
            "warningCount": 1,
            "jsonrpc": "2.0",
        }
        # The result should not change
        assert self.api.sanitize_warnings(input) == input

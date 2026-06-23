# pylint: disable=wrong-import-position,line-too-long
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
from unittest.mock import patch
from cvprac.cvp_client import CvpClient
from cvprac.cvp_api import CvpApi, sanitize_warnings
from cvprac.cvp_client_errors import CvpApiError


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
        test_input = {
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
        self.assertEqual(sanitize_warnings(test_input), expected)

    def test_sanitize_warnings_skip(self):
        """Test sanitization if no warnings need changing"""
        test_input = {
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
        self.assertEqual(sanitize_warnings(test_input), test_input)

    @patch.object(CvpApi, 'change_control_get_one')
    @patch.object(CvpClient, 'post')
    def test_change_control_approve_raises_on_task_errors(self, mock_post, mock_get_one):
        """Test that change_control_approve raises CvpApiError when tasks have config errors."""
        self.clnt.apiversion = 6.0
        cc_id = 'test-cc-id'
        mock_get_one.return_value = {
            'value': {
                'key': {'id': cc_id},
                'change': {
                    'name': 'Test CC',
                    'time': '2021-12-13T21:05:58.813750128Z',
                    'rootStageId': 'root',
                    'stages': {'values': {
                        'root': {'name': 'root', 'rows': {'values': [{'values': ['stage0']}]}},
                        'stage0': {
                            'name': 'Update Config',
                            'action': {
                                'name': 'task',
                                'timeout': 3000,
                                'args': {'values': {'TaskID': '10'}}
                            }
                        }
                    }}
                }
            },
            'time': '2021-12-13T21:05:58.813750128Z'
        }
        mock_post.return_value = [
            {'sources': {'source': []}},
            {'diff': {'entries': []}},
            {'error': {
                'error_code': 'DEVICEERROR',
                'error_msg': '> typocommand test % Invalid input',
                'line_num': 50,
                'configlet_name': 'test-configlet',
                'config_line_num': 54
            }}
        ]
        with self.assertRaises(CvpApiError) as context:
            self.api.change_control_approve(cc_id)
        self.assertIn('Task 10', str(context.exception))
        self.assertIn('typocommand', str(context.exception))

    @patch.object(CvpApi, 'change_control_get_one')
    @patch.object(CvpApi, 'get_config_diff_for_task')
    def test_change_control_get_task_errors(self, mock_diff, mock_get_one):
        """Test that change_control_get_task_errors returns task config errors."""
        self.clnt.apiversion = 6.0
        cc_id = 'test-cc-id'
        mock_get_one.return_value = {
            'value': {
                'key': {'id': cc_id},
                'change': {
                    'name': 'Test CC',
                    'time': '2021-12-13T21:05:58.813750128Z',
                    'rootStageId': 'root',
                    'stages': {'values': {
                        'root': {'name': 'root', 'rows': {'values': [{'values': ['stage0']}]}},
                        'stage0': {
                            'name': 'Update Config',
                            'action': {
                                'name': 'task',
                                'timeout': 3000,
                                'args': {'values': {'TaskID': '10'}}
                            }
                        }
                    }}
                }
            },
            'time': '2021-12-13T21:05:58.813750128Z'
        }
        task_error = {
            'error_code': 'DEVICEERROR',
            'error_msg': '> typocommand test % Invalid input',
            'line_num': 50,
            'configlet_name': 'test-configlet',
            'config_line_num': 54
        }
        mock_diff.return_value = [
            {'sources': {'source': []}},
            {'diff': {'entries': []}},
            {'error': task_error}
        ]
        result = self.api.change_control_get_task_errors(cc_id)
        self.assertEqual(result, [('10', task_error)])
        mock_get_one.assert_called_once_with(cc_id)
        mock_diff.assert_called_once_with('10')

    @patch.object(CvpApi, 'change_control_get_one')
    def test_change_control_get_task_errors_returns_none_without_cc(self, mock_get_one):
        """Test that change_control_get_task_errors returns None when the CC is missing."""
        self.clnt.apiversion = 6.0
        mock_get_one.return_value = None
        result = self.api.change_control_get_task_errors('missing-cc-id')
        self.assertIsNone(result)
        mock_get_one.assert_called_once_with('missing-cc-id')

    @patch.object(CvpApi, 'change_control_get_one')
    @patch.object(CvpApi, 'get_config_diff_for_task')
    @patch.object(CvpClient, 'post')
    def test_change_control_approve_skips_validation_on_unapprove(self, mock_post, mock_diff, mock_get_one):
        """Test that unapproving a change control skips task error validation."""
        self.clnt.apiversion = 6.0
        cc_id = 'test-cc-id'
        mock_get_one.return_value = {
            'value': {
                'key': {'id': cc_id},
                'change': {
                    'name': 'Test CC',
                    'time': '2021-12-13T21:05:58.813750128Z',
                    'rootStageId': 'root',
                    'stages': {'values': {
                        'root': {'name': 'root', 'rows': {'values': [{'values': ['stage0']}]}},
                        'stage0': {
                            'name': 'Update Config',
                            'action': {
                                'name': 'task',
                                'timeout': 3000,
                                'args': {'values': {'TaskID': '10'}}
                            }
                        }
                    }}
                }
            },
            'time': '2021-12-13T21:05:58.813750128Z'
        }
        unapprove_response = {
            'value': {
                'key': {'id': cc_id},
                'approve': {'value': False, 'notes': ''}
            }
        }
        mock_post.return_value = unapprove_response
        result = self.api.change_control_approve(cc_id, approve=False)
        self.assertEqual(result, unapprove_response)
        mock_diff.assert_not_called()

    @patch.object(CvpClient, 'post')
    def test_get_config_diff_for_task(self, mock_post):
        """Test get_config_diff_for_task returns the compliance check response."""
        expected_response = [
            {'sources': {'source': [{'source_type': 'CONFIG_TYPE_TOMCAT_CONFIGLET', 'key': 'test'}]}},
            {'diff': {'entries': [{'op': 'NOP', 'a_lineno': 1, 'b_lineno': 1}]}},
        ]
        mock_post.return_value = expected_response
        result = self.api.get_config_diff_for_task('10')
        self.assertEqual(result, expected_response)
        mock_post.assert_called_once_with(
            '/api/v3/services/compliancecheck.Compliance/GetConfigDiffForTask',
            data={'task_id': '10'},
            timeout=self.api.request_timeout
        )

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

''' System test for the CvpClient class

    Requirements for CVP Node:
    1) Just need one node for test with the following account:
       username: CvpRacTest
       password: AristaInnovates

       Be sure to create the same account on the switch used for testing.
'''
import logging
import os
import sys
import unittest
from requests.exceptions import Timeout

from cvprac.cvp_client import CvpClient
from cvprac.cvp_client_errors import CvpApiError, CvpLoginError, \
    CvpRequestError, CvpSessionLogOutError

sys.path.append(os.path.join(os.path.dirname(__file__), '../lib'))
from systestlib import DutSystemTest


class TestCvpClient(DutSystemTest):
    ''' Test cases for the CvpClient class.
    '''
    # pylint: disable=too-many-public-methods
    # pylint: disable=invalid-name
    NEW_PASSWORD = 'ChangeMe'

    def setUp(self):
        ''' Instantiate the CvpClient class.
            Log messages to the /tmp/TestCvpClient.log
        '''
        super(TestCvpClient, self).setUp()
        self.clnt = CvpClient(filename='/tmp/TestCvpClient.log')
        self.assertIsNotNone(self.clnt)

    def tearDown(self):
        ''' Destroy the CvpClient class.
        '''
        super(TestCvpClient, self).tearDown()
        self.clnt = None

    def _change_passwd(self, nodes, username, old_password, new_password):
        ''' Helper method to change the user password on CVP.
        '''
        # Create a new connection to handle the request.
        clnt = CvpClient(filename='/tmp/TestCvpClient.log')
        clnt.connect(nodes, username, old_password)
        data = {
            'user': {
                'userId': username,
                'password': new_password,
                'email': 'cvprac@cvprac.com',
                'userStatus': 'Enabled',
            },
            'roles': [
                'network-admin'
            ]
        }
        result = clnt.post("/user/updateUser.do?userId=%s" % username, data)
        self.assertEqual('success', result['data'])

    def test_clnt_init(self):
        ''' Verify CvpClient init
        '''
        clnt = CvpClient()
        self.assertIsNotNone(clnt)
        self.assertEqual(clnt.log.getEffectiveLevel(), logging.INFO)

    def test_clnt_init_syslog(self):
        ''' Verify CvpClient init with syslog argument
        '''
        clnt = CvpClient(syslog=True)
        self.assertIsNotNone(clnt)

    def test_clnt_init_syslog_filename(self):
        ''' Verify CvpClient init with syslog and filename argument
        '''
        logfile = '/tmp/foo'
        clnt = CvpClient(syslog=True, logger='cvpracTmp', filename=logfile)
        self.assertIsNotNone(clnt)
        os.remove(logfile)

    def test_clnt_init_log_level(self):
        ''' Verify CvpClient init with setting log level
        '''
        clnt = CvpClient(log_level='DEBUG')
        self.assertIsNotNone(clnt)
        self.assertEqual(clnt.log.getEffectiveLevel(), logging.DEBUG)

    def test_set_log_level(self):
        ''' Verify changing/setting of log level using client setter method
        '''
        self.clnt.set_log_level('DEBUG')
        self.assertEqual(self.clnt.log.getEffectiveLevel(), logging.DEBUG)
        self.clnt.set_log_level('INFO')
        self.assertEqual(self.clnt.log.getEffectiveLevel(), logging.INFO)

    def test_set_log_level_invalid_value(self):
        ''' Verify an invalid log level value will default the log level to
            INFO
        '''
        self.clnt.set_log_level('blahblah')
        self.assertEqual(self.clnt.log.getEffectiveLevel(), logging.INFO)

    def test_connect_http_good(self):
        ''' Verify http connection succeeds to a single CVP node
            Uses default protocol and port.
        '''
        dut = self.duts[0]
        self.clnt.connect([dut['node']], dut['username'], dut['password'])

    def test_connect_https_good(self):
        ''' Verify https connection succeeds to a single CVP node
            Uses https protocol and port.
        '''
        dut = self.duts[0]
        self.clnt.connect([dut['node']], dut['username'], dut['password'])

    def test_connect_set_request_timeout(self):
        ''' Verify API request timeout is set when provided to
            client connect method.
        '''
        dut = self.duts[0]
        self.clnt.connect([dut['node']], dut['username'], dut['password'],
                          request_timeout=34)
        self.assertEqual(self.clnt.api.request_timeout, 34)

    def test_connect_username_bad(self):
        ''' Verify connect fails with bad username.
        '''
        dut = self.duts[0]
        with self.assertRaises(CvpLoginError):
            self.clnt.connect([dut['node']], 'username', dut['password'])

    def test_connect_password_bad(self):
        ''' Verify connect fails with bad password.
        '''
        dut = self.duts[0]
        with self.assertRaises(CvpLoginError):
            self.clnt.connect([dut['node']], dut['username'], 'password')

    def test_connect_node_bad(self):
        ''' Verify connection fails to a single bogus CVP node
        '''
        with self.assertRaises(CvpLoginError):
            self.clnt.connect(['bogus'], 'username', 'password',
                              connect_timeout=1)

    def test_connect_non_cvp_node(self):
        ''' Verify connection fails to a non-CVP node
        '''
        with self.assertRaises(CvpLoginError):
            self.clnt.connect(['localhost'], 'username', 'password')

    def test_connect_all_nodes_bad(self):
        ''' Verify connection fails to a single bogus CVP node
        '''
        with self.assertRaises(CvpLoginError):
            self.clnt.connect(['bogus1', 'bogus2', 'bogus3'], 'username',
                              'password', connect_timeout=1)

    def test_connect_n1_bad_n2_good(self):
        ''' Verify connect succeeds even if one node is bad
        '''
        dut = self.duts[0]
        self.clnt.connect(['bogus', dut['node']], dut['username'],
                          dut['password'], connect_timeout=5)

    def test_connect_nodes_arg_bad(self):
        ''' Verify non-list nodes argument raises a TypeError
        '''
        with self.assertRaises(TypeError):
            self.clnt.connect('bogus', 'username', 'password')

    def test_connect_port_bad(self):
        ''' Verify non default port for https raises an error if appliance is
            not configured for the port.
        '''
        dut = self.duts[0]
        with self.assertRaises(CvpLoginError):
            self.clnt.connect([dut['node']], dut['username'], dut['password'],
                              port=700)

    def test_connect_from_cb_script(self):
        ''' Verify connection works from configlet builder scripts
        '''
        dut = self.duts[0]
        os.environ["CURRENT_NODE_IP"] = dut['node']
        self.clnt.connect(['localhost'], dut['username'], dut['password'])
        self.clnt.connect(['127.0.0.1'], dut['username'], dut['password'])

    def test_get_not_connected(self):
        ''' Verify get with no connection raises a ValueError
        '''
        with self.assertRaises(ValueError):
            self.clnt.get('/bogus')

    def test_get(self):
        ''' Verify get of CVP info
        '''
        dut = self.duts[0]
        self.clnt.connect([dut['node']], dut['username'], dut['password'])
        result = self.clnt.get('/cvpInfo/getCvpInfo.do')
        self.assertIn('version', result)

    def test_get_recover_session(self):
        ''' Verify client(get) recovers session after logout
        '''
        dut = self.duts[0]
        self.clnt.connect([dut['node']], dut['username'], dut['password'])
        result = self.clnt.post('/login/logout.do', None)
        self.assertIn('data', result)
        self.assertEqual('success', result['data'])
        result = self.clnt.get('/cvpInfo/getCvpInfo.do')
        self.assertIn('version', result)

    def test_get_recover_session_bg(self):
        ''' Verify client(get) recovers session after logout for bad/good node
        '''
        dut = self.duts[0]
        self.clnt.connect(['bogus', dut['node']], dut['username'],
                          dut['password'])
        result = self.clnt.post('/login/logout.do', None)
        self.assertIn('data', result)
        self.assertEqual('success', result['data'])
        result = self.clnt.get('/cvpInfo/getCvpInfo.do')
        self.assertIn('version', result)

    def test_get_cvp_error(self):
        ''' Verify get of bad CVP request returns an error
        '''
        dut = self.duts[0]
        self.clnt.connect([dut['node']], dut['username'], dut['password'])
        if self.clnt.apiversion is None:
            self.clnt.api.get_cvp_info()
        if self.clnt.apiversion == 1.0:
            with self.assertRaises(CvpRequestError):
                self.clnt.get('/aaa/getServerById.do')
        else:
            with self.assertRaises(CvpApiError):
                self.clnt.get('/aaa/getServerById.do')

    def test_get_cvp_url_bad(self):
        ''' Verify get with bad URL returns an error
        '''
        dut = self.duts[0]
        self.clnt.connect([dut['node']], dut['username'], dut['password'])
        with self.assertRaises(CvpApiError):
            self.clnt.get('/aaa/bogus.do')

    def test_get_handle_timeout(self):
        ''' Verify get with bad URL returns an error
        '''
        dut = self.duts[0]
        self.clnt.connect([dut['node']], dut['username'], dut['password'])
        with self.assertRaises(Timeout):
            self.clnt.get('/tasks/getTasks.do', timeout=0.0001)

    def test_get_except_fail_reconnect(self):
        ''' Verify exception raised if session fails and cannot be
            re-established.
        '''
        dut = self.duts[0]
        nodes = ['bogus', dut['node']]
        self.clnt.connect(nodes, dut['username'], dut['password'])
        # Change the password for the CVP user so that a session reconnect
        # to any node will fail
        self._change_passwd(nodes, dut['username'], dut['password'],
                            self.NEW_PASSWORD)

        try:
            # Logout to end the current session and force a reconnect for the
            # next request.
            result = self.clnt.post('/login/logout.do', None)
            self.assertIn('data', result)
            self.assertEqual('success', result['data'])

        except Exception as error:
            # Should not have had an exception.  Restore the CVP password
            # and re-raise the error.
            self._change_passwd(nodes, dut['username'], self.NEW_PASSWORD,
                                dut['password'])
            raise error
        try:
            # Try a get request and expect a CvpSessionLogOutError
            result = self.clnt.get('/cvpInfo/getCvpInfo.do')
        except (CvpSessionLogOutError, CvpApiError) as error:
            pass
        except Exception as error:
            # Unexpected error, restore password and re-raise the error.
            self._change_passwd(nodes, dut['username'], self.NEW_PASSWORD,
                                dut['password'])
            raise error
        # Restore password
        self._change_passwd(nodes, dut['username'], self.NEW_PASSWORD,
                            dut['password'])

    def test_post_not_connected(self):
        ''' Verify post with no connection raises a ValueError
        '''
        with self.assertRaises(ValueError):
            self.clnt.post('/bogus', None)

    def test_post(self):
        ''' Verify post of CVP info
        '''
        dut = self.duts[0]
        self.clnt.connect([dut['node']], dut['username'], dut['password'])
        result = self.clnt.post('/login/logout.do', None)
        self.assertIn('data', result)
        self.assertEqual('success', result['data'])

    def test_post_recover_session(self):
        ''' Verify client(post) recovers session after logout
        '''
        dut = self.duts[0]
        self.clnt.connect([dut['node']], dut['username'], dut['password'])
        result = self.clnt.post('/login/logout.do', None)
        self.assertIn('data', result)
        self.assertEqual('success', result['data'])
        result = self.clnt.post('/login/logout.do', None)
        self.assertEqual('success', result['data'])

    def test_post_recover_session_bg(self):
        ''' Verify client(post) recovers session after logout for bad/good node
        '''
        dut = self.duts[0]
        self.clnt.connect(['bogus', dut['node']], dut['username'],
                          dut['password'])
        result = self.clnt.post('/login/logout.do', None)
        self.assertIn('data', result)
        self.assertEqual('success', result['data'])
        result = self.clnt.post('/login/logout.do', None)
        self.assertEqual('success', result['data'])

    def test_post_cvp_bad_schema(self):
        ''' Verify post with bad schema returns an error
        '''
        dut = self.duts[0]
        self.clnt.connect([dut['node']], dut['username'], dut['password'])
        if self.clnt.apiversion is None:
            self.clnt.api.get_cvp_info()
        if self.clnt.apiversion == 1.0:
            with self.assertRaises(CvpApiError):
                self.clnt.post('/aaa/saveAAADetails.do', None)
        else:
            with self.assertRaises(CvpRequestError):
                self.clnt.post('/aaa/saveAAADetails.do', None)

    def test_post_cvp_url_bad(self):
        ''' Verify post with bad URL returns an error
        '''
        dut = self.duts[0]
        self.clnt.connect([dut['node']], dut['username'], dut['password'])
        with self.assertRaises(CvpApiError):
            self.clnt.post('/aaa/bogus.do', None)

    def test_post_except_fail_reconn(self):
        ''' Verify exception raised if session fails and cannot be
            re-established.
        '''
        dut = self.duts[0]
        nodes = ['bogus', dut['node']]
        self.clnt.connect(nodes, dut['username'], dut['password'])
        # Change the password for the CVP user so that a session reconnect
        # to any node will fail
        self._change_passwd(nodes, dut['username'], dut['password'],
                            self.NEW_PASSWORD)

        try:
            # Logout to end the current session and force a reconnect for the
            # next request.
            result = self.clnt.post('/login/logout.do', None)
            self.assertIn('data', result)
            self.assertEqual('success', result['data'])

        except Exception as error:
            # Should not have had an exception.  Restore the CVP password
            # and re-raise the error.
            self._change_passwd(nodes, dut['username'], self.NEW_PASSWORD,
                                dut['password'])
            raise error
        try:
            # Try a post request and expect a CvpSessionLogOutError
            result = self.clnt.post('/login/logout.do', None)
        except (CvpSessionLogOutError, CvpApiError) as error:
            pass
        except Exception as error:
            # Unexpected error, restore password and re-raise the error.
            self._change_passwd(nodes, dut['username'], self.NEW_PASSWORD,
                                dut['password'])
            raise error
        # Restore password
        self._change_passwd(nodes, dut['username'], self.NEW_PASSWORD,
                            dut['password'])


if __name__ == '__main__':
    unittest.main()

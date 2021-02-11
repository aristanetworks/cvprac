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

''' Unit tests for the CvpClient class
'''
import unittest
from itertools import cycle
from mock import Mock
from requests.exceptions import HTTPError, ReadTimeout
from cvprac.cvp_client import CvpClient
from cvprac.cvp_client_errors import CvpApiError, CvpSessionLogOutError


class TestClient(unittest.TestCase):
    """ Unit test cases for CvpClient
    """
    # pylint: disable=protected-access
    # pylint: disable=invalid-name
    # pylint: disable=too-many-statements

    def setUp(self):
        """ Setup for CvpClient unittests
        """
        self.clnt = CvpClient()
        nodes = ['1.1.1.1']
        self.clnt.nodes = nodes
        self.clnt.node_cnt = len(nodes)
        self.clnt.node_pool = cycle(nodes)

    def test_set_version(self):
        """ Test setting of client.apiversion parameter
        """
        self.assertEqual(self.clnt.apiversion, None)

        test_version = '2018.0'
        self.clnt.set_version(test_version)
        self.assertEqual(self.clnt.apiversion, 1.0)
        self.clnt.apiversion = None

        test_version = '2018.1'
        self.clnt.set_version(test_version)
        self.assertEqual(self.clnt.apiversion, 1.0)
        self.clnt.apiversion = None

        test_version = '2018.1.0'
        self.clnt.set_version(test_version)
        self.assertEqual(self.clnt.apiversion, 1.0)
        self.clnt.apiversion = None

        test_version = '2018.1.3'
        self.clnt.set_version(test_version)
        self.assertEqual(self.clnt.apiversion, 1.0)
        self.clnt.apiversion = None

        test_version = '2018.2'
        self.clnt.set_version(test_version)
        self.assertEqual(self.clnt.apiversion, 2.0)
        self.clnt.apiversion = None

        test_version = '2018.2.0'
        self.clnt.set_version(test_version)
        self.assertEqual(self.clnt.apiversion, 2.0)
        self.clnt.apiversion = None

        test_version = '2018.2.5'
        self.clnt.set_version(test_version)
        self.assertEqual(self.clnt.apiversion, 2.0)
        self.clnt.apiversion = None

        test_version = '2019.0'
        self.clnt.set_version(test_version)
        self.assertEqual(self.clnt.apiversion, 3.0)
        self.clnt.apiversion = None

        test_version = '2019.1'
        self.clnt.set_version(test_version)
        self.assertEqual(self.clnt.apiversion, 3.0)
        self.clnt.apiversion = None

        test_version = '2019.1.0'
        self.clnt.set_version(test_version)
        self.assertEqual(self.clnt.apiversion, 3.0)
        self.clnt.apiversion = None

        test_version = '2019.1.1'
        self.clnt.set_version(test_version)
        self.assertEqual(self.clnt.apiversion, 3.0)
        self.clnt.apiversion = None

        test_version = '2019.1.4'
        self.clnt.set_version(test_version)
        self.assertEqual(self.clnt.apiversion, 3.0)
        self.clnt.apiversion = None

        test_version = '2020.0'
        self.clnt.set_version(test_version)
        self.assertEqual(self.clnt.apiversion, 3.0)
        self.clnt.apiversion = None

        test_version = '2020.0.0'
        self.clnt.set_version(test_version)
        self.assertEqual(self.clnt.apiversion, 3.0)
        self.clnt.apiversion = None

        test_version = '2020.1'
        self.clnt.set_version(test_version)
        self.assertEqual(self.clnt.apiversion, 3.0)
        self.clnt.apiversion = None

        test_version = '2020.1.0'
        self.clnt.set_version(test_version)
        self.assertEqual(self.clnt.apiversion, 3.0)
        self.clnt.apiversion = None

        test_version = '2020.1.0.1'
        self.clnt.set_version(test_version)
        self.assertEqual(self.clnt.apiversion, 3.0)
        self.clnt.apiversion = None

        test_version = '2020.1.1'
        self.clnt.set_version(test_version)
        self.assertEqual(self.clnt.apiversion, 4.0)
        self.clnt.apiversion = None

        test_version = '2020.1.1.1'
        self.clnt.set_version(test_version)
        self.assertEqual(self.clnt.apiversion, 4.0)
        self.clnt.apiversion = None

        test_version = '2020.2'
        self.clnt.set_version(test_version)
        self.assertEqual(self.clnt.apiversion, 4.0)
        self.clnt.apiversion = None

        test_version = '2020.2.0'
        self.clnt.set_version(test_version)
        self.assertEqual(self.clnt.apiversion, 4.0)
        self.clnt.apiversion = None

    def test_create_session_default_https(self):
        """ Test connection to CVP nodes will default to https.
        """
        url = 'https://1.1.1.1:443/web'
        self.clnt._reset_session = Mock()
        self.clnt._reset_session.return_value = None
        self.clnt._create_session(all_nodes=True)
        self.assertEqual(self.clnt.url_prefix, url)

    def test_create_session_https_port(self):
        """ Test https session with user provided port.
        """
        self.clnt.port = 7777
        url = 'https://1.1.1.1:7777/web'
        self.clnt._reset_session = Mock()
        self.clnt._reset_session.return_value = None
        self.clnt._create_session(all_nodes=True)
        self.assertEqual(self.clnt.url_prefix, url)

    def test_create_session_no_http_fallback(self):
        """ Test a failed https connection will not attempt to fallback to http.
        """
        self.clnt.port = None
        url = 'https://1.1.1.1:443/web'
        error = '\n1.1.1.1: Failed to connect via https\n'
        self.clnt._reset_session = Mock()
        self.clnt._reset_session.side_effect = ['Failed to connect via https',
                                                None]
        self.clnt._create_session(all_nodes=True)
        self.assertEqual(self.clnt.url_prefix, url)
        self.assertEqual(self.clnt.error_msg, error)

    def test_make_request_good(self):
        """ Test request does not raise exception and returns json.
        """
        self.clnt.session = Mock()
        self.clnt.session.return_value = True
        request_return_value = Mock()
        self.clnt.session.get.return_value = request_return_value
        self.clnt._create_session = Mock()
        self.clnt.NUM_RETRY_REQUESTS = 2
        self.clnt.connect_timeout = 2
        self.clnt.node_cnt = 2
        self.clnt.url_prefix = 'https://1.1.1.1:7777/web'
        self.clnt._is_good_response = Mock(return_value='Good')
        self.assertIsNone(self.clnt.last_used_node)
        self.clnt._make_request('GET', 'url', 2, {'data': 'data'})
        request_return_value.json.assert_called_once_with()
        self.assertEqual(self.clnt.last_used_node, '1.1.1.1')

    def test_make_request_timeout(self):
        """ Test request timeout exception raised if hit on multiple nodes.
        """
        self.clnt.session = Mock()
        self.clnt.session.return_value = True
        self.clnt.session.get.side_effect = ReadTimeout('Timeout')
        self.clnt._create_session = Mock()
        self.clnt.NUM_RETRY_REQUESTS = 3
        self.clnt.connect_timeout = 2
        self.clnt.node_cnt = 3
        self.clnt.url_prefix = 'https://1.1.1.1:7777/web'
        self.clnt._is_good_response = Mock(return_value='Good')
        self.assertIsNone(self.clnt.last_used_node)
        with self.assertRaises(ReadTimeout):
            self.clnt._make_request('GET', 'url', 2, {'data': 'data'})
        self.assertEqual(self.clnt.last_used_node, '1.1.1.1')

    def test_make_request_http_error(self):
        """ Test request http exception raised if hit on multiple nodes.
        """
        self.clnt.session = Mock()
        self.clnt.session.return_value = True
        self.clnt.session.get.side_effect = HTTPError('HTTPError')
        self.clnt._create_session = Mock()
        self.clnt.NUM_RETRY_REQUESTS = 2
        self.clnt.connect_timeout = 2
        self.clnt.node_cnt = 2
        self.clnt.url_prefix = 'https://1.1.1.1:7777/web'
        self.clnt._is_good_response = Mock(return_value='Good')
        self.assertIsNone(self.clnt.last_used_node)
        with self.assertRaises(HTTPError):
            self.clnt._make_request('GET', 'url', 2, {'data': 'data'})
        self.assertEqual(self.clnt.last_used_node, '1.1.1.1')

    def test_make_request_no_session_error(self):
        """ Test request exception raised if hit on multiple nodes and
            _create_session fails to reset clnt.session.
        """
        self.clnt.session = Mock()
        self.clnt.session.return_value = True
        self.clnt.session.get.side_effect = HTTPError('HTTPError')
        self.clnt.NUM_RETRY_REQUESTS = 2
        self.clnt.connect_timeout = 0.01
        self.clnt.node_cnt = 2
        self.clnt.url_prefix = 'https://1.1.1.1:7777/web'
        self.clnt._is_good_response = Mock(return_value='Good')
        self.assertIsNone(self.clnt.last_used_node)
        with self.assertRaises(HTTPError):
            self.clnt._make_request('GET', 'url', 2, {'data': 'data'})
        self.assertEqual(self.clnt.last_used_node, '1.1.1.1')

    def test_make_request_response_error(self):
        """ Test request exception raised from CVP response data.
        """
        self.clnt.session = Mock()
        self.clnt.session.return_value = True
        self.clnt.session.get.return_value = Mock()
        self.clnt._create_session = Mock()
        self.clnt.NUM_RETRY_REQUESTS = 2
        self.clnt.connect_timeout = 2
        self.clnt.node_cnt = 2
        self.clnt.url_prefix = 'https://1.1.1.1:7777/web'
        self.clnt._is_good_response = Mock()
        self.clnt._is_good_response.side_effect = CvpApiError('CvpApiError')
        self.assertIsNone(self.clnt.last_used_node)
        with self.assertRaises(CvpApiError):
            self.clnt._make_request('GET', 'url', 2, {'data': 'data'})
        self.assertEqual(self.clnt.last_used_node, '1.1.1.1')

    def test_make_request_response_error_unauthorized(self):
        """ Test request exception raised if CVP responds unauthorized user.
        """
        self.clnt.session = Mock()
        self.clnt.session.return_value = True
        self.clnt.session.get.return_value = Mock()
        self.clnt._create_session = Mock()
        self.clnt._reset_session = Mock()
        self.clnt.NUM_RETRY_REQUESTS = 2
        self.clnt.connect_timeout = 2
        self.clnt.node_cnt = 2
        self.clnt.url_prefix = 'https://1.1.1.1:7777/web'
        self.clnt._is_good_response = Mock()
        self.clnt._is_good_response.side_effect = CvpApiError(
            msg='Unauthorized User')
        self.assertIsNone(self.clnt.last_used_node)
        with self.assertRaises(CvpApiError):
            self.clnt._make_request('GET', 'url', 2, {'data': 'data'})
        self.assertEqual(self.clnt.last_used_node, '1.1.1.1')

    def test_make_request_response_error_logout(self):
        """ Test request exception raised if CVP logout error hit.
        """
        self.clnt.session = Mock()
        self.clnt.session.return_value = True
        self.clnt.session.get.return_value = Mock()
        self.clnt._create_session = Mock()
        self.clnt._reset_session = Mock()
        self.clnt.NUM_RETRY_REQUESTS = 2
        self.clnt.connect_timeout = 2
        self.clnt.node_cnt = 2
        self.clnt.url_prefix = 'https://1.1.1.1:7777/web'
        self.clnt._is_good_response = Mock()
        self.clnt._is_good_response.side_effect = CvpSessionLogOutError('bad')
        self.assertIsNone(self.clnt.last_used_node)
        with self.assertRaises(CvpSessionLogOutError):
            self.clnt._make_request('GET', 'url', 2, {'data': 'data'})
        self.assertEqual(self.clnt.last_used_node, '1.1.1.1')

    def test_finditem(self):
        """ Test _finditem
        """
        testobj = {'key1': 'value1',
                   'key2': {'nestkey1': 'nestval1'},
                   'key3': ['nestlist1', 'nestlist2'],
                   'key4': [{'nestobjkey1': 'nestobjval1'},
                            {'nestobjkey2': 'nestobjval2'},
                            ['nestlist1', 'nestlist2'], 'neststring']}
        value = self.clnt._finditem(testobj, 'key5')
        self.assertIsNone(value)

        value = self.clnt._finditem(testobj, 'key1')
        self.assertEqual(value, 'value1')

        value = self.clnt._finditem(testobj, 'nestkey1')
        self.assertEqual(value, 'nestval1')

        value = self.clnt._finditem(testobj, 'key2')
        self.assertEqual(value, {'nestkey1': 'nestval1'})

        value = self.clnt._finditem(testobj, 'key3')
        self.assertEqual(value, ['nestlist1', 'nestlist2'])

        value = self.clnt._finditem(testobj, 'nestobjkey2')
        self.assertEqual(value, 'nestobjval2')


if __name__ == '__main__':
    unittest.main()

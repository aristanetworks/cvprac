#
# Copyright (c) 2016, Arista Networks, Inc.
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
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
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
''' RESTful API Client class for Cloudvision(R) Portal

This module provides a RESTful API client for Cloudvision(R) Portal (CVP)
which can be used for building applications that work with Arista CVP.

When the class is instantiated the logging is configured.  Either syslog,
file logging, both, or none can be enabled.  If neither syslog nor filename is
specified then no logging will be performed.

This class supports creating a connection to a CVP node and then issuing
subsequent GET and POST requests to CVP.  A GET or POST request will be
automatically retried on the same node if the request receives a
requests.exceptions.Timeout or ReadTimeout error.  A GET or POST request will
be automatically retried on the same node if the request receives a
CvpSessionLogOutError.  For this case a login will be performed before the
request is retried.  For either case, the maximum number of times a request
will be retried on the same node is specified by the class attribute
NUM_RETRY_REQUESTS.

If more than one CVP node is specified when creating a connection, and a GET
or POST request that receives a requests.exceptions.ConnectionError,
requests.exceptions.HTTPError, or a requests.exceptions.TooManyRedirects will
be retried on the next CVP node in the list.  If a GET or POST request that
receives a requests.exceptions.Timeout or CvpSessionLogOutError and the retries
on the same node exceed NUM_RETRY_REQUESTS, then the request will be retried
on the next node on the list.

If any of the errors persists across all nodes then the GET or POST request
will fail and the last error that occurred will be raised.

The class provides connect, get, and post methods that allow the user to make
direct RESTful API calls to CVP.

Example:

    >>> from cvprac.cvp_client import CvpClient
    >>> clnt = CvpClient()
    >>> clnt.connect(['cvp1', 'cvp2', 'cvp3'], 'cvp_user', 'cvp_word')
    >>> result = clnt.get('/cvpInfo/getCvpInfo.do')
    >>> print result
    {u'version': u'2016.1.0'}
    >>>

The class provides a wrapper function around the CVP RESTful API operations.
Each API method takes the RESTful API parameters as method parameters to the
operation method.  The API class was added to the client class because the
API functions are required when using the CVP RESTful API and placing them
in this library avoids duplicating the calls in every application that uses
this class.

Example:

    >>> from cvprac.cvp_client import CvpClient
    >>> clnt = CvpClient()
    >>> clnt.connect(['cvp1', 'cvp2', 'cvp3'], 'cvp_user', 'cvp_word')
    >>> result = clnt.api.get_cvp_info()
    >>> print result
    {u'version': u'2016.1.0'}
    >>>
'''

import json
import logging
from logging.handlers import SysLogHandler
from itertools import cycle

import requests
from requests.exceptions import ConnectionError, HTTPError, Timeout, \
    ReadTimeout, TooManyRedirects

from cvprac.cvp_api import CvpApi
from cvprac.cvp_client_errors import CvpApiError, CvpLoginError, \
    CvpRequestError, CvpSessionLogOutError

class CvpClient(object):
    ''' Use this class to create a persistent connection to CVP.
    '''
    # pylint: disable=too-many-instance-attributes
    # Maximum number of times to retry a get or post to the same
    # CVP node.
    NUM_RETRY_REQUESTS = 3

    def __init__(self, logger='cvprac', syslog=False, filename=None):
        ''' Initialize the client and configure logging.  Either syslog, file
            logging, both, or none can be enabled.  If neither syslog
            nor filename is specified then no logging will be performed.

            Args:
                logger (str): The name assigned to the logger.
                syslog (bool): If True enable logging to syslog. Default is
                    False.
                filename (str): Log to the file specified by filename. Default
                    is None.
        '''
        self.authdata = None
        self.connect_timeout = None
        self.cookies = None
        self.error_msg = ''
        self.node_cnt = None
        self.node_pool = None
        self.nodes = None
        self.port = None
        self.protocol = None
        self.session = None
        self.url_prefix = None

        # Save proper headers
        self.headers = {'Accept' : 'application/json',
                        'Content-Type' : 'application/json'}

        self.log = logging.getLogger(logger)
        self.log.setLevel(logging.INFO)
        if syslog:
            # Enables sending logging messages to the local syslog server.
            self.log.addHandler(SysLogHandler())
        if filename:
            # Enables sending logging messages to a file.
            self.log.addHandler(logging.FileHandler(filename))
        if syslog is False and filename is None:
            # Not logging so use the null handler
            self.log.addHandler(logging.NullHandler())

        # Instantiate the CvpApi class
        self.api = CvpApi(self)

    def connect(self, nodes, username, password, connect_timeout=10,
                protocol='http', port=None):
        ''' Login to CVP and get a session ID and cookie.  Currently
            certificates are not verified if the https protocol is specified. A
            warning may be printed out from the requests module for this case.

            Args:
                nodes (list): A list of hostname/IP addresses for CVP nodes
                username (str): The CVP username
                password (str): The CVP password
                connect_timeout (int): The number of seconds to wait for a
                    connection.
                protocol (str): The type of protocol to use for the connection.
                    The default value is 'http'.
                port (int): The TCP port of the endpoint for the connection.
                    If this keyword is not specified, the default value is
                    automatically determined by the transport type.
                    (http=80, https=443)

            Raises:
                CvpLoginError: A CvpLoginError is raised if a connection
                    could not be established to any of the nodes.
                TypeError: A TypeError is raised if the nodes argument is not
                    a list.
                ValueError: A ValueError is raised if a port is not specified
                    and the protocol is not http or https.
        '''
        # pylint: disable=too-many-arguments
        if not isinstance(nodes, list):
            raise TypeError('nodes argument must be a list')

        self.nodes = nodes
        self.node_cnt = len(nodes)
        self.node_pool = cycle(nodes)
        self.authdata = {'userId': username, 'password': password}
        self.connect_timeout = connect_timeout
        self.protocol = protocol

        if port is None:
            if protocol == 'http':
                port = 80
            elif protocol == 'https':
                port = 443
            else:
                raise ValueError('No default port for protocol: %s' % protocol)
        self.port = port

        self._create_session(all_nodes=True)
        # Verify that we can connect to at least one node
        if not self.session:
            raise CvpLoginError(self.error_msg)

    def _create_session(self, all_nodes=False):
        ''' Login to CVP and get a session ID and user information.
            If the all_nodes parameter is True then try creating a session
            with each CVP node.  If False, then try creating a session with
            each node except the one currently connected to.
        '''
        num_nodes = self.node_cnt
        if not all_nodes and num_nodes > 1:
            num_nodes -= 1

        self.error_msg = '\n'
        for _ in range(0, num_nodes):
            host = next(self.node_pool)
            self.url_prefix = ('%s://%s:%d/web' %
                               (self.protocol, host, self.port))
            error = self._reset_session()
            if error is None:
                break
            self.error_msg += '%s: %s\n' % (host, error)

    def _reset_session(self):
        ''' Get a new request session and try logging into the current
            CVP node. If the login succeeded None will be returned and
            self.session will be valid. If the login failed then an
            exception error will be returned and self.session will
            be set to None.
        '''
        self.session = requests.Session()
        error = None
        try:
            self._login()
        except (ConnectionError, CvpApiError, CvpRequestError,
                CvpSessionLogOutError, HTTPError, ReadTimeout, Timeout,
                TooManyRedirects) as error:
            self.log.error(error)
            # Any error that occurs during login is a good reason not to use
            # this CVP node.
            self.session = None
        return error

    def _is_good_response(self, response, prefix):
        ''' Check for errors in a response from a GET or POST request.
            The response argument contains a response object from a GET or POST
            request.  The prefix argument contains the prefix to put into the
            error message.

            Raises:
                CvpApiError: A CvpApiError is raised if there was a JSON error.
                CvpRequestError: A CvpRequestError is raised if the request
                    is not properly constructed.
                CvpSessionLogOutError: A CvpSessionLogOutError is raised if
                    response from server indicates session was logged out.
        '''
        if not response.ok:
            msg = '%s: Request Error: %s' % (prefix, response.reason)
            self.log.error(msg)
            raise CvpRequestError(msg)

        if 'LOG OUT MESSAGE' in response.text:
            msg = ('%s: Request Error: session logged out' % prefix)
            raise CvpSessionLogOutError(msg)

        if 'errorCode' in response.text:
            joutput = response.json()
            if 'errorMessage' in joutput:
                err_msg = joutput['errorMessage']
            else:
                if 'errors' in joutput:
                    error_list = joutput['errors']
                else:
                    error_list = [joutput['errorCode']]
                # Build the error message from all the errors.
                err_msg = error_list[0]
                for idx in range(1, len(error_list)):
                    err_msg = '%s\n%s' % (err_msg, error_list[idx])

            msg = ('%s: Request Error: %s' % (prefix, err_msg))
            self.log.error(msg)
            raise CvpApiError(msg)

    def _login(self):
        ''' Make a POST request to CVP login authentication.
            An error can be raised from the post method call or the
            _is_good_response method call.  Any errors raised would be a good
            reason not to use this host.

            Raises:
                ConnectionError: A ConnectionError is raised if there was a
                    network problem (e.g. DNS failure, refused connection, etc)
                CvpApiError: A CvpApiError is raised if there was a JSON error.
                CvpRequestError: A CvpRequestError is raised if the request
                    is not properly constructed.
                CvpSessionLogOutError: A CvpSessionLogOutError is raised if
                    reponse from server indicates session was logged out.
                HTTPError: A HTTPError is raised if there was an invalid HTTP
                    response.
                ReadTimeout: A ReadTimeout is raised if there was a request
                    timeout when reading from the connection.
                Timeout: A Timeout is raised if there was a request timeout.
                TooManyRedirects: A TooManyRedirects is raised if the request
                    exceeds the configured number of maximum redirections
                ValueError: A ValueError is raised when there is no valid
                    CVP session.  This occurs because the previous get or post
                    request failed and no session could be established to a
                    CVP node.  Destroy the class and re-instantiate.
        '''
        # Remove any previous session id from the headers
        self.headers.pop('APP_SESSION_ID', None)
        url = self.url_prefix + '/login/authenticate.do'
        response = self.session.post(url,
                                     data=json.dumps(self.authdata),
                                     headers=self.headers,
                                     timeout=self.connect_timeout,
                                     verify=False)
        self._is_good_response(response, 'Authenticate: %s' % url)

        self.cookies = response.cookies
        self.headers['APP_SESSION_ID'] = response.json()['sessionId']

    def _make_request(self, req_type, url, timeout, data=None):
        ''' Make a GET or POST request to CVP.  If the request call raises a
            timeout or CvpSessionLogOutError then the request will be retried
            on the same CVP node.  Otherwise the request will be tried on the
            next CVP node.

            Args:
                req_type (str): Either 'GET' or 'POST'.
                url (str): Portion of request URL that comes after the host.
                timeout (int): Number of seconds the client will wait between
                    bytes sent from the server.
                data (dict): Dict of key/value pairs to pass as parameters into
                    the request. Default is None.

            Returns:
                The JSON response.

            Raises:
                ConnectionError: A ConnectionError is raised if there was a
                    network problem (e.g. DNS failure, refused connection, etc)
                CvpApiError: A CvpApiError is raised if there was a JSON error.
                CvpRequestError: A CvpRequestError is raised if the request
                    is not properly constructed.
                CvpSessionLogOutError: A CvpSessionLogOutError is raised if
                    reponse from server indicates session was logged out.
                HTTPError: A HTTPError is raised if there was an invalid HTTP
                    response.
                ReadTimeout: A ReadTimeout is raised if there was a request
                    timeout when reading from the connection.
                Timeout: A Timeout is raised if there was a request timeout.
                TooManyRedirects: A TooManyRedirects is raised if the request
                    exceeds the configured number of maximum redirections
                ValueError: A ValueError is raised when there is no valid
                    CVP session.  This occurs because the previous get or post
                    request failed and no session could be established to a
                    CVP node.  Destroy the class and re-instantiate.
        '''
        # pylint: disable=too-many-branches

        if not self.session:
            raise ValueError('No valid session to CVP node')

        # For get or post requests apply both the connect and read timeout.
        timeout = (self.connect_timeout, timeout)

        # Retry the request for the number of nodes.
        error = None
        retry_cnt = self.NUM_RETRY_REQUESTS
        node_cnt = self.node_cnt
        while node_cnt > 0:
            if error:
                # Decrement count as another node will be tried, if there
                # are no more nodes then raise the error.
                node_cnt -= 1
                if node_cnt == 0:
                    # pylint: disable=raising-bad-type
                    # error will not be None here
                    raise error

                # Not the first time through the loop. Retrying request so
                # create a session to another CVP node.
                self._create_session()

                # Verify that we can connect to at least one node
                # otherwise raise the last error
                if not self.session:
                    # pylint: disable=raising-bad-type
                    # error will not be None here
                    raise error

                retry_cnt = self.NUM_RETRY_REQUESTS
                error = None

            full_url = self.url_prefix + url
            try:
                if req_type == 'GET':
                    response = self.session.get(full_url,
                                                cookies=self.cookies,
                                                headers=self.headers,
                                                timeout=timeout,
                                                verify=False)
                else:
                    response = self.session.post(full_url,
                                                 cookies=self.cookies,
                                                 data=json.dumps(data),
                                                 headers=self.headers,
                                                 timeout=timeout,
                                                 verify=False)

            except (ConnectionError, HTTPError, TooManyRedirects) as error:
                # Any of these errors is a good reason to try another CVP node
                self.log.error(error)
                continue

            except (ReadTimeout, Timeout) as error:
                self.log.debug(error)

                # Retry the request if there was a timeout. Decrement the
                # retry count and if greater than zero retry the request
                # to the same node.
                retry_cnt -= 1
                if retry_cnt > 0:
                    error = None
                continue

            try:
                self._is_good_response(response, '%s: %s ' %
                                       (req_type, full_url))
            except CvpSessionLogOutError as error:
                self.log.debug(error)

                # Retry the request to the same node if there was a CVP session
                # logout. Reset the session which will login. If a valid
                # session comes back then clear the error so this request will
                # be retried on the same node.
                retry_cnt -= 1
                if retry_cnt > 0:
                    self._reset_session()
                    if self.session:
                        error = None
                continue
            break

        return response.json()

    def get(self, url, timeout=30):
        ''' Make a GET request to CVP.  If the request call raises an error
            or if the JSON response contains a CVP session related error then
            retry the request on another CVP node.

            Args:
                url (str): Portion of request URL that comes after the host.
                timeout (int): Number of seconds the client will wait between
                    bytes sent from the server.  Default value is 30 seconds.

            Returns:
                The JSON response.

            Raises:
                ConnectionError: A ConnectionError is raised if there was a
                    network problem (e.g. DNS failure, refused connection, etc)
                CvpApiError: A CvpApiError is raised if there was a JSON error.
                CvpRequestError: A CvpRequestError is raised if the request
                    is not properly constructed.
                CvpSessionLogOutError: A CvpSessionLogOutError is raised if
                    reponse from server indicates session was logged out.
                HTTPError: A HTTPError is raised if there was an invalid HTTP
                    response.
                ReadTimeout: A ReadTimeout is raised if there was a request
                    timeout when reading from the connection.
                Timeout: A Timeout is raised if there was a request timeout.
                TooManyRedirects: A TooManyRedirects is raised if the request
                    exceeds the configured number of maximum redirections
                ValueError: A ValueError is raised when there is no valid
                    CVP session.  This occurs because the previous get or post
                    request failed and no session could be established to a
                    CVP node.  Destroy the class and re-instantiate.
        '''
        return self._make_request('GET', url, timeout)

    def post(self, url, data=None, timeout=30):
        ''' Make a POST request to CVP.  If the request call raises an error
            or if the JSON response contains a CVP session related error then
            retry the request on another CVP node.

            Args:
                url (str): Portion of request URL that comes after the host.
                data (dict): Dict of key/value pairs to pass as parameters into
                    the request. Default is None.
                timeout (int): Number of seconds the client will wait between
                    bytes sent from the server.  Default value is 30 seconds.

            Returns:
                The JSON response.

            Raises:
                ConnectionError: A ConnectionError is raised if there was a
                    network problem (e.g. DNS failure, refused connection, etc)
                CvpApiError: A CvpApiError is raised if there was a JSON error.
                CvpRequestError: A CvpRequestError is raised if the request
                    is not properly constructed.
                CvpSessionLogOutError: A CvpSessionLogOutError is raised if
                    reponse from server indicates session was logged out.
                HTTPError: A HTTPError is raised if there was an invalid HTTP
                    response.
                ReadTimeout: A ReadTimeout is raised if there was a request
                    timeout when reading from the connection.
                Timeout: A Timeout is raised if there was a request timeout.
                TooManyRedirects: A TooManyRedirects is raised if the request
                    exceeds the configured number of maximum redirections
                ValueError: A ValueError is raised when there is no valid
                    CVP session.  This occurs because the previous get or post
                    request failed and no session could be established to a
                    CVP node.  Destroy the class and re-instantiate.
        '''
        return self._make_request('POST', url, timeout, data=data)

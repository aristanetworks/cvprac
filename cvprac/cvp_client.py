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

# pylint: disable=too-many-branches,too-many-statements,too-many-locals,too-many-lines

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

import os
import re
import json
import logging
from logging.handlers import SysLogHandler
from itertools import cycle
from packaging.version import parse

import requests
from requests.exceptions import ( # pylint: disable=redefined-builtin
    ConnectionError,
    HTTPError,
    Timeout,
    ReadTimeout,
    TooManyRedirects,
    JSONDecodeError
)

from cvprac.cvp_api import CvpApi
from cvprac.cvp_client_errors import CvpApiError, CvpLoginError, \
    CvpRequestError, CvpSessionLogOutError


class CvpClient():
    ''' Use this class to create a persistent connection to CVP.
    '''
    # pylint: disable=too-many-instance-attributes
    # Maximum number of times to retry a get or post to the same
    # CVP node.
    NUM_RETRY_REQUESTS = 3
    LATEST_API_VERSION = 17.0

    def __init__(self, logger='cvprac', syslog=False, filename=None,
                 log_level='INFO'):
        ''' Initialize the client and configure logging.  Either syslog, file
            logging, both, or none can be enabled.  If neither syslog
            nor filename is specified then no logging will be performed.

            Args:
                logger (str): The name assigned to the logger.
                syslog (bool): If True enable logging to syslog. Default is
                    False.
                filename (str): Log to the file specified by filename. Default
                    is None.
                log_level (str): Log level to use for logger. Default is INFO.
        '''
        self.apiversion = None
        self.authdata = None
        self.cert = False
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
        self.url_prefix_short = None
        self.is_cvaas = False
        self.tenant = None
        self.cvaas_token = None
        self.api_token = None
        self.version = None
        self._last_used_node = None
        self.proxies = None

        # Save proper headers
        self.headers = {'Accept': 'application/json',
                        'Content-Type': 'application/json'}

        self.log = logging.getLogger(logger)
        self.set_log_level(log_level)
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

    @property
    def last_used_node(self):
        ''' Returns the node that the last request was sent to regardless of
            whether the request was successful or not.

            Returns:
                String identifying the node that the last request was sent to.
        '''
        return self._last_used_node

    def set_log_level(self, log_level='INFO'):
        ''' Set log level for logger. Defaults to INFO if no level passed in or
            if an invalid level is passed in.

            Args:
                log_level (str): Log level to use for logger. Default is INFO.
        '''
        log_level = log_level.upper()
        if log_level not in ['NOTSET', 'DEBUG', 'INFO',
                             'WARNING', 'ERROR', 'CRITICAL']:
            log_level = 'INFO'
        self.log.setLevel(getattr(logging, log_level))

    def set_version(self, version):
        ''' Set the CVP API version to be used when making api calls.

            For CVP versions 2018.1.X and prior, use api version 1.0
            For CVP versions 2018.2.X, use api version 2.0
            For CVP versions 2019.0.0 through 2020.1.0, use api version 3.0
            For CVP versions 2020.1.1 through 2020.2.3, use api version 4.0
            For CVP versions 2020.2.4 through 2021.1.x, use api version 5.0
            For CVP versions 2021.2.x, use api version 6.0
            For CVP versions 2021.3.x, use api version 7.0
            For CVP versions 2022.x.x, use api version 8.0
            For CVP versions 2023.1.x, use api version 9.0
            For CVP versions 2023.2.x, use api version 10.0
            For CVP versions 2023.3.x, use api version 11.0
            For CVP versions 2024.1.x, use api version 12.0
            For CVP versions 2024.2.x, use api version 13.0
            For CVP versions 2024.3.x, use api version 14.0
            For CVP versions 2025.1.x, use api version 15.0
            For CVP versions 2025.2.x, use api version 16.0
            For CVP versions 2025.3.x and beyond, use api version 17.0


            Args:
                version (str): The CVP version in use.
        '''
        self.version = version
        self.log.info('Version %s', version)
        # Set apiversion to latest available API version for CVaaS
        # Set apiversion to 17.0 for 2025.3.x
        # Set apiversion to 16.0 for 2025.2.x
        # Set apiversion to 15.0 for 2025.1.x
        # Set apiversion to 14.0 for 2024.3.x
        # Set apiversion to 13.0 for 2024.2.x
        # Set apiversion to 12.0 for 2024.1.x
        # Set apiversion to 11.0 for 2023.3.x
        # Set apiversion to 10.0 for 2023.2.x
        # Set apiversion to 9.0 for 2023.1.x
        # Set apiversion to 8.0 for 2022.1.x - 2022.3.x
        # Set apiversion to 7.0 for 2021.3.x
        # Set apiversion to 6.0 for 2021.2.x
        # Set apiversion to 5.0 for 2020.2.4 through 2021.1.x
        # Set apiversion to 4.0 for 2020.1.1 through 2020.2.3
        # Set apiversion to 3.0 for 2019.0.0 through 2020.1.0
        # Set apiversion to 2.0 for 2018.2.X
        # Set apiversion to 1.0 for 2018.1.X and prior
        if self.is_cvaas:
            self.log.info('Setting API version to %d for CVaaS',
                          self.LATEST_API_VERSION)
            self.apiversion = self.LATEST_API_VERSION
        else:
            version_components = version.split(".")
            if len(version_components) < 3:
                version_components.append("0")
                self.log.info('Version found with less than 3 components.'
                              ' Appending 0. Updated Version String - %s',
                              ".".join(version_components))
            full_version = ".".join(version_components)
            if parse(full_version) >= parse('2025.3.0'):
                self.log.info('Setting API version to v17')
                self.apiversion = 17.0
            elif parse(full_version) >= parse('2025.2.0'):
                self.log.info('Setting API version to v16')
                self.apiversion = 16.0
            elif parse(full_version) >= parse('2025.1.0'):
                self.log.info('Setting API version to v15')
                self.apiversion = 15.0
            elif parse(full_version) >= parse('2024.3.0'):
                self.log.info('Setting API version to v14')
                self.apiversion = 14.0
            elif parse(full_version) >= parse('2024.2.0'):
                self.log.info('Setting API version to v13')
                self.apiversion = 13.0
            elif parse(full_version) >= parse('2024.1.0'):
                self.log.info('Setting API version to v12')
                self.apiversion = 12.0
            elif parse(full_version) >= parse('2023.3.0'):
                self.log.info('Setting API version to v11')
                self.apiversion = 11.0
            elif parse(full_version) >= parse('2023.2.0'):
                self.log.info('Setting API version to v10')
                self.apiversion = 10.0
            elif parse(full_version) >= parse('2023.1.0'):
                self.log.info('Setting API version to v9')
                self.apiversion = 9.0
            elif parse(full_version) >= parse('2022.1.0'):
                self.log.info('Setting API version to v8')
                self.apiversion = 8.0
            elif parse(full_version) >= parse('2021.3.0'):
                self.log.info('Setting API version to v7')
                self.apiversion = 7.0
            elif parse(full_version) >= parse('2021.2.0'):
                self.log.info('Setting API version to v6')
                self.apiversion = 6.0
            elif parse(full_version) >= parse('2020.2.4'):
                self.log.info('Setting API version to v5')
                self.apiversion = 5.0
            elif parse(full_version) >= parse('2020.1.1'):
                self.log.info('Setting API version to v4')
                self.apiversion = 4.0
            elif parse(full_version) >= parse('2019.0.0'):
                self.log.info('Setting API version to v3')
                self.apiversion = 3.0
            elif parse(full_version) >= parse('2018.2.0'):
                self.log.info('Setting API version to v2')
                self.apiversion = 2.0
            else:
                self.log.info('Setting API version to v1')
                self.apiversion = 1.0

    def connect(self, nodes, username, password, connect_timeout=10,
                request_timeout=30, protocol='https', port=None, cert=False,
                is_cvaas=False, tenant=None, api_token=None, cvaas_token=None,
                proxies=None):
        ''' Login to CVP and get a session ID and cookie.  Currently
            certificates are not verified if the https protocol is specified. A
            warning may be printed out from the requests module for this case.

            Args:
                nodes (list): A list of hostname/IP addresses for CVP nodes
                username (str): The CVP username
                password (str): The CVP password
                connect_timeout (int): The number of seconds to wait for a
                    connection.
                request_timeout (int): The default number of seconds to allow
                    api requests to complete before timing out.
                protocol (str): The protocol to use to connect to CVP.
                    THIS PARAMETER IS NOT USED AND WILL BE DEPRECATED.
                    ONLY INCLUDED TO NOT BREAK EXISTING CODE THAT HAS PROTOCOL
                    SPECIFIED IN CONNECTION.
                port (int): The TCP port of the endpoint for the connection.
                    If this keyword is not specified, the default value is
                    automatically determined by the transport type.
                    (http=80, https=443)
                cert (str or boolean): Path to a cert file used for a https
                    connection or boolean with default False. If a cert is
                    provided then the connection will not attempt to fallback
                    to http. The False default sets the request to not verify
                    the servers TLS certificate.
                is_cvaas (boolean): Flag for enabling connection to CVaaS.
                tenant: (string): Tenant/Org within CVaaS to connect to.
                    Required if is_cvaas is enabled.
                cvaas_token (string): API Token to use in place of UN/PW login
                    for CVaaS.
                api_token (string): API Token to use in place of UN/PW login
                    for CVP 2020.3.0 and beyond.
                proxies (dict): A dictionary of proxy protocol to URL. Example:

                    {'http': 'hostname.domain.com:8080',
                     'https': 'hostname.domain.com:8080'}

                     Proxies can also be set via environment variables.
                     Please reference the below link for details of precedence.
                     https://requests.readthedocs.io/en/latest/user/advanced/#proxies

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

        for idx, _ in enumerate(nodes):
            if (os.environ.get('CURRENT_NODE_IP') and
                    nodes[idx] in ['127.0.0.1', 'localhost']):
                # We set this env in script-executor container.
                # Mask localhost or 127.0.0.1 with node IP if this
                # is called from configlet builder scripts.
                nodes[idx] = os.environ.get('CURRENT_NODE_IP')

        self.cert = cert
        self.nodes = nodes
        self.node_cnt = len(nodes)
        self.node_pool = cycle(nodes)
        self.authdata = {'userId': username, 'password': password}
        self.connect_timeout = connect_timeout
        self.api.request_timeout = request_timeout
        # protocol is deprecated and not used.
        self.protocol = protocol
        self.port = port
        self.is_cvaas = is_cvaas
        self.tenant = tenant
        if cvaas_token is not None:
            self.log.warning('The cvaas_token parameter will be deprecated'
                             ' soon. Please start using the api_token'
                             ' parameter instead. It provides the same'
                             ' functionality that was previously provided'
                             ' by cvaas_token. The api_token parameter is'
                             ' a more general API token parameter because'
                             ' using the CVP REST API via token is also'
                             ' available for on premises CVP as of'
                             ' CVP version 2020.3.0')
            self.cvaas_token = cvaas_token
            self.api_token = cvaas_token
        if api_token is not None:
            self.log.warning('Using the new api_token parameter.'
                             ' This will override usage of the cvaas_token'
                             ' parameter if both are provided. This is because'
                             ' api_token and cvaas_token parameters are for'
                             ' the same use case and api_token is more'
                             ' generic')
            self.api_token = api_token
            self.cvaas_token = api_token
        self.proxies = proxies
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
            self.url_prefix = f"https://{host}:{self.port or 443}/web"
            self.url_prefix_short = f"https://{host}:{self.port or 443}"
            error = self._reset_session()
            if error is None:
                break
            self.error_msg += f"{host}: {error}\n"

    def _reset_session(self):
        ''' Get a new request session and try logging into the current
            CVP node. If the login succeeded None will be returned and
            self.session will be valid. If the login failed then an
            exception error will be returned and self.session will
            be set to None.
        '''
        self.session = requests.Session()
        if self.proxies:
            self.session.proxies.update(self.proxies)
        return_error = None
        try:
            self._login()
        except (ConnectionError, CvpApiError, CvpRequestError,
                CvpSessionLogOutError, HTTPError, ReadTimeout, Timeout,
                TooManyRedirects) as error:
            self.log.error(error)
            # Use outer scope var for return to handle
            # Python 3 UnboundLocalError
            return_error = error
            # Any error that occurs during login is a good reason not to use
            # this CVP node.
            self.session = None
        return return_error

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
            if 'Unauthorized' in response.reason:
                # Check for 'Unauthorized' User error because this is how
                # CVP responds to a logged out users requests in 2018.x.
                msg = f"{prefix}: Request Error: {response.reason}"
                self.log.error(msg)
                raise CvpApiError(msg)
            if 'User is unauthorized' in response.text:
                # Check for 'User is unauthorized' response text because this
                # is how CVP responds to a logged out users requests in 2019.x.
                msg = f"{prefix}: Request Error: User is unauthorized"
                self.log.error(msg)
                raise CvpApiError(msg)
            msg = f"{prefix}: Request Error: {response.reason} - {response.text}"
            raise CvpRequestError(msg)

        if 'LOG OUT MESSAGE' in response.text:
            msg = f"{prefix}: Request Error: session logged out"
            raise CvpSessionLogOutError(msg)

        joutput = json_decoder(response.text)
        err_code_val = self._finditem(joutput, 'errorCode')
        if err_code_val:
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
                    err_msg = f"{err_msg}\n{error_list[idx]}"

            msg = f"{prefix}: Request Error: {err_msg}"
            self.log.error(msg)
            raise CvpApiError(msg)

    def _check_response_status(self, response, prefix):
        ''' Check for status OK in a response from a GET or POST request.
            The response argument contains a response object from a GET or POST
            request.  The prefix argument contains the prefix to put into the
            error message.

            Raises:
                CvpRequestError: A CvpRequestError is raised if request
                response status is not OK.
        '''
        if not response.ok:
            msg = f"{prefix}: Request Error: {response.reason} - {response.text}"
            self.log.error(msg)
            raise CvpRequestError(msg)

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
                    response from server indicates session was logged out.
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
        if self.api_token is not None:
            return self._set_headers_api_token()
        if self.is_cvaas:
            raise CvpLoginError('CVaaS only supports API token authentication.'
                                ' Please create an API token and provide it'
                                ' via the api_token parameter in combination'
                                ' with the is_cvaas parameter')
        return self._login_on_prem()

    def _login_on_prem(self):
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
                    response from server indicates session was logged out.
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
        url = self.url_prefix + '/login/authenticate.do'
        response = self.session.post(url,
                                     data=json.dumps(self.authdata),
                                     headers=self.headers,
                                     timeout=self.connect_timeout,
                                     verify=self.cert)
        self._is_good_response(response, f"Authenticate: {url}")

        self.cookies = response.cookies
        self.headers['APP_SESSION_ID'] = response.json()['sessionId']

    def _set_headers_api_token(self):
        ''' Sets headers with API token instead of making a call to login API.
        '''
        # If using an API token there is no need to run a Login API.
        # Simply add the token into the headers or cookies
        self.headers['Authorization'] = f"Bearer {self.api_token}"
        # Alternative to adding token to headers it can be added to
        # cookies as shown below.
        # self.cookies = {'access_token': self.api_token}
        url = self.url_prefix_short + '/api/v1/rest/'
        response = self.session.get(
            url,
            cookies=self.cookies,
            headers=self.headers,
            timeout=self.connect_timeout,
            verify=self.cert
        )
        # Verify that the generic request was successful
        self._is_good_response(response, f"Authenticate: {url}")

    def logout(self):
        '''

        :return:
        '''
        response = self.post('/login/logout.do')
        if response['data'] == 'success':
            self.log.info('User logged out.')
            self.session = None
        else:
            err = f"Error trying to logout {response}"
            self.log.error(err)

    def _make_request(self, req_type, url, timeout, data=None,
                      files=None):
        ''' Make a GET, POST or DELETE request to CVP.  If the request call raises a
            timeout or CvpSessionLogOutError then the request will be retried
            on the same CVP node.  Otherwise the request will be tried on the
            next CVP node.

            Args:
                req_type (str): Either 'GET', 'POST' or 'DELETE'.
                url (str): Portion of request URL that comes after the host.
                timeout (int): Number of seconds the client will wait between
                    bytes sent from the server.
                data (dict): Dict of key/value pairs to pass as parameters into
                    the request. Default is None.
                files (dict): Dict of file name to files for upload. Currently
                    only used for adding images to CVP. Default is None.

            Returns:
                The JSON response.

            Raises:
                ConnectionError: A ConnectionError is raised if there was a
                    network problem (e.g. DNS failure, refused connection, etc)
                CvpApiError: A CvpApiError is raised if there was a JSON error.
                CvpRequestError: A CvpRequestError is raised if the request
                    is not properly constructed.
                CvpSessionLogOutError: A CvpSessionLogOutError is raised if
                    response from server indicates session was logged out.
                HTTPError: A HTTPError is raised if there was an invalid HTTP
                    response.
                ReadTimeout: A ReadTimeout is raised if there was a request
                    timeout when reading from the connection.
                Timeout: A Timeout is raised if there was a request timeout.
                TooManyRedirects: A TooManyRedirects is raised if the request
                    exceeds the configured number of maximum re-directions
                ValueError: A ValueError is raised when there is no valid
                    CVP session.  This occurs because the previous get, post
                    or delete request failed and no session could be
                    established to a CVP node.  Destroy the class and
                    re-instantiate.
                JSONDecodeError: A JSONDecodeError is raised when the response
                    content contains invalid JSON. Potentially in the case of
                    Resource APIs that will return Stream JSON format with
                    multiple object or in the case where the response contains
                    incomplete JSON.
        '''
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-arguments
        # pylint: disable=raising-bad-type
        if not self.session:
            raise ValueError('No valid session to CVP node')
        # Keep note of which node is handling this request.
        self._last_used_node = re.match('http[s]?://(.*):',
                                        self.url_prefix).group(1)
        # Retry the request for the number of nodes.
        response = None
        for node_num in range(self.node_cnt):
            # Set full URL based on current node
            if '/api/' in url or '/cvpservice/' in url:
                full_url = self.url_prefix_short + url
            elif self.is_cvaas:
                # For CVaaS use cvpservice instead of web or api
                full_url = self.url_prefix_short + '/cvpservice' + url
            else:
                full_url = self.url_prefix + url
            try:
                response = self._send_request(req_type, full_url, timeout,
                                              data, files)
            except CvpApiError as error:
                # If this is not an Unauthorized CvpApiError raise the error
                # 'Unauthorized' is for 2018.x
                # 'User is unauthorized' is for 2019.x
                if ('Unauthorized' not in error.msg and
                        'User is unauthorized' not in error.msg):
                    raise error
                # If this is the final CVP node raise error
                if node_num + 1 == self.node_cnt:
                    raise error
                # Create a new session to retry on another CVP node.
                self._create_session()
                # Verify that we can connect to at least one node
                # otherwise raise the last error
                if not self.session:
                    raise error
                continue
            except (ConnectionError, HTTPError, TooManyRedirects, ReadTimeout,
                    Timeout, CvpSessionLogOutError) as error:
                # If this is the final CVP node raise error
                if node_num + 1 == self.node_cnt:
                    raise error
                # Create a new session to retry on another CVP node.
                self._create_session()
                # Verify that we can connect to at least one node
                # otherwise raise the last error
                if not self.session:
                    raise error
                continue
            break

        if not response:
            self.log.debug('Received no response for request %s %s',
                           req_type, url)
            return None

        # Added check for response.content being 'null' because of the
        # service account APIs being a special case /services/ API that
        # returns a null string for no objects instead of an empty string.
        if not response.content or response.content == b'null':
            return {'data': []}

        try:
            resp_data = response.json()
            if (resp_data is not None and 'result' in resp_data and
                    '/resources/' in full_url):
                # Resource APIs use JSON streaming and will return
                # multiple JSON objects during GetAll type API
                # calls. We are wrapping the multiple objects into
                # a key "data" and we also return a dictionary with
                # key "data" as an empty dict for no data. This
                # checks and keeps consistent the "data" key wrapper
                # for a Resource API GetAll that returns a single
                # object.
                return {'data': [resp_data]}
            return resp_data
        except JSONDecodeError as error:
            # Truncate long error messages
            err_str = str(error)
            if len(err_str) > 700:
                err_str = f"{err_str[:300]}[... truncated ...]" \
                          f" {err_str[-300:]}"
            self.log.debug('Error trying to decode request response - %s',
                           err_str)
            if 'Extra data' in str(error):
                self.log.debug('Found multiple objects or NO objects in'
                               ' response data. Attempt to decode')
                decoded_data = json_decoder(response.text)
                return {'data': decoded_data}
            self.log.error("Unknown format for JSONDecodeError - %s", err_str)
            raise error

    def _send_request(self, req_type, full_url, timeout, data=None,
                      files=None):
        ''' Make a GET, POST or DELETE request to CVP.  If the request call
            raises a timeout or CvpSessionLogOutError then the request will be
            retried on the same CVP node.  Otherwise the request will be tried
            on the next CVP node.

            Args:
                req_type (str): Either 'GET', 'POST' or 'DELETE'.
                full_url (str): Portion of request URL that comes after the
                    host.
                timeout (int): Number of seconds the client will wait between
                    bytes sent from the server.
                data (dict): Dict of key/value pairs to pass as parameters into
                    the request. Default is None.
                files (dict): Dict of file name to files for upload. Currently
                    only used for adding images to CVP. Default is None.

            Returns:
                The JSON response.

            Raises:
                ConnectionError: A ConnectionError is raised if there was a
                    network problem (e.g. DNS failure, refused connection, etc)
                CvpApiError: A CvpApiError is raised if there was a JSON error.
                CvpRequestError: A CvpRequestError is raised if the request
                    is not properly constructed.
                CvpSessionLogOutError: A CvpSessionLogOutError is raised if
                    response from server indicates session was logged out.
                HTTPError: A HTTPError is raised if there was an invalid HTTP
                    response.
                ReadTimeout: A ReadTimeout is raised if there was a request
                    timeout when reading from the connection.
                Timeout: A Timeout is raised if there was a request timeout.
                TooManyRedirects: A TooManyRedirects is raised if the request
                    exceeds the configured number of maximum re-directions
                ValueError: A ValueError is raised when there is no valid
                    CVP session.  This occurs because the previous get, post
                    or delete request failed and no session could be
                    established to a CVP node.  Destroy the class and
                    re-instantiate.
        '''
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-arguments
        # pylint: disable=raising-bad-type
        # For get or post requests apply both the connect and read timeout.
        timeout = (self.connect_timeout, timeout)
        for req_try in range(self.NUM_RETRY_REQUESTS):
            try:
                if req_type == 'GET':
                    response = self.session.get(full_url,
                                                cookies=self.cookies,
                                                headers=self.headers,
                                                timeout=timeout,
                                                verify=self.cert)
                elif req_type == 'POST':
                    if files is None:
                        response = self.session.post(full_url,
                                                     cookies=self.cookies,
                                                     data=json.dumps(data),
                                                     headers=self.headers,
                                                     timeout=timeout,
                                                     verify=self.cert)
                    else:
                        fhs = {}
                        fhs['Accept'] = self.headers['Accept']
                        if 'APP_SESSION_ID' in self.headers:
                            fhs['APP_SESSION_ID'] = self.headers[
                                'APP_SESSION_ID']
                        if 'Authorization' in self.headers:
                            fhs['Authorization'] = self.headers[
                                'Authorization']
                        response = self.session.post(full_url,
                                                     cookies=self.cookies,
                                                     headers=fhs,
                                                     timeout=timeout,
                                                     verify=self.cert,
                                                     files=files)
                elif req_type == 'DELETE':
                    response = self.session.delete(full_url,
                                                   cookies=self.cookies,
                                                   data=json.dumps(data),
                                                   headers=self.headers,
                                                   timeout=timeout,
                                                   verify=self.cert)
            except (ConnectionError, HTTPError, TooManyRedirects) as error:
                # Any of these errors is a good reason to try another CVP node
                self.log.error(error)
                raise error
            except (ReadTimeout, Timeout) as error:
                self.log.debug(error)
                # If there was a timeout and this is not the final try,
                # retry this request to the same node. If this is the final
                # try raise the error so another CVP node can be tried
                if req_try + 1 == self.NUM_RETRY_REQUESTS:
                    raise error
                continue

            try:
                self._is_good_response(response, f"{req_type}: {full_url} ")
            except CvpSessionLogOutError as error:
                self.log.debug(error)
                # Retry the request to the same node if there was a CVP session
                # logout. Reset the session which will login. If a valid
                # session comes back then clear the error so this request will
                # be retried on the same node.
                if req_try + 1 == self.NUM_RETRY_REQUESTS:
                    raise error
                self._reset_session()
                if not self.session:
                    raise error
                continue
            except CvpApiError as error:
                self.log.debug(error)
                if ('Unauthorized' in error.msg or
                        'User is unauthorized' in error.msg):
                    # Retry the request to the same node if there was an
                    # Unauthorized User error because this is how CVP responds
                    # to a logged out users requests in 2017.1.
                    # Check for 'User is unauthorized' in error because this is
                    # how CVP responds to a logged out user requests in 2019.x.
                    # Reset the session which will login. If a valid
                    # session comes back then clear the error so this request
                    # will be retried on the same node.
                    if req_try + 1 == self.NUM_RETRY_REQUESTS:
                        raise error
                    self._reset_session()
                    if not self.session:
                        raise error
                    continue
                # pylint: disable=raising-bad-type
                raise error
            return response

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
                    response from server indicates session was logged out.
                HTTPError: A HTTPError is raised if there was an invalid HTTP
                    response.
                ReadTimeout: A ReadTimeout is raised if there was a request
                    timeout when reading from the connection.
                Timeout: A Timeout is raised if there was a request timeout.
                TooManyRedirects: A TooManyRedirects is raised if the request
                    exceeds the configured number of maximum re-directions
                ValueError: A ValueError is raised when there is no valid
                    CVP session.  This occurs because the previous get, post
                    or delete request failed and no session could be
                    established to a CVP node.  Destroy the class and
                    re-instantiate.
        '''
        return self._make_request('GET', url, timeout)

    def post(self, url, data=None, files=None, timeout=30):
        ''' Make a POST request to CVP.  If the request call raises an error
            or if the JSON response contains a CVP session related error then
            retry the request on another CVP node.

            Args:
                url (str): Portion of request URL that comes after the host.
                data (dict): Dict of key/value pairs to pass as parameters into
                    the request. Default is None.
                files (dict): Dict of file name to files for upload. Currently
                    only used for adding images to CVP. Default is None.
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
                    response from server indicates session was logged out.
                HTTPError: A HTTPError is raised if there was an invalid HTTP
                    response.
                ReadTimeout: A ReadTimeout is raised if there was a request
                    timeout when reading from the connection.
                Timeout: A Timeout is raised if there was a request timeout.
                TooManyRedirects: A TooManyRedirects is raised if the request
                    exceeds the configured number of maximum re-directions
                ValueError: A ValueError is raised when there is no valid
                    CVP session.  This occurs because the previous get, post
                    or delete request failed and no session could be
                    established to a CVP node.  Destroy the class and
                    re-instantiate.
        '''
        return self._make_request('POST', url, timeout, data=data, files=files)

    def delete(self, url, data=None, timeout=30):
        ''' Make a DELETE request to CVP.  If the request call raises an error
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
                    response from server indicates session was logged out.
                HTTPError: A HTTPError is raised if there was an invalid HTTP
                    response.
                ReadTimeout: A ReadTimeout is raised if there was a request
                    timeout when reading from the connection.
                Timeout: A Timeout is raised if there was a request timeout.
                TooManyRedirects: A TooManyRedirects is raised if the request
                    exceeds the configured number of maximum re-directions
                ValueError: A ValueError is raised when there is no valid
                    CVP session.  This occurs because the previous get, post
                    or delete request failed and no session could be
                    established to a CVP node.  Destroy the class and
                    re-instantiate.
        '''
        return self._make_request('DELETE', url, timeout, data=data)

    def _finditem(self, obj, key):
        """ Find a key in a a nested list/dict.

            Args:
                obj (dict): Object to iterate to return value for provided key
                key (str): The key to locate in dict and return the value for

            Returns:
                Value of found key or None if not found.
        """
        item = None
        if isinstance(obj, dict):
            if key in obj:
                item = obj[key]
            else:
                for _, value in obj.items():
                    if isinstance(value, (dict, list)):
                        item = self._finditem(value, key)
                        if item is not None:
                            break
        elif isinstance(obj, list):
            for i in obj:
                if isinstance(i, (dict, list)):
                    item = self._finditem(i, key)
                    if item is not None:
                        break
        return item


def json_decoder(data):
    ''' Check for ...
    '''
    decoder = json.JSONDecoder()
    position = 0
    decoded_data = []
    while True:
        try:
            obj, position = decoder.raw_decode(data, position)
            decoded_data.append(obj)
            position += 1
        except ValueError:
            break
    if len(decoded_data) == 1:
        return decoded_data[0]
    return decoded_data

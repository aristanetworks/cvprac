Arista Cloudvision\ |reg| Portal RESTful API Client
===================================================
|pypi_version_badge|
|System_test_Status|

Table of Contents
=================
#. `Overview`_

   -  `Requirements`_

#. `Installation`_

   -  `Development: Run from Source`_

#. `Getting Started`_

   -  `Connecting`_
   -  `CVP On Premises`_
   -  `CVaaS`_
   -  `CVP Version Handling`_
   -  `Examples`_

#. `Testing`_
#. `License`_

Overview
========

This module provides a RESTful API client for Cloudvision\ |reg| Portal (CVP)
which can be used for building applications that work with Arista CVP.

When the class is instantiated the logging is configured. Either syslog,
file logging, both, or none can be enabled. If neither syslog nor
filename is specified then no logging will be performed.

This class supports creating a connection to a CVP node and then issuing
subsequent GET and POST requests to CVP. A GET or POST request will be
automatically retried on the same node if the request receives a
requests.exceptions.Timeout or ReadTimeout error. A GET or POST request
will be automatically retried on the same node if the request receives a
CvpSessionLogOutError. For this case a login will be performed before
the request is retried. For either case, the maximum number of times a
request will be retried on the same node is specified by the class
attribute NUM\_RETRY\_REQUESTS.

If more than one CVP node is specified when creating a connection, and a
GET or POST request that receives a requests.exceptions.ConnectionError,
requests.exceptions.HTTPError, or a requests.exceptions.TooManyRedirects
will be retried on the next CVP node in the list. If a GET or POST
request that receives a requests.exceptions.Timeout or
CvpSessionLogOutError and the retries on the same node exceed
NUM\_RETRY\_REQUESTS, then the request will be retried on the next node
on the list.

If any of the errors persists across all nodes then the GET or POST
request will fail and the last error that occurred will be raised.

The class provides connect, get, and post methods that allow the user to
make RESTful API calls to CVP. See the example below using the get
method.

The class provides a wrapper function around the CVP RESTful API
operations. Each API method takes the RESTful API parameters as method
parameters to the operation method. The API class was added to the
client class because the API functions are required when using the CVP
RESTful API and placing them in this library avoids duplicating the
calls in every application that uses this class. See the examples below
using the API methods.

Requirements
------------

-  Python 2.7 or later
-  Python logging module
-  Python requests module version 1.0.0 or later

Installation
============

The source code for cvprac is provided on Github at
https://github.com/aristanetworks/cvprac. All current development is
done in the develop branch. Stable released versions are tagged in the
master branch and uploaded to https://pypi.python.org.

If your platform has internet access you can use the Python Package
manager to install cvprac.

::

    admin:~ admin$ sudo pip install cvprac

You can upgrade cvprac

::

    admin:~ admin$ sudo pip install --upgrade cvprac

Development: Run from Source
----------------------------

We recommend running cvprac in a virtual environment. For more
information, read this:
http://docs.python-guide.org/en/latest/dev/virtualenvs/

These instructions will help you install and run cvprac from source.
This is useful if you plan on contributing or if you would always like
to see the latest code in the develop branch. Note that these steps
require the pip and git commands.

Step 1: Clone the cvprac Github repo
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    # Go to a directory where you'd like to keep the source
    admin:~ admin$ cd ~/projects
    admin:~ admin$ git clone https://github.com/aristanetworks/cvprac
    admin:~ admin$ cd cvprac

Step 2: Check out the desired version or branch
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    # Go to a directory where you'd like to keep the source
    admin:~ admin$ cd ~/projects/cvprac

    # To see a list of available versions or branches
    admin:~ admin$ git tag
    admin:~ admin$ git branch

    # Checkout the desired version of code
    admin:~ admin$ git checkout v1.0.3

Step 3: Install cvprac using Pip with -e switch
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    # Go to a directory where you'd like to keep the source
    admin:~ admin$ cd ~/projects/cvprac

    # Install
    admin:~ admin$ sudo pip install -e ~/projects/cvprac

Step 4: Install cvprac development requirements
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    # Go to a directory where you'd like to keep the source
    admin:~ admin$ pip install -r dev-requirements.txt

Getting Started
===============

Once the package has been installed you can run the following example to
verify that everything has been installed properly.

Connecting
----------

Connecting to CVP will depend on your CVP setup. Several options are outlined below.

CVP On Premises
---------------

CVP On Premises is for users with CVP running on a local server or cluster of servers. This is the
standard form of connection. Multiple examples below demonstrate connecting to CVP On Premises setups.

CVaaS
-----

CVaaS is CloudVision as a Service. Users with CVaaS must use a REST API token for accessing CVP with REST APIs.

   In the case where users authenticate with CVP (CVaaS) using Oauth a REST API token is required to be generated
   and used for running REST APIs. In this case no username/password login is necessary, but the API token
   (via api_token parameter) must be provided to cvprac client with the is_cvaas parameter.
   In the case that the api_token is used for REST APIs the username and password will be ignored and
   the tenant parameter is not needed.

An example of a CVaaS connection is shown below.

Note that the token parameter was previously cvaas_token but this has been converted to api_token because
tokens are also available for usage with On Prem CVP deployments. The api_token parameter name is more
generic in this sense. If you are using the cvaas_token parameter please convert to api_token because the
cvaas_token parameter will be deprecated in the future.


CVP Version Handling
--------------------

The CVP RESTful APIs often change between releases of CVP. Cvprac attempts to mask these API changes from
the user via making appropriate API calls based on the CVP version while attempting to maintain return data and
not changing function names when possible. This helps maintain backward compatibility for users when they upgrade CVP
so that any custom automation/scripts will continue to work. In some cases maintaining return data requires
additional API calls so there are cases where this comes with the cost of a slight performance hit. Users are free
to access the clients get(), post() and delete() methods and make API calls directly if they want to avoid the
potential time delay of some API functions. The current API version information handled by cvprac is shown below.

  Current latest API version is 4.0
  API version is set to latest available version for CVaaS
  API version is set to 4.0 for 2020.1.1 and beyond.
  API version is set to 3.0 for 2019.0.0 through 2020.1.0
  API version is set to 2.0 for 2018.2.X
  API version is set to 1.0 for 2018.1.X and prior

Examples
--------

Example using CVP On Prem client get method directly:

::

    >>> from cvprac.cvp_client import CvpClient
    >>> clnt = CvpClient()
    >>> clnt.connect(['cvp1', 'cvp2', 'cvp3'], 'cvp_user', 'cvp_word')
    >>> result = clnt.get('/cvpInfo/getCvpInfo.do')
    >>> print result
    {u'version': u'2016.1.0'}
    >>>

Same example as above using the API method:

::

    >>> from cvprac.cvp_client import CvpClient
    >>> clnt = CvpClient()
    >>> clnt.connect(['cvp1', 'cvp2', 'cvp3'], 'cvp_user', 'cvp_word')
    >>> result = clnt.api.get_cvp_info()
    >>> print result
    {u'version': u'2016.1.0'}
    >>>

Same example as above but connecting to CVaaS with a token:
Note that the username and password parameters are required by the connect function but will be ignored when using api_token:

::

    >>> from cvprac.cvp_client import CvpClient
    >>> clnt = CvpClient()
    >>> clnt.connect(nodes=['cvaas'], username='', password='', is_cvaas=True, api_token='user token')
    >>> result = clnt.api.get_cvp_info()
    >>> print result
    {u'version': u'cvaas'}
    >>>

Example using the API method to create a container, wait 5 seconds, then
delete the container. Before running this example manually create a
container named DC-1 on your CVP node.

::

    >>> import time
    >>> from cvprac.cvp_client import CvpClient
    >>> clnt = CvpClient()
    >>> clnt.connect(['cvp1'], 'cvp_user', 'cvp_word')
    >>> parent = clnt.api.search_topology('DC-1')
    >>> clnt.api.add_container('TORs', 'DC-1', parent['containerList'][0]['key'])
    >>> child = clnt.api.search_topology('TORs')
    >>> time.sleep(5)
    >>> result = clnt.api.delete_container('TORs', child['containerList'][0]['key'], 'DC-1', parent['containerList'][0]['key'])
    >>>

Notes for API Class Usage
=========================

Containers
----------

With the API the containers are added for all cases. If you add the
container to the original root container ‘Tenant’ then you have to do a
refresh from the GUI to see the container after it is added or deleted.
If the root container has been renamed or the parent container is not
the root container then an add or delete will update the GUI without
requiring a manual refresh.

Testing
=======

The cvprac module provides system tests. To run the system tests, you
will need to update the ``cvp_nodes.yaml`` file found in test/fixtures.

Requirements for running the system tests:

-  Need one CVP node for test with a test user account. Create the same
   account on the switch used for testing. The user account information
   follows:

::

    username: CvpRacTest
    password: AristaInnovates

    If switch does not have correct username and/or password then the tests that
    execute tasks will fail with the following error:

    AssertionError: Execution for task id 220 failed

    and in the test log is the error:

    Failure response received from the netElement : ' Unauthorized User '

-  Test has dedicated access to the CVP node.

-  CVP node contains at least one device in a container.

-  Container or device has at least one configlet applied.

To run the system tests:

-  run ``make tests`` from the root of the cvprac source folder.

Contributing
============

Contributing pull requests are gladly welcomed for this repository.
Please note that all contributions that modify the library behavior
require corresponding test cases otherwise the pull request will be
rejected.

Contact/Questions
=================

Cvprac is developed by Arista EOS+ CS and supported by the Arista EOS+ community. Support for the code is provided on a best effort basis by the Arista EOS+ CS team and the community. You can contact the team that develops these modules by sending an email to eosplus-dev@arista.com.

For customers that are looking for a premium level of support, please contact your local account team or email eosplus@arista.com for help.

License
=======

Copyright\ |copy| 2020, Arista Networks, Inc. All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

* Redistributions of source code must retain the above copyright notice,
  this list of conditions and the following disclaimer.

- Redistributions in binary form must reproduce the above copyright
  notice, this list of conditions and the following disclaimer in the
  documentation and/or other materials provided with the distribution.

* Neither the name of Arista Networks nor the names of its contributors
  may be used to endorse or promote products derived from this software
  without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL ARISTA NETWORKS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
THE POSSIBILITY OF SUCH DAMAGE.

.. |copy|   unicode:: U+000A9 .. COPYRIGHT SIGN
.. |trademark| unicode:: U+2122 .. TRADEMARK SIGN
.. |reg| unicode:: U+000AE .. REGISTERED SIGN
.. |pypi_version_badge| image:: https://img.shields.io/pypi/v/cvprac.svg
    :target: https://pypi.python.org/pypi/cvprac
.. |System_test_Status| image:: https://revproxy.arista.com/eosplus/ci/buildStatus/icon?job=Pipeline_jerearista_test/cvprac-rb/develop&style=plastic
   :target: https://revproxy.arista.com/eosplus/ci/job/Pipeline_jerearista_test/cvprac-rb/develop

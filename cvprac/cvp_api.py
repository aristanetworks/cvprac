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
''' Class containing calls to CVP RESTful API.
'''
import os
import time
# This import is for proper file IO handling support for both Python 2 and 3
# pylint: disable=redefined-builtin
from io import open
from datetime import datetime

from cvprac.cvp_client_errors import CvpApiError

try:
    from urllib import quote_plus as qplus
except (AttributeError, ImportError):
    from urllib.parse import quote_plus as qplus


class CvpApi(object):
    ''' CvpApi class contains calls to CVP RESTful API.  The RESTful API
        parameters are passed in as parameters to the method.  The results of
        the RESTful API call are converted from json to a dict and returned.
        Where needed minimal processing is performed on the results.
        Any method that does a cvprac get or post call could raise the
        following errors:

        ConnectionError: A ConnectionError is raised if there was a network
            problem (e.g. DNS failure, refused connection, etc)
        CvpApiError: A CvpApiError is raised if there was a JSON error.
        CvpRequestError: A CvpRequestError is raised if the request is not
            properly constructed.
        CvpSessionLogOutError: A CvpSessionLogOutError is raised if
            reponse from server indicates session was logged out.
        HTTPError: A HTTPError is raised if there was an invalid HTTP response.
        ReadTimeout: A ReadTimeout is raised if there was a request
            timeout when reading from the connection.
        Timeout: A Timeout is raised if there was a request timeout.
        TooManyRedirects: A TooManyRedirects is raised if the request exceeds
            the configured number of maximum redirections
        ValueError: A ValueError is raised when there is no valid
            CVP session.  This occurs because the previous get or post request
            failed and no session could be established to a CVP node.  Destroy
            the class and re-instantiate.
    '''
    # pylint: disable=too-many-public-methods
    # pylint: disable=too-many-lines

    def __init__(self, clnt, request_timeout=30):
        ''' Initialize the class.

            Args:
                clnt (obj): A CvpClient object
        '''
        self.clnt = clnt
        self.log = clnt.log
        self.request_timeout = request_timeout

    def get_cvp_info(self):
        ''' Returns information about CVP.

            Returns:
                cvp_info (dict): CVP Information
        '''
        if not self.clnt.is_cvaas:
            data = self.clnt.get('/cvpInfo/getCvpInfo.do',
                                 timeout=self.request_timeout)
        else:
            # For CVaaS do not run the getCvpInfo REST API and assume the
            # latest version of the API
            data = {'version': 'cvaas'}
        if 'version' in data and self.clnt.apiversion is None:
            self.clnt.set_version(data['version'])
        return data

    # pylint: disable=too-many-arguments
    def add_user(self, username, password, role, status, first_name,
                 last_name, email, user_type):
        ''' Add new local user to the CVP UI.

            Args:
                username (str): local username on CVP
                password (str): password of the user
                role (str): role of the user
                status (str): state of the user (Enabled/Disabled)
                first_name (str): first name of the user
                last_name (str): last name of the user
                email (str): email address of the user
                user_type (str): type of AAA (Local/TACACS/RADIUS)
        '''
        if status not in ['Enabled', 'Disabled']:
            self.log.error('Invalid status %s.'
                           ' Status must be Enabled or Disabled.'
                           ' Defaulting to Disabled' % status)
            status = 'Disabled'
        data = {"roles": [role],
                "user": {"contactNumber": "",
                         "email": email,
                         "firstName": first_name,
                         "lastName": last_name,
                         "password": password,
                         "userId": username,
                         "userStatus": status,
                         "userType": user_type}}
        return self.clnt.post('/user/addUser.do', data=data,
                              timeout=self.request_timeout)

    def update_user(self, username, password, role, status, first_name,
                    last_name, email, user_type):
        ''' Updates username information, like
            changing password, user role, email address, names,
            disable/enable the username.

            Args:
                username (str): local username on CVP
                password (str): password of the user
                role (str): role of the user
                status (str): state of the user (Enabled/Disabled)
                first_name (str): first name of the user
                last_name (str): last name of the user
                email (str): email address of the user
                user_type (str): type of AAA (Local/TACACS/RADIUS)
        '''
        if status not in ['Enabled', 'Disabled']:
            self.log.error('Invalid status %s.'
                           ' Status must be Enabled or Disabled.'
                           ' Defaulting to Disabled' % status)
            status = 'Disabled'
        data = {"roles": [role],
                "user": {"contactNumber": "",
                         "email": email,
                         "firstName": first_name,
                         "lastName": last_name,
                         "password": password,
                         "userId": username,
                         "userStatus": status,
                         "userType": user_type}}
        return self.clnt.post('/user/updateUser.do?userId={}'.format(username),
                              data=data, timeout=self.request_timeout)

    def get_user(self, username):
        ''' Returns specified user information

            Args:
                username (str): username on CVP
        '''
        return self.clnt.get('/user/getUser.do?userId={}'.format(username),
                             timeout=self.request_timeout)

    def delete_user(self, username):
        ''' Remove specified user from CVP

            Args:
                username (str): username on CVP
        '''
        data = [username]
        return self.clnt.post('/user/deleteUsers.do', data=data,
                              timeout=self.request_timeout)

    def get_task_by_id(self, task_id):
        ''' Returns the current CVP Task status for the task with the specified
            TaskId.

            Args:
                task_id (int): CVP task identifier

            Returns:
                task (dict): The CVP task for the associated Id.  Returns None
                    if the task_id was invalid.
        '''
        self.log.debug('get_task_by_id: task_id: %s' % task_id)
        try:
            task = self.clnt.get('/task/getTaskById.do?taskId=%s' % task_id,
                                 timeout=self.request_timeout)
        except CvpApiError as error:
            self.log.debug('Caught error: %s attempting to get task.' % error)
            # Catch an invalid task_id error and return None
            return None
        return task

    def get_tasks_by_status(self, status, start=0, end=0):
        ''' Returns a list of tasks with the given status.

            Args:
                status (str): Task status
                start (int): Start index for the pagination.  Default is 0.
                end (int): End index for the pagination.  If end index is 0
                    then all the records will be returned.  Default is 0.

            Returns:
                tasks (list): The list of tasks
        '''
        self.log.debug('get_tasks_by_status: status: %s' % status)
        data = self.clnt.get(
            '/task/getTasks.do?queryparam=%s&startIndex=%d&endIndex=%d' %
            (status, start, end), timeout=self.request_timeout)
        return data['data']

    def get_tasks(self, start=0, end=0):
        ''' Returns a list of all the tasks.

            Args:
                start (int): Start index for the pagination.  Default is 0.
                end (int): End index for the pagination.  If end index is 0
                    then all the records will be returned.  Default is 0.

            Returns:
                tasks (dict): The 'total' key contains the number of tasks,
                    the 'data' key contains a list of the tasks.
        '''
        self.log.debug('get_tasks:')
        return self.clnt.get('/task/getTasks.do?queryparam=&startIndex=%d&'
                             'endIndex=%d' % (start, end),
                             timeout=self.request_timeout)

    def get_logs_by_id(self, task_id, start=0, end=0):
        ''' Returns the log entries for the task with the specified TaskId.

            Args:
                task_id (int): CVP task identifier
                start (int): The first log entry to return.  Default is 0.
                end (int): The last log entry to return.  Default is 0 which
                    means to return all log entries.  Can be a large number to
                    indicate the last log entry.

            Returns:
                task (dict): The CVP log for the associated Id.  Returns None
                    if the task_id was invalid.
        '''
        self.log.debug('get_logs_by_id: task_id: %s' % task_id)
        if self.clnt.apiversion is None:
            self.get_cvp_info()
        if self.clnt.apiversion < 5.0:
            self.log.debug('v1 - v4 /task/getLogsByID.do?')
            resp = self.clnt.get('/task/getLogsById.do?id=%s&queryparam='
                                 '&startIndex=%d&endIndex=%d' %
                                 (task_id, start, end),
                                 timeout=self.request_timeout)
        else:
            self.log.debug('v5 /audit/getLogs.do')
            task_info = self.get_task_by_id(task_id)
            stage_id = None
            if 'stageId' in task_info:
                stage_id = task_info['stageId']
            else:
                self.log.debug('No stage ID found for task %s' % task_id)
            if 'ccIdV2' in task_info:
                cc_id = task_info['ccIdV2']
                if cc_id == '':
                    self.log.debug('No ccIdV2 for task %s.'
                                   ' It was likely cancelled.'
                                   ' Using old /task/getLogsByID.do?'
                                   % task_id)
                    resp = self.clnt.get(
                        '/task/getLogsById.do?id=%s&queryparam='
                        '&startIndex=%d&endIndex=%d' % (task_id, start, end),
                        timeout=self.request_timeout)
                else:
                    resp = self.get_audit_logs_by_id(cc_id, stage_id)
            else:
                self.log.debug('No change ID found for task %s' % task_id)
                resp = None
        return resp

    def get_audit_logs_by_id(self, cc_id, stage_id=None, data_size=75):
        ''' Returns the audit logs of a particular ChangeControl.

            Args:
                cc_id (string): change control ID from ccIdV2 field
                stage_id (string): stage ID from stageId field
                data_size (int): data size

            Returns:
                task (dict): The CVP log for the associated ccIdV2
        '''
        data = {"category": "ChangeControl",
                "startTime": 0,
                "endTime": 0,
                "dataSize": data_size,
                "objectKey": cc_id,
                "lastRetrievedAudit": {}}
        if stage_id:
            data["tags"] = {"stageId": stage_id}
        return self.clnt.post('/cvpservice/audit/getLogs.do?', data=data,
                              timeout=self.request_timeout)

    def add_note_to_task(self, task_id, note):
        ''' Add notes to the task.

            Args:
                task_id (str): Task ID
                note (str): Note to add to the task
        '''
        self.log.debug('add_note_to_task: task_id: %s note: %s' %
                       (task_id, note))
        data = {'workOrderId': task_id, 'note': note}
        self.clnt.post('/task/addNoteToTask.do', data=data,
                       timeout=self.request_timeout)

    def execute_task(self, task_id):
        ''' Execute the task.  Note that if the task has failed then inspect
            the task logs to determine why the task failed.  If you see:

              Failure response received from the netElement: Unauthorized User

            then it means that the netelement does not have the same user ID
            and/or password as the CVP user executing the task.

            Args:
                task_id (str): Task ID
        '''
        self.log.debug('execute_task: task_id: %s' % task_id)
        data = {'data': [task_id]}
        self.clnt.post('/task/executeTask.do', data=data,
                       timeout=self.request_timeout)

    def cancel_task(self, task_id):
        ''' Cancel the task

            Args:
                task_id (str): Task ID
        '''
        self.log.debug('cancel_task: task_id: %s' % task_id)
        data = {'data': [task_id]}
        return self.clnt.post('/task/cancelTask.do', data=data,
                              timeout=self.request_timeout)

    def get_configlets(self, start=0, end=0):
        ''' Returns a list of all defined configlets.

            Args:
                start (int): Start index for the pagination. Default is 0.
                end (int): End index for the pagination. If end index is 0
                    then all the records will be returned. Default is 0.
        '''
        if self.clnt.apiversion is None:
            self.get_cvp_info()
        configlets = self.clnt.get('/configlet/getConfiglets.do?'
                                   'startIndex=%d&endIndex=%d' % (start, end),
                                   timeout=self.request_timeout)
        if self.clnt.apiversion == 1.0:
            self.log.debug('v1 Inventory API Call')
            return configlets
        else:
            self.log.debug('v2 Inventory API Call')
            # New API getConfiglets does not return the actual configlet config
            # Get the actual configlet config using getConfigletByName
            if 'data' in configlets:
                for configlet in configlets['data']:
                    full_cfglt_data = self.get_configlet_by_name(
                        configlet['name'])
                    configlet['config'] = full_cfglt_data['config']
            return configlets

    def get_configlets_and_mappers(self):
        ''' Returns a list of all defined configlets and associated mappers
        '''
        self.log.debug(
            'get_configlets_and_mappers: getConfigletsAndAssociatedMappers')
        return self.clnt.get('/configlet/getConfigletsAndAssociatedMappers.do')

    def get_configlet_builder(self, c_id):
        ''' Returns the configlet builder data for the given configlet ID.

            Args:
                c_id (str): The ID (key) for the configlet to be queried.
        '''
        return self.clnt.get('/configlet/getConfigletBuilder.do?id=%s'
                             % c_id, timeout=self.request_timeout)

    def search_configlets(self, query, start=0, end=0):
        ''' Returns a list of configlets that match a search query.

            Args:
                query (str): A simple string of text to be matched against
                    the existing configlets. Not a regex.
                start (int): Start index for the pagination. Default is 0.
                end (int): End index for the pagination. If end index is 0
                    then all the records will be returned. Default is 0.
        '''
        self.log.debug('search_configlets: query: %s' % query)
        return self.clnt.get('/configlet/searchConfiglets.do?'
                             'queryparam=%s&startIndex=%d&endIndex=%d' %
                             (qplus(query), start, end),
                             timeout=self.request_timeout)

    def get_configlet_by_name(self, name):
        ''' Returns the configlet with the specified name

            Args:
                name (str): Name of the configlet.  Can contain spaces.

            Returns:
                configlet (dict): The configlet dict.
        '''
        self.log.debug('get_configlets_by_name: name: %s' % name)
        return self.clnt.get('/configlet/getConfigletByName.do?name=%s'
                             % qplus(name), timeout=self.request_timeout)

    def get_configlets_by_container_id(self, c_id, start=0, end=0):
        ''' Returns a list of configlets applied to the given container.

            Args:
                c_id (str): The container ID (key) to query.
                start (int): Start index for the pagination. Default is 0.
                end (int): End index for the pagination. If end index is 0
                    then all the records will be returned. Default is 0.
        '''
        return self.clnt.get('/provisioning/getConfigletsByContainerId.do?'
                             'containerId=%s&startIndex=%d&endIndex=%d'
                             % (c_id, start, end),
                             timeout=self.request_timeout)

    def get_configlets_by_netelement_id(self, d_id, start=0, end=0):
        ''' Returns a list of configlets applied to the given device.

            Args:
                d_id (str): The device ID (key) to query.
                start (int): Start index for the pagination. Default is 0.
                end (int): End index for the pagination. If end index is 0
                    then all the records will be returned. Default is 0.
        '''
        return self.clnt.get('/provisioning/getConfigletsByNetElementId.do?'
                             'netElementId=%s&startIndex=%d&endIndex=%d'
                             % (d_id, start, end),
                             timeout=self.request_timeout)

    def get_image_bundle_by_container_id(self, container_id, start=0, end=0,
                                         scope='false'):
        ''' Returns a list of ImageBundles applied to the given container.
            Args:
                container_id (str): The container ID (key) to query.
                start (int): Start index for the pagination. Default is 0.
                end (int): End index for the pagination. If end index is 0
                    then all the records will be returned. Default is 0.
                scope (string) the session scope (true or false).
        '''
        if scope != 'true' and scope != 'false':
            self.log.error('scope value must be true or false.'
                           ' %s is an invalid value.'
                           ' Defaulting back to false' % scope)
            scope = 'false'
        return self.clnt.get('/provisioning/getImageBundleByContainerId.do?'
                             'containerId=%s&startIndex=%d&endIndex=%d'
                             '&sessionScope=%s'
                             % (container_id, start, end, scope),
                             timeout=self.request_timeout)

    def get_configlet_history(self, key, start=0, end=0):
        ''' Returns the configlet history.

            Args:
                key (str): Key for the configlet.
                start (int): The first configlet entry to return.  Default is 0
                end (int): The last configlet entry to return.  Default is 0
                    which means to return all configlet entries.  Can be a
                    large number to indicate the last configlet entry.

            Returns:
                history (dict): The configlet dict with the changes from
                    most recent to oldest.
        '''
        self.log.debug('get_configlets_history: key: %s' % key)
        return self.clnt.get('/configlet/getConfigletHistory.do?configletId='
                             '%s&queryparam=&startIndex=%d&endIndex=%d' %
                             (key, start, end), timeout=self.request_timeout)

    def get_inventory(self, start=0, end=0, query=''):
        ''' Returns the a dict of the net elements known to CVP.

            Args:
                start (int): The first inventory entry to return.  Default is 0
                end (int): The last inventory entry to return.  Default is 0
                    which means to return all inventory entries.  Can be a
                    large number to indicate the last inventory entry.
                query (string): A value that can be used as a match to filter
                    returned inventory list. For example get all switches that
                    are running a specific version of EOS.
        '''
        self.log.debug('get_inventory: called')
        if self.clnt.apiversion is None:
            self.get_cvp_info()
        if self.clnt.apiversion == 1.0:
            self.log.debug('v1 Inventory API Call')
            data = self.clnt.get('/inventory/getInventory.do?'
                                 'queryparam=%s&startIndex=%d&endIndex=%d' %
                                 (qplus(query), start, end),
                                 timeout=self.request_timeout)
            return data['netElementList']
        self.log.debug('v2 Inventory API Call')
        data = self.clnt.get('/inventory/devices?provisioned=true',
                             timeout=self.request_timeout)
        containers = self.get_containers()
        for dev in data:
            dev['key'] = dev['systemMacAddress']
            dev['deviceInfo'] = dev['deviceStatus'] = dev['status']
            dev['isMLAGEnabled'] = dev['mlagEnabled']
            dev['isDANZEnabled'] = dev['danzEnabled']
            dev['parentContainerId'] = dev['parentContainerKey']
            dev['bootupTimeStamp'] = dev['bootupTimestamp']
            dev['internalBuildId'] = dev['internalBuild']
            if 'taskIdList' not in dev:
                dev['taskIdList'] = []
            if 'tempAction' not in dev:
                dev['tempAction'] = None
            dev['memTotal'] = 0
            dev['memFree'] = 0
            dev['sslConfigAvailable'] = False
            dev['sslEnabledByCVP'] = False
            dev['lastSyncUp'] = 0
            dev['type'] = 'netelement'
            dev['dcaKey'] = None
            container_found = False
            for container in containers['data']:
                if dev['parentContainerKey'] == container['key']:
                    dev['containerName'] = container['name']
                    container_found = True
            if not container_found:
                dev['containerName'] = ''
        return data

    def add_devices_to_inventory(self, device_list, wait=False):
        ''' Add a list of devices to the specified parent container.

            Args:
                device_list (list): A list of devices to be added in the
                    form of dictionaries. Each device dictionary should
                    contain the following information:
                    - device_ip (str): ip address of device we are adding
                    - parent_name (str): Parent container name
                    - parent_key (str): Parent container key
                wait (boolean): Specifies whether to allow a wait time for
                    devices to appear in inventory before moving them to
                    the specified container. Applies to v2 API only.

            Example device list:
                device_list = [
                    {
                        device_ip: '10.10.10.1',
                        parent_name: 'Tenant',
                        parent_key: 'root'
                    },
                    {
                        device_ip: '10.10.10.2',
                        parent_name: 'MyContainer',
                        parent_key: 'container-id-1234'
                    }
                ]
        '''

        self.log.debug('add_device_to_inventory: called')
        if self.clnt.apiversion is None:
            self.get_cvp_info()
        if self.clnt.apiversion == 1.0:
            self.log.debug('v1 Inventory API Call')
            data_list = []
            for device in device_list:
                dev_data = {
                    'containerName': device['parent_name'],
                    'containerId': device['parent_key'],
                    'containerType': 'Existing',
                    'ipAddress': device['device_ip'],
                    'containerList': []
                }
                data_list.append(dev_data)
            data = {'data': data_list}
            self.clnt.post('/inventory/add/addToInventory.do?'
                           'startIndex=0&endIndex=0', data=data,
                           timeout=self.request_timeout)
        else:
            self.log.debug('v2 Inventory API Call')

            # Create a list of device IPs
            device_ips = [dev['device_ip'] for dev in device_list]

            # First add the devices to the inventory in a single call
            data = {'hosts': device_ips}
            self.clnt.post('/inventory/devices', data=data,
                           timeout=self.request_timeout)

            # Get the inventory list
            inv = self.get_inventory()

            if wait:
                # With v2, the devices can take a few moments to appear
                # We need them present before we can move them to a container
                timeout = time.time() + 600
                while device_ips and time.time() < timeout:
                    inv_devices = [dev['ipAddress'] for dev in inv]
                    device_ips = list(set(device_ips) - set(inv_devices))
                    if device_ips:
                        time.sleep(2)
                        inv = self.get_inventory()

                if device_ips:
                    # If any devices did not appear, there is a problem
                    # Join the missing IPs into a string for output
                    missing_ips = ', '.join(device_ips)
                    raise RuntimeError('Devices {} failed to appear '
                                       'in inventory'.format(missing_ips))

            # Move the devices to their specified containers
            for device in device_list:
                devs = [dev for dev in inv if 'ipAddress' in dev and
                        device['device_ip'] in dev['ipAddress']]
                dev = devs[0]
                container = {'key': device['parent_key'],
                             'name': device['parent_name']}
                self.move_device_to_container('add_device_to_inventory API v2',
                                              dev, container, False)

    def add_device_to_inventory(self, device_ip, parent_name,
                                parent_key, wait=False):
        ''' Add the device to the specified parent container.

            Args:
                device_ip (str): ip address of device we are adding
                parent_name (str): Parent container name
                parent_key (str): Parent container key
        '''
        # Put parameters into a dictionary and call add_devices_to_inventory
        device = {
            'device_ip': device_ip,
            'parent_name': parent_name,
            'parent_key': parent_key
        }
        self.add_devices_to_inventory([device], wait=wait)

    def retry_add_to_inventory(self, device_mac, device_ip, username,
                               password):
        '''Retry addition of device to Cvp inventory

            Args:
                device_mac (str): MAC address of device
                device_ip (str): ip address assigned to device
                username (str): username for device login
                password (str): password for user
        '''
        self.log.debug('retry_add_to_inventory: called')
        if self.clnt.apiversion is None:
            self.get_cvp_info()
        if self.clnt.apiversion == 1.0:
            self.log.debug('v1 Inventory API Call')
            data = {"key": device_mac,
                    "ipAddress": device_ip,
                    "userName": username,
                    "password": password}
            self.clnt.post('/inventory/add/retryAddDeviceToInventory.do?'
                           'startIndex=0&endIndex=0',
                           data=data,
                           timeout=self.request_timeout)
        else:
            self.log.debug('v2 Inventory API Call')
            self.log.warning(
                'retry_add_to_inventory: not implemented for v2 APIs')

    def delete_device(self, device_mac):
        '''Delete the device and its pending tasks from Cvp inventory

            Args:
                device_mac (str): mac address of device we are deleting
                                  For CVP 2020 this param is now required to
                                  be the device serial number instead of MAC
                                  address. This method will handle getting
                                  the device serial number via the provided
                                  MAC address.
            Returns:
                data (dict): Contains success or failure message
        '''
        self.log.debug('delete_device: called')
        return self.delete_devices([device_mac])

    def delete_devices(self, device_macs):
        '''Delete the device and its pending tasks from Cvp inventory

            Args:
                device_macs (list): list of mac address for
                                    devices we're deleting
                                    For CVP 2020 this param is now required to
                                    be a list of device serial numbers instead
                                    of MAC addresses. This method will handle
                                    getting the device serial number via the
                                    provided MAC address.
            Returns:
                data (dict): Contains success or failure message
        '''
        self.log.debug('delete_devices: called')
        resp = None
        if self.clnt.apiversion is None:
            self.get_cvp_info()
        if self.clnt.apiversion < 4.0:
            data = {'data': device_macs}
            resp = self.clnt.post('/inventory/deleteDevices.do?', data=data,
                                  timeout=self.request_timeout)
        else:
            self.log.warning('NOTE: The Delete Devices API has updated for'
                             ' CVP 2020.2 and it is not required to send the'
                             ' device serial number instead of mac address'
                             ' when deleting a device. Looking up each devices'
                             'serial num based on provided MAC addresses')
            devices = []
            for dev_mac in device_macs:
                device_info = self.get_device_by_mac(dev_mac)
                if device_info is not None and 'serialNumber' in device_info:
                    devices.append(device_info)
            resp = self.delete_devices_by_serial(devices)
        return resp

    def delete_devices_by_serial(self, devices):
        '''Delete the device and its pending tasks from Cvp inventory

            Args:
                devices (list): list of device objects to be deleted

            Returns:
                data (dict): Contains success or failure message
        '''
        device_serials = []
        for device in devices:
            device_serials.append(device['serialNumber'])
        data = {'data': device_serials}
        resp = self.clnt.delete('/inventory/devices', data=data,
                                timeout=self.request_timeout)
        return resp

    def get_non_connected_device_count(self):
        '''Returns number of devices not accessible/connected in the temporary
           inventory.

            Returns:
                data (int): Number of temporary inventory devices not
                            accessible/connected
        '''
        self.log.debug('get_non_connected_device_count: called')
        if self.clnt.apiversion is None:
            self.get_cvp_info()
        if self.clnt.apiversion == 1.0:
            self.log.debug('v1 Inventory API Call')
            data = self.clnt.get(
                '/inventory/add/getNonConnectedDeviceCount.do',
                timeout=self.request_timeout)
            return data['data']
        self.log.debug('v2 Inventory API Call')
        data = self.clnt.get('/inventory/devices?provisioned=false',
                             timeout=self.request_timeout)
        unprovisioned_devs = 0
        for dev in data:
            if 'status' in dev and dev['status'] == '':
                unprovisioned_devs += 1
        return unprovisioned_devs

    def save_inventory(self):
        '''Saves Cvp inventory state
        '''
        self.log.debug('save_inventory: called')
        if self.clnt.apiversion is None:
            self.get_cvp_info()
        if self.clnt.apiversion == 1.0:
            self.log.debug('v1 Inventory API Call')
            return self.clnt.post('/inventory/add/saveInventory.do',
                                  timeout=self.request_timeout)
        self.log.debug('v2 Inventory API Call')
        message = 'Save Inventory not implemented/necessary for' +\
                  ' CVP 2018.2 and beyond'
        data = {'data': 0, 'message': message}
        return data

    def get_devices_in_container(self, name):
        ''' Returns a dict of the devices under the named container.

            Args:
                name (str): The name of the container to get devices from
        '''
        self.log.debug('get_devices_in_container: called')
        devices = []
        container = self.get_container_by_name(name)
        if container:
            all_devices = self.get_inventory(0, 0, name)
            for device in all_devices:
                if device['parentContainerId'] == container['key']:
                    devices.append(device)
        return devices

    def get_device_by_name(self, fqdn):
        ''' Returns the net element device dict for the devices fqdn name.

            Args:
                fqdn (str): Fully qualified domain name of the device.

            Returns:
                device (dict): The net element device dict for the device if
                    otherwise returns an empty hash.
        '''
        self.log.debug('get_device_by_name: fqdn: %s' % fqdn)
        # data = self.get_inventory(start=0, end=0, query=fqdn)
        data = self.search_topology(fqdn)
        device = {}
        if 'netElementList' in data:
            for netelem in data['netElementList']:
                if netelem['fqdn'] == fqdn:
                    device = netelem
                    break
        return device

    def get_device_by_mac(self, device_mac):
        ''' Returns the net element device dict for the devices mac address.

            Args:
                device_mac (str): MAC Address of the device.

            Returns:
                device (dict): The net element device dict for the device if
                    otherwise returns an empty hash.
        '''
        self.log.debug('get_device_by_mac: MAC address: %s' % device_mac)
        # data = self.get_inventory(start=0, end=0, query=device_mac)
        data = self.search_topology(device_mac)
        device = {}
        if 'netElementList' in data:
            for netelem in data['netElementList']:
                if netelem['systemMacAddress'] == device_mac:
                    device = netelem
                    break
        return device

    def get_device_configuration(self, device_mac):
        ''' Returns the running configuration for the device provided.

            Args:
                device_mac (str): Mac address of the device to get the running
                    configuration for.

            Returns:
                device (dict): The net element device dict for the device if
                    otherwise returns an empty hash.
        '''
        self.log.debug('get_device_configuration: device_mac: %s' % device_mac)
        if self.clnt.apiversion is None:
            self.get_cvp_info()
        if self.clnt.apiversion < 4.0:
            data = self.clnt.get('/inventory/getInventoryConfiguration.do?'
                                 'netElementId=%s' % device_mac,
                                 timeout=self.request_timeout)
        else:
            data = self.clnt.get('/inventory/device/config?'
                                 'netElementId=%s' % device_mac,
                                 timeout=self.request_timeout)
        running_config = ''
        if 'output' in data:
            running_config = data['output']
        return running_config

    def get_device_image_info(self, device_mac):
        ''' Return a dict of info about a device in CVP.

            Args:
                device_mac (str): Mac address of the device to get the running
                    configuration for.

            Returns:
                device_image_info (dict): Dict of image info for the device
                    if found. Otherwise returns None.
        '''
        self.log.debug('Attempt to get net element data for %s' % device_mac)
        try:
            device_image_info = self.clnt.get(
                '/provisioning/getNetElementInfoById.do?netElementId=%s'
                % qplus(device_mac), timeout=self.request_timeout)
        except CvpApiError as error:
            # Catch error when device for provided MAC is not found
            if 'Invalid Netelement id' in str(error):
                self.log.debug('Device with MAC %s not found' % device_mac)
                return None
            raise error
        return device_image_info

    def get_containers(self, start=0, end=0):
        ''' Returns a list of all the containers.

            Args:
                start (int): Start index for the pagination.  Default is 0.
                end (int): End index for the pagination.  If end index is 0
                    then all the records will be returned.  Default is 0.

            Returns:
                containers (dict): The 'total' key contains the number of
                containers, the 'data' key contains a list of the containers
                with associated info.
        '''
        self.log.debug('Get list of containers')
        if self.clnt.apiversion is None:
            self.get_cvp_info()
        if self.clnt.apiversion == 1.0:
            self.log.debug('v1 Inventory API Call')
            return self.clnt.get('/inventory/add/searchContainers.do?'
                                 'startIndex=%d&endIndex=%d' % (start, end))
        self.log.debug('v2 Inventory API Call')
        containers = self.clnt.get('/inventory/containers')
        for container in containers:
            container['name'] = container['Name']
            container['key'] = container['Key']
            full_cont_info = self.get_container_by_id(
                container['Key'])
            if (full_cont_info is not None and
                    container['Key'] != 'root'):
                container['parentName'] = full_cont_info['parentName']
                for cont in containers:
                    if cont['Name'] == full_cont_info['parentName']:
                        container['parentId'] = cont['Key']
                        break
                else:
                    self.log.debug(
                        'No container parentId found for parentName %s',
                        full_cont_info['parentName'])
                    container['parentId'] = None
            else:
                container['parentName'] = None
                container['parentId'] = None
            container['type'] = None
            container['id'] = 21
            container['factoryId'] = 1
            container['userId'] = None
            container['childContainerId'] = None
        return {'data': containers, 'total': len(containers)}

    def get_container_by_name(self, name):
        ''' Returns a container that exactly matches the name.

            Args:
                name (str): String to search for in container names.

            Returns:
                container (dict): Container info in dictionary format or None
        '''
        self.log.debug('Get info for container %s' % name)
        conts = self.clnt.get('/provisioning/searchTopology.do?queryParam=%s'
                              '&startIndex=0&endIndex=0' % qplus(name))
        if conts['total'] > 0 and conts['containerList']:
            for cont in conts['containerList']:
                if cont['name'] == name:
                    return cont
        return None

    def get_container_by_id(self, key):
        ''' Returns a container for the given id.

            Args:
                key (str): String ID for container to find.

            Returns:
                container (dict): Container info in dictionary format or None
        '''
        self.log.debug('Get info for container %s' % key)
        return self.clnt.get('/provisioning/getContainerInfoById.do?'
                             'containerId=%s' % qplus(key))

    def get_configlets_by_device_id(self, mac, start=0, end=0):
        ''' Returns the list of configlets applied to a device.

            Args:
                mac (str): Device mac address (i.e. device id)
                start (int): The first configlet entry to return.  Default is 0
                end (int): The last configlet entry to return.  Default is 0
                    which means to return all configlet entries.  Can be a
                    large number to indicate the last configlet entry.

            Returns:
                configlets (list): The list of configlets applied to the device
        '''
        self.log.debug('get_configlets_by_device: mac: %s' % mac)
        data = self.get_configlets_by_netelement_id(mac, start, end)
        return data['configletList']

    def add_configlet_builder(self, name, config, draft=False, form=None):
        ''' Add a confilget builder and return the key for the configlet builder.

            Args:
                name (str): Configlet builder name
                config (str): Python configlet builder code
                draft (bool): If builder is a draft
                form (list): Array/list of form data
                    Parameters:
                        fieldId (str):
                        fieldLabel (str):
                        value (str):
                        type (str): {
                            'Text box',
                            'Text area',
                            'Drop down',
                            'Check box',
                            'Radio button',
                            'IP address',
                            'Password'
                        }
                        validation:
                            mandatory (boolean):
                        helpText (str)

            Returns:
                key (str): The key for the configlet
        '''
        if not form:
            form = []

        self.log.debug('add_configlet_builder: name: %s config: %s form: %s'
                       % (name, config, form))
        data = {'name': name,
                'data': {'formList': form,
                         'main_script': {'data': config}}}
        # Create the configlet builder
        self.clnt.post('/configlet/addConfigletBuilder.do?isDraft=%s' % draft,
                       data=data, timeout=self.request_timeout)

        # Get the key for the configlet
        data = self.clnt.get(
            '/configlet/getConfigletByName.do?name=%s' % qplus(name),
            timeout=self.request_timeout)
        return data['key']

    def add_configlet(self, name, config):
        ''' Add a configlet and return the key for the configlet.

            Args:
                name (str): Configlet name
                config (str): Switch config statements

            Returns:
                key (str): The key for the configlet
        '''
        self.log.debug('add_configlet: name: %s config: %s' % (name, config))
        body = {'name': name, 'config': config}
        # Create the configlet
        self.clnt.post('/configlet/addConfiglet.do', data=body,
                       timeout=self.request_timeout)

        # Get the key for the configlet
        data = self.clnt.get('/configlet/getConfigletByName.do?name=%s'
                             % qplus(name), timeout=self.request_timeout)
        return data['key']

    def delete_configlet(self, name, key):
        ''' Delete the configlet.

            Args:
                name (str): Configlet name
                key (str): Configlet key
        '''
        self.log.debug('delete_configlet: name: %s key: %s' % (name, key))
        body = [{'name': name, 'key': key}]
        # Delete the configlet
        self.clnt.post('/configlet/deleteConfiglet.do', data=body,
                       timeout=self.request_timeout)

    def update_configlet(self, config, key, name, wait_task_ids=False):
        ''' Update a configlet.

            Args:
                config (str): Switch config statements
                key (str): Configlet key
                name (str): Configlet name
                wait_task_ids (boolean): Wait for task IDs to generate

            Returns:
                data (dict): Contains success or failure message
        '''
        self.log.debug('update_configlet: config: %s key: %s name: %s' %
                       (config, key, name))

        # Update the configlet
        body = {'config': config, 'key': key, 'name': name,
                'waitForTaskIds': wait_task_ids}
        return self.clnt.post('/configlet/updateConfiglet.do', data=body,
                              timeout=self.request_timeout)

    def update_configlet_builder(self, name, key, config, draft=False,
                                 wait_for_task=False):
        ''' Update an existing configlet builder.
            Args:
                config (str): Contents of the configlet builder configuration
                key: (str): key/id of the configlet builder to be updated
                name: (str): name of the configlet builder
                draft (boolean): is update a draft
                wait_for_task (boolean): wait for task IDs to be generated
        '''
        data = {
            "name": name,
            "waitForTaskIds": wait_for_task,
            "data": {
                "main_script": {
                    "data": config
                }
            }
        }
        debug_str = 'update_configlet_builder:' \
                    ' config: {} key: {} name: {} '
        self.log.debug(debug_str.format(config, key, name))
        # Update the configlet builder
        url_string = '/configlet/updateConfigletBuilder.do?' \
                     'isDraft={}&id={}&action=save'
        return self.clnt.post(url_string.format(draft, key),
                              data=data, timeout=self.request_timeout)

    def update_reconcile_configlet(self, device_mac, config, key, name,
                                   reconciled=False):
        ''' Update the reconcile configlet.

            Args:
                device_mac (str): Mac address/Key for device whose reconcile
                    configlet is being updated
                config (str): Reconciled config statements
                key (str): Reconcile Configlet key
                name (str): Reconcile Configlet name
                reconciled (boolean): Wait for task IDs to generate

            Returns:
                data (dict): Contains success or failure message
        '''
        log_str = ('update_reconcile_configlet:'
                   ' device_mac: {} config: {} key: {} name: {}')
        self.log.debug(log_str.format(device_mac, config, key, name))

        url_str = ('/provisioning/updateReconcileConfiglet.do?'
                   'netElementId={}')
        body = {
            'config': config,
            'key': key,
            'name': name,
            'reconciled': reconciled,
            'unCheckedLines': '',
        }
        return self.clnt.post(url_str.format(device_mac), data=body,
                              timeout=self.request_timeout)

    def add_note_to_configlet(self, key, note):
        ''' Add a note to a configlet.

            Args:
                key (str): Configlet key
                note (str): Note to be added to configlet.
        '''
        data = {
            'key': key,
            'note': note,
        }
        return self.clnt.post('/configlet/addNoteToConfiglet.do',
                              data=data, timeout=self.request_timeout)

    def validate_config(self, device_mac, config):
        ''' Validate a config against a device

            Args:
                device_mac (str): Device MAC address
                config (str): Switch config statements

            Returns:
                response (dict): A dict that contains the result of the
                    validation operation
        '''
        self.log.debug('validate_config: name: %s config: %s'
                       % (device_mac, config))
        body = {'netElementId': device_mac, 'config': config}
        # Invoke the validate API call
        result = self.clnt.post('/configlet/validateConfig.do', data=body,
                                timeout=self.request_timeout)
        validated = True
        if 'warningCount' in result and result['warnings']:
            for warning in result['warnings']:
                self.log.warning('Validation of config produced warning - %s'
                                 % warning)
        if 'errorCount' in result:
            self.log.error('Validation of config produced %s errors'
                           % result['errorCount'])
            if 'errors' in result:
                for error in result['errors']:
                    self.log.error('Validation of config produced error - %s'
                                   % error)
            validated = False
        if 'result' in result:
            for item in result['result']:
                if 'messages' in item:
                    for message in item['messages']:
                        self.log.info('Validation of config returned'
                                      ' message - %s' % message)
        return validated

    def get_all_temp_actions(self, start=0, end=0):
        ''' Returns a list of existing temp actions.

            Args:
                start (int): Start index for the pagination. Default is 0.
                end (int): End index for the pagination. If end index is 0
                    then all the records will be returned. Default is 0.

            Returns:
                response (dict): A dict that contains a list of the current
                    temp actions.
        '''
        url = ('/provisioning/getAllTempActions.do?startIndex=%d&endIndex=%d'
               % (start, end))
        data = self.clnt.get(url, timeout=self.request_timeout)

        return data

    def _add_temp_action(self, data):
        ''' Adds temp action that requires a saveTopology call to take effect.

            Args:
                data (dict): a data dict with a specific format for the
                    desired action.

                    Base Ex: data = {'data': [{specific key/value pairs}]}
        '''
        url = ('/provisioning/addTempAction.do?'
               'format=topology&queryParam=&nodeId=root')
        self.clnt.post(url, data=data, timeout=self.request_timeout)

    def _save_topology_v2(self, data):
        ''' Confirms a previously created temp action.

            Args:
                data (list): a list that contains a dict with a specific
                    format for the desired action. Our primary use case is for
                    confirming existing temp actions so we most often send an
                    empty list to confirm an existing temp action.

            Returns:
                response (dict): A dict that contains a status and a list of
                    task ids created (if any).

                    Ex: {u'data': {u'status': u'success', u'taskIds': []}}
        '''
        url = '/provisioning/v2/saveTopology.do'
        return self.clnt.post(url, data=data, timeout=self.request_timeout)

    def apply_configlets_to_device(self, app_name, dev, new_configlets,
                                   create_task=True):
        ''' Apply the configlets to the device.

            Args:
                app_name (str): The application name to use in info field.
                dev (dict): The switch device dict
                new_configlets (list): List of configlet name and key pairs
                create_task (bool): Determines whether or not to execute a save
                    and create the tasks (if any)

            Returns:
                response (dict): A dict that contains a status and a list of
                    task ids created (if any).

                    Ex: {u'data': {u'status': u'success', u'taskIds': [u'32']}}
        '''
        self.log.debug('apply_configlets_to_device: dev: %s names: %s' %
                       (dev, new_configlets))
        # Get all the configlets assigned to the device.
        configlets = self.get_configlets_by_device_id(dev['systemMacAddress'])

        # Get a list of the names and keys of the configlets
        cnames = []
        ckeys = []
        for configlet in configlets:
            cnames.append(configlet['name'])
            ckeys.append(configlet['key'])

        # Add the new configlets to the end of the arrays
        for entry in new_configlets:
            cnames.append(entry['name'])
            ckeys.append(entry['key'])

        info = '%s: Configlet Assign: to Device %s' % (app_name, dev['fqdn'])
        info_preview = '<b>Configlet Assign:</b> to Device' + dev['fqdn']
        data = {'data': [{'info': info,
                          'infoPreview': info_preview,
                          'note': '',
                          'action': 'associate',
                          'nodeType': 'configlet',
                          'nodeId': '',
                          'configletList': ckeys,
                          'configletNamesList': cnames,
                          'ignoreConfigletNamesList': [],
                          'ignoreConfigletList': [],
                          'configletBuilderList': [],
                          'configletBuilderNamesList': [],
                          'ignoreConfigletBuilderList': [],
                          'ignoreConfigletBuilderNamesList': [],
                          'toId': dev['systemMacAddress'],
                          'toIdType': 'netelement',
                          'fromId': '',
                          'nodeName': '',
                          'fromName': '',
                          'toName': dev['fqdn'],
                          'nodeIpAddress': dev['ipAddress'],
                          'nodeTargetIpAddress': dev['ipAddress'],
                          'childTasks': [],
                          'parentTask': ''}]}
        self.log.debug('apply_configlets_to_device: saveTopology data:\n%s' %
                       data['data'])
        self._add_temp_action(data)
        if create_task:
            return self._save_topology_v2([])
        return None

    # pylint: disable=too-many-locals
    def remove_configlets_from_device(self, app_name, dev, del_configlets,
                                      create_task=True):
        ''' Remove the configlets from the device.

            Args:
                app_name (str): The application name to use in info field.
                dev (dict): The switch device dict
                del_configlets (list): List of configlet name and key pairs
                create_task (bool): Determines whether or not to execute a save
                    and create the tasks (if any)

            Returns:
                response (dict): A dict that contains a status and a list of
                    task ids created (if any).

                    Ex: {u'data': {u'status': u'success', u'taskIds': [u'35']}}
        '''
        self.log.debug('remove_configlets_from_device: dev: %s names: %s' %
                       (dev, del_configlets))

        # Get all the configlets assigned to the device.
        configlets = self.get_configlets_by_device_id(dev['systemMacAddress'])

        # Get a list of the names and keys of the configlets.  Do not add
        # configlets that are on the delete list.
        keep_names = []
        keep_keys = []
        for configlet in configlets:
            key = configlet['key']
            if next((ent for ent in del_configlets if ent['key'] == key),
                    None) is None:
                keep_names.append(configlet['name'])
                keep_keys.append(key)

        # Remove the names and keys of the configlets to keep and build a
        # list of the configlets to remove.
        del_names = []
        del_keys = []
        for entry in del_configlets:
            del_names.append(entry['name'])
            del_keys.append(entry['key'])

        info = '%s Configlet Remove: from Device %s' % (app_name, dev['fqdn'])
        info_preview = '<b>Configlet Remove:</b> from Device' + dev['fqdn']
        data = {'data': [{'info': info,
                          'infoPreview': info_preview,
                          'note': '',
                          'action': 'associate',
                          'nodeType': 'configlet',
                          'nodeId': '',
                          'configletList': keep_keys,
                          'configletNamesList': keep_names,
                          'ignoreConfigletNamesList': del_names,
                          'ignoreConfigletList': del_keys,
                          'configletBuilderList': [],
                          'configletBuilderNamesList': [],
                          'ignoreConfigletBuilderList': [],
                          'ignoreConfigletBuilderNamesList': [],
                          'toId': dev['systemMacAddress'],
                          'toIdType': 'netelement',
                          'fromId': '',
                          'nodeName': '',
                          'fromName': '',
                          'toName': dev['fqdn'],
                          'nodeIpAddress': dev['ipAddress'],
                          'nodeTargetIpAddress': dev['ipAddress'],
                          'childTasks': [],
                          'parentTask': ''}]}
        self.log.debug('remove_configlets_from_device: saveTopology data:\n%s'
                       % data['data'])
        self._add_temp_action(data)
        if create_task:
            return self._save_topology_v2([])
        return None

    def apply_configlets_to_container(self, app_name, container,
                                      new_configlets, create_task=True):
        ''' Apply the configlets to the container.

            Args:
                app_name (str): The application name to use in info field.
                container (dict): The container dict
                new_configlets (list): List of configlet name and key pairs
                create_task (bool): Determines whether or not to execute a save
                    and create the tasks (if any)

            Returns:
                response (dict): A dict that contains a status and a list of
                    task ids created (if any).

                    Ex: {u'data': {u'status': u'success', u'taskIds': [u'32']}}
        '''
        self.log.debug(
            'apply_configlets_to_container: container: %s names: %s' %
            (container, new_configlets))
        # Get all the configlets assigned to the device.
        configlets = self.get_configlets_by_container_id(container['key'])

        # Get a list of the names and keys of the configlets
        # Static Configlets
        cnames = []
        ckeys = []
        # ConfigletBuilder Configlets
        bnames = []
        bkeys = []
        if configlets['configletList']:
            for configlet in configlets['configletList']:
                if configlet['type'] == 'Static':
                    cnames.append(configlet['name'])
                    ckeys.append(configlet['key'])
                elif configlet['type'] == 'Builder':
                    bnames.append(configlet['name'])
                    bkeys.append(configlet['key'])

                    # Add the new configlets to the end of the arrays
        for entry in new_configlets:
            cnames.append(entry['name'])
            ckeys.append(entry['key'])

        info = '%s: Configlet Assign: to Container %s' % (app_name,
                                                          container['name'])
        info_preview = '<b>Configlet Assign:</b> to Container' + container[
            'name']
        data = {'data': [{'info': info,
                          'infoPreview': info_preview,
                          'note': '',
                          'action': 'associate',
                          'nodeType': 'configlet',
                          'nodeId': '',
                          'configletList': ckeys,
                          'configletNamesList': cnames,
                          'ignoreConfigletNamesList': [],
                          'ignoreConfigletList': [],
                          'configletBuilderList': bkeys,
                          'configletBuilderNamesList': bnames,
                          'ignoreConfigletBuilderList': [],
                          'ignoreConfigletBuilderNamesList': [],
                          'toId': container['key'],
                          'toIdType': 'container',
                          'fromId': '',
                          'nodeName': '',
                          'fromName': '',
                          'toName': container['name'],
                          'nodeIpAddress': '',
                          'nodeTargetIpAddress': '',
                          'childTasks': [],
                          'parentTask': ''}]}
        self.log.debug(
            'apply_configlets_to_container: saveTopology data:\n%s' %
            data['data'])
        self._add_temp_action(data)
        if create_task:
            return self._save_topology_v2([])
        return data

    # pylint: disable=too-many-locals
    # pylint: disable=invalid-name
    def remove_configlets_from_container(self, app_name, container,
                                         del_configlets, create_task=True):
        ''' Remove the configlets from the container.

            Args:
                app_name (str): The application name to use in info field.
                container (dict): The container dict
                del_configlets (list): List of configlet name and key pairs
                create_task (bool): Determines whether or not to execute a save
                    and create the tasks (if any)

            Returns:
                response (dict): A dict that contains a status and a list of
                    task ids created (if any).

                    Ex: {u'data': {u'status': u'success', u'taskIds': [u'35']}}
        '''
        self.log.debug(
            'remove_configlets_from_container: container: %s names: %s' %
            (container, del_configlets))

        # Get all the configlets assigned to the device.
        configlets = self.get_configlets_by_container_id(container['key'])

        # Get a list of the names and keys of the configlets.  Do not add
        # configlets that are on the delete list.
        keep_names = []
        keep_keys = []
        for configlet in configlets['configletList']:
            key = configlet['key']
            if next((ent for ent in del_configlets if ent['key'] == key),
                    None) is None:
                keep_names.append(configlet['name'])
                keep_keys.append(key)

        # Remove the names and keys of the configlets to keep and build a
        # list of the configlets to remove.
        del_names = []
        del_keys = []
        for entry in del_configlets:
            del_names.append(entry['name'])
            del_keys.append(entry['key'])

        info = '%s Configlet Remove: from Container %s' % (app_name,
                                                           container['name'])
        info_preview = '<b>Configlet Remove:</b> from Container' + container[
            'name']
        data = {'data': [{'info': info,
                          'infoPreview': info_preview,
                          'note': '',
                          'action': 'associate',
                          'nodeType': 'configlet',
                          'nodeId': '',
                          'configletList': keep_keys,
                          'configletNamesList': keep_names,
                          'ignoreConfigletNamesList': del_names,
                          'ignoreConfigletList': del_keys,
                          'configletBuilderList': [],
                          'configletBuilderNamesList': [],
                          'ignoreConfigletBuilderList': [],
                          'ignoreConfigletBuilderNamesList': [],
                          'toId': container['key'],
                          'toIdType': 'container',
                          'fromId': '',
                          'nodeName': '',
                          'fromName': '',
                          'toName': container['name'],
                          'nodeIpAddress': '',
                          'nodeTargetIpAddress': '',
                          'childTasks': [],
                          'parentTask': ''}]}
        self.log.debug(
            'remove_configlets_from_container: saveTopology data:\n%s'
            % data['data'])
        self._add_temp_action(data)
        if create_task:
            return self._save_topology_v2([])
        return data

    def validate_configlets_for_device(self, mac, configlet_keys,
                                       page_type='viewConfig'):
        ''' Validate and compare configlets for device.

            Args:
                mac (str): MAC address of device to validate configlets for.
                configlet_keys (list): List of configlet keys
                page_type (list): Possible Values of pageType - 'viewConfig',
                    'managementIPValidation', 'validateConfig', etc...

            Returns:
                response (dict): A dict that contains ...

                    Ex: {"reconciledConfig": {...},
                         "reconcile": 0,
                         "new": 0,
                         "designedConfig": [{...}],
                         "total": 0,
                         "runningConfig": [{...}],
                         "isReconcileInvoked": true,
                         "mismatch": 0,
                         "warnings": [""],
                         "errors": [{"configletLineNo": 0,
                                     "error": "string",
                                     "configletId": "string"}, ...]
                        }
        '''
        self.log.debug('validate_configlets_for_device: '
                       'MAC: %s - conf keys: %s - page_type: %s' %
                       (mac, configlet_keys, page_type))
        data = {'configIdList': configlet_keys,
                'netElementId': mac,
                'pageType': page_type}
        return self.clnt.post(
            '/provisioning/v2/validateAndCompareConfiglets.do',
            data=data, timeout=self.request_timeout)

    def get_applied_devices(self, configlet_name, start=0, end=0):
        ''' Returns a list of devices to which the named configlet is applied.

            Args:
                configlet_name (str): The name of the configlet to be queried.
                start (int): Start index for the pagination. Default is 0.
                end (int): End index for the pagination. If end index is 0
                    then all the records will be returned. Default is 0.
        '''
        return self.clnt.get('/configlet/getAppliedDevices.do?'
                             'configletName=%s&startIndex=%d&endIndex=%d'
                             % (configlet_name, start, end),
                             timeout=self.request_timeout)

    def get_applied_containers(self, configlet_name, start=0, end=0):
        ''' Returns a list of containers to which the named
            configlet is applied.

            Args:
                configlet_name (str): The name of the configlet to be queried.
                start (int): Start index for the pagination. Default is 0.
                end (int): End index for the pagination. If end index is 0
                    then all the records will be returned. Default is 0.
        '''
        return self.clnt.get('/configlet/getAppliedContainers.do?'
                             'configletName=%s&startIndex=%d&endIndex=%d'
                             % (configlet_name, start, end),
                             timeout=self.request_timeout)

    # pylint: disable=too-many-arguments
    def _container_op(self, container_name, container_key, parent_name,
                      parent_key, operation):
        ''' Perform the operation on the container.

            Args:
                container_name (str): Container name
                container_key (str): Container key, can be empty for add.
                parent_name (str): Parent container name
                parent_key (str): Parent container key
                operation (str): Container operation 'add' or 'delete'.

            Returns:
                response (dict): A dict that contains a status and a list of
                    task ids created (if any).

                    Ex: {u'data': {u'status': u'success', u'taskIds': []}}
        '''
        msg = ('%s container %s under container %s' %
               (operation, container_name, parent_name))
        data = {'data': [{'info': msg,
                          'infoPreview': msg,
                          'action': operation,
                          'nodeType': 'container',
                          'nodeId': container_key,
                          'toId': '',
                          'fromId': '',
                          'nodeName': container_name,
                          'fromName': '',
                          'toName': '',
                          'childTasks': [],
                          'parentTask': '',
                          'toIdType': 'container'}]}
        if operation == 'add':
            data['data'][0]['toId'] = parent_key
            data['data'][0]['toName'] = parent_name
        elif operation == 'delete':
            data['data'][0]['fromId'] = parent_key
            data['data'][0]['fromName'] = parent_name

        # Perform the container operation
        self._add_temp_action(data)
        return self._save_topology_v2([])

    def add_container(self, container_name, parent_name, parent_key):
        ''' Add the container to the specified parent.

            Args:
                container_name (str): Container name
                parent_name (str): Parent container name
                parent_key (str): Parent container key

            Returns:
                response (dict): A dict that contains a status and a list of
                    task ids created (if any).

                    Ex: {u'data': {u'status': u'success', u'taskIds': []}}
        '''
        self.log.debug('add_container: container: %s parent: %s parent_key: %s'
                       % (container_name, parent_name, parent_key))
        return self._container_op(container_name, 'new_container', parent_name,
                                  parent_key, 'add')

    def delete_container(self, container_name, container_key, parent_name,
                         parent_key):
        ''' Add the container to the specified parent.

            Args:
                container_name (str): Container name
                container_key (str): Container key
                parent_name (str): Parent container name
                parent_key (str): Parent container key

            Returns:
                response (dict): A dict that contains a status and a list of
                    task ids created (if any).

                    Ex: {u'data': {u'status': u'success', u'taskIds': []}}
        '''
        self.log.debug('delete_container: container: %s container_key: %s '
                       'parent: %s parent_key: %s' %
                       (container_name, container_key, parent_name,
                        parent_key))
        resp = self._container_op(container_name, container_key, parent_name,
                                  parent_key, 'delete')
        # As of CVP version 2020.1 the addTempAction.do API endpoint stopped
        # raising an Error when attempting to delete a container with children.
        # To account for this try to see if the container being deleted
        # still exists after the attempted delete. If it still exists
        # raise an error similar to how CVP behaved prior to CVP 2020.1
        try:
            still_exists = self.get_container_by_id(container_key)
        except CvpApiError as error:
            if 'Invalid Container id' in error.msg:
                return resp
            else:
                raise
        if still_exists is not None:
            raise CvpApiError('Container was not deleted. Check for children')
        return resp

    def get_parent_container_for_device(self, device_mac):
        ''' Add the container to the specified parent.

            Args:
                device_mac (str): Device mac address

            Returns:
                response (dict): A dict that contains the parent container info
        '''
        self.log.debug('get_parent_container_for_device: called for %s'
                       % device_mac)
        data = self.clnt.get('/provisioning/searchTopology.do?'
                             'queryParam=%s&startIndex=0&endIndex=0'
                             % device_mac, timeout=self.request_timeout)
        if data['total'] > 0:
            cont_name = data['netElementContainerList'][0]['containerName']
            return self.get_container_by_name(cont_name)
        return None

    def move_device_to_container(self, app_name, device, container,
                                 create_task=True):
        ''' Add the container to the specified parent.

            Args:
                app_name (str): String to specify info/signifier of calling app
                device (dict): Device info
                container (dict): Container info
                create_task (bool): Determines whether or not to execute a save
                    and create the tasks (if any)

            Returns:
                response (dict): A dict that contains a status and a list of
                    task ids created (if any).

                    Ex: {u'data': {u'status': u'success', u'taskIds': []}}
        '''
        info = 'Device Add {} to container {} by {}'.format(device['fqdn'],
                                                            container['name'],
                                                            app_name)
        self.log.debug('Attempting to move device %s to container %s'
                       % (device['fqdn'], container['name']))
        if 'parentContainerId' in device:
            from_id = device['parentContainerId']
        else:
            parent_cont = self.get_parent_container_for_device(device['key'])
            from_id = parent_cont['key']
        data = {'data': [{'info': info,
                          'infoPreview': info,
                          'action': 'update',
                          'nodeType': 'netelement',
                          'nodeId': device['key'],
                          'toId': container['key'],
                          'fromId': from_id,
                          'nodeName': device['fqdn'],
                          'toName': container['name'],
                          'toIdType': 'container',
                          'childTasks': [],
                          'parentTask': ''}]}
        try:
            self._add_temp_action(data)
        # pylint: disable=invalid-name
        except CvpApiError as e:
            if 'Data already exists' in str(e):
                self.log.debug('Device %s already in container %s'
                               % (device['fqdn'], container))
        if create_task:
            return self._save_topology_v2([])
        return None

    def search_topology(self, query, start=0, end=0):
        ''' Search the topology for items matching the query parameter.

            Args:
                query (str): Query parameter which is the name of the container
                    or device.
                start (int): Start index for the pagination.  Default is 0.
                end (int): End index for the pagination.  If end index is 0
                    then all the records will be returned.  Default is 0.

            Returns:
                response (dict): A dict that contains the container and
                    netelement lists.
        '''
        self.log.debug('search_topology: query: %s start: %d end: %d' %
                       (query, start, end))
        data = self.clnt.get('/provisioning/searchTopology.do?queryParam=%s&'
                             'startIndex=%d&endIndex=%d'
                             % (qplus(query), start, end),
                             timeout=self.request_timeout)
        if 'netElementList' in data:
            for device in data['netElementList']:
                device['status'] = device['deviceStatus']
                device['mlagEnabled'] = device['isMLAGEnabled']
                device['danzEnabled'] = device['isDANZEnabled']
                device['parentContainerKey'] = device['parentContainerId']
                device['bootupTimestamp'] = device['bootupTimeStamp']
                device['internalBuild'] = device['internalBuildId']
        return data

    def filter_topology(self, node_id='root', fmt='topology',
                        start=0, end=0):
        ''' Filter the CVP topology for container and device information.

            Args:
                node_id (str): The container key to base the filter in.
                    Default is 'root', for the Tenant container.
                fmt (str): The type of filter to return. Must be either
                    'topology' or 'list'. Default is 'topology'.
                start (int): Start index for the pagination. Default is 0.
                end (int): End index for the pagination. If end index is 0
                    then all the records will be returned. Default is 0.
        '''
        url = ('/provisioning/filterTopology.do?nodeId=%s&'
               'format=%s&startIndex=%d&endIndex=%d'
               % (node_id, fmt, start, end))
        return self.clnt.get(url, timeout=self.request_timeout)

    def check_compliance(self, node_key, node_type):
        ''' Check that a device is in compliance, that is the configlets
            applied to the device match the devices running configuration.

            Args:
                node_key (str): The device key. This is the device MAC address
                    Example: ff:ff:ff:ff:ff:ff
                node_type (str): The device type. This is either 'netelement'
                    or 'container'

            Returns:
                response (dict): A dict that contains the results of the
                    compliance check.
        '''
        self.log.debug('check_compliance: node_key: %s node_type: %s' %
                       (node_key, node_type))
        data = {'nodeId': node_key, 'nodeType': node_type}
        resp = self.clnt.post('/provisioning/checkCompliance.do', data=data,
                              timeout=self.request_timeout)
        if self.clnt.apiversion is None:
            self.get_cvp_info()
        if self.clnt.apiversion >= 2.0:
            if resp['complianceIndication'] == u'':
                resp['complianceIndication'] = 'NONE'
        return resp

    def get_event_by_id(self, e_id):
        ''' Return information on the requested event ID.

            Args:
                e_id (str): The event id to be queried.
        '''
        return self.clnt.get('/event/getEventById.do?eventId=%s' % e_id,
                             timeout=self.request_timeout)

    def get_default_snapshot_template(self):
        ''' Return the default snapshot template.

        '''
        if self.clnt.apiversion is None:
            self.get_cvp_info()
        if self.clnt.apiversion == 1.0:
            self.log.debug('v1 Inventory API Call')
            url = ('/snapshot/getDefaultSnapshotTemplate.do?'
                   'startIndex=0&endIndex=0')
            return self.clnt.get(url, timeout=self.request_timeout)
        self.log.debug('v2 Inventory API Call')
        self.log.debug('API getDefaultSnapshotTemplate.do'
                       ' deprecated for CVP 2018.2 and beyond')
        return None

    # pylint: disable=invalid-name
    def capture_container_level_snapshot(self, template_key, container_key):
        ''' Initialize a container level snapshot event.

            Args:
                template_key (str): The snapshot template key to be used for
                    the snapshots.
                container_key (str): The container key to start the
                    snapshots on.
        '''
        if self.clnt.apiversion is None:
            self.get_cvp_info()
        if self.clnt.apiversion == 1.0:
            self.log.debug('v1 Inventory API Call')
            data = {
                'templateId': template_key,
                'containerId': container_key,
            }
            return self.clnt.post('/snapshot/captureContainerLevelSnapshot.do',
                                  data=data, timeout=self.request_timeout)
        self.log.debug('v2 Inventory API Call')
        self.log.debug('API captureContainerLevelSnapshot.do'
                       ' deprecated for CVP 2018.2 and beyond')
        return None

    def add_image(self, filepath):
        ''' Add an image to a CVP cluster.

            Args:
                filepath (str): Local path to the image to upload.

            Returns:
                data (dict): Dictionary of image add data.
        '''
        # Get the absolute file path to be uploaded
        image_path = os.path.abspath(filepath)
        image_data = open(image_path, 'rb')
        response = self.clnt.post('/image/addImage.do',
                                  files={'file': image_data})
        return response

    def cancel_image(self, image_name):
        ''' Discard/cancel the uploaded image/image bundle before save.

            Args:
                image_name (string): Name of image to cancel/discard.

            Returns:
                data (dict): Success or error message.
        '''
        image_data = {'data': image_name}
        return self.clnt.post('/image/cancelImages.do', data=image_data,
                              timeout=self.request_timeout)

    def get_images(self, start=0, end=0):
        ''' Return a list of all images.

            Args:
                start (int): Start index for the pagination.  Default is 0.
                end (int): End index for the pagination.  If end index is 0
                    then all the records will be returned.  Default is 0.

            Returns:
                images (dict): The 'total' key contains the number of images,
                    the 'data' key contains a list of images and their info.
        '''
        self.log.debug('Get info about images')
        return self.clnt.get('/image/getImages.do?queryparam=&startIndex=%d&'
                             'endIndex=%d' % (start, end),
                             timeout=self.request_timeout)

    def get_image_bundles(self, start=0, end=0):
        ''' Return a list of all image bundles.

            Args:
                start (int): Start index for the pagination.  Default is 0.
                end (int): End index for the pagination.  If end index is 0
                    then all the records will be returned.  Default is 0.

            Returns:
                image bundles (dict): The 'total' key contains the number of
                    image bundles, the 'data' key contains a list of image
                    bundles and their info.
        '''
        self.log.debug('Get image bundles that can be applied to devices or'
                       ' containers')
        return self.clnt.get('/image/getImageBundles.do?queryparam=&'
                             'startIndex=%d&endIndex=%d' % (start, end),
                             timeout=self.request_timeout)

    def get_image_bundle_by_name(self, name):
        ''' Return a dict of info about an image bundle.

            Args:
                name (str): Name of image bundle to return info about.

            Returns:
                image bundle (dict): Dict of info specific to the image bundle
                    requested or None if the name requested doesn't exist.
        '''
        self.log.debug('Attempt to get image bundle %s' % name)
        try:
            image = self.clnt.get('/image/getImageBundleByName.do?name=%s'
                                  % qplus(name), timeout=self.request_timeout)
        except CvpApiError as error:
            # Catch an invalid task_id error and return None
            if 'Entity does not exist' in str(error):
                self.log.debug('Bundle with name %s does not exist' % name)
                return None
            raise error
        return image

    def delete_image_bundle(self, image_key, image_name):
        ''' Delete image bundle

            Args:
                image_key (str): The key of the image bundle to be deleted.
                image_name (str): The name of the image bundle to be deleted.
        '''
        bundle_data = {
            'data': [{'key': image_key,
                      'name': image_name}]
        }
        return self.clnt.post('/image/deleteImageBundles.do', data=bundle_data,
                              timeout=self.request_timeout)

    def save_image_bundle(self, name, images, certified=True):
        ''' Save an image bundle to a cluster.

            Args:
                name (str): The name of the image bundle to be saved.
                images (list): A list of image names to include in the bundle.
                certified (bool): Whether the image bundle is certified or
                    not. Default is True.
        '''
        certified_image = 'true' if certified else 'false'
        data = {
            'name': name,
            'isCertifiedImage': certified_image,
            'images': images,
        }
        return self.clnt.post('/image/saveImageBundle.do', data=data,
                              timeout=self.request_timeout)

    def update_image_bundle(self, bundle_id, name, images, certified=True):
        ''' Update an existing image bundle
        '''
        certified_image = 'true' if certified else 'false'
        data = {
            'id': bundle_id,
            'name': name,
            'isCertifiedImage': certified_image,
            'images': images,
        }
        return self.clnt.post('/image/updateImageBundle.do', data=data,
                              timeout=self.request_timeout)

    def apply_image_to_device(self, image, device, create_task=True):
        ''' Apply an image bundle to a device

            Args:
                image (dict): The image info.
                device (dict): Info about device to apply image to.
                create_task (bool): Determines whether or not to execute a save
                    and create the tasks (if any)

            Returns:
                response (dict): A dict that contains a status and a list of
                    task ids created (if any). Image updates will not run until
                    task or tasks are executed.

                    Ex: {u'data': {u'status': u'success', u'taskIds': [u'32']}}
        '''
        return self.apply_image_to_element(image, device, device['fqdn'],
                                           'netelement', create_task)

    def apply_image_to_container(self, image, container, create_task=True):
        ''' Apply an image bundle to a container

            Args:
                image (dict): The image info.
                container (dict): Info about container to apply image to.
                create_task (bool): Determines whether or not to execute a save
                    and create the tasks (if any)

            Returns:
                response (dict): A dict that contains a status and a list of
                    task ids created (if any). Image updates will not run until
                    task or tasks are executed.

                    Ex: {u'data': {u'status': u'success', u'taskIds': [u'32']}}
        '''
        return self.apply_image_to_element(image, container, container['name'],
                                           'container', create_task)

    def apply_image_to_element(self, image, element, name, id_type,
                               create_task=True):
        ''' Apply an image bundle to a device or container.

            Args:
                image (dict): The image info.
                element (dict): Info about element to apply image to. Dict
                    can contain device info or container info.
                name (str): Name of element image is being applied to.
                id_type (str): Id type of element image is being applied to.
                create_task (bool): Determines whether or not to execute a save
                    and create the tasks (if any)

            Returns:
                response (dict): A dict that contains a status and a list of
                    task ids created (if any). Image updates will not run until
                    task or tasks are executed.

                    Ex: {u'data': {u'status': u'success', u'taskIds': [u'32']}}
        '''
        self.log.debug('Attempt to apply %s to %s %s' % (image['name'],
                                                         id_type, name))
        info = 'Apply image: %s to %s %s' % (image['name'], id_type, name)
        node_id = ''
        if 'imageBundleKeys' in image:
            if image['imageBundleKeys']:
                node_id = image['imageBundleKeys'][0]
            self.log.info('Provided image is an image object.'
                          ' Using first value from imageBundleKeys - %s'
                          % node_id)
        if 'id' in image:
            node_id = image['id']
            self.log.info('Provided image is an image bundle object.'
                          ' Found v1 API id field - %s' % node_id)
        elif 'key' in image:
            node_id = image['key']
            self.log.info('Provided image is an image bundle object.'
                          ' Found v2 API key field - %s' % node_id)
        data = {'data': [{'info': info,
                          'infoPreview': info,
                          'note': '',
                          'action': 'associate',
                          'nodeType': 'imagebundle',
                          'nodeId': node_id,
                          'toId': element['key'],
                          'toIdType': id_type,
                          'fromId': '',
                          'nodeName': image['name'],
                          'fromName': '',
                          'toName': name,
                          'childTasks': [],
                          'parentTask': ''}]}
        self._add_temp_action(data)
        if create_task:
            return self._save_topology_v2([])
        return None

    def remove_image_from_device(self, image, device):
        ''' Remove the image bundle from the specified device.

            Args:
                image (dict): The image info.
                device (dict): The device info.

            Returns:
                response (dict): A dict that contains a status and a list of
                    task ids created (if any).

                    Ex: {u'data': {u'status': u'success', u'taskIds': [u'32']}}
        '''
        return self.remove_image_from_element(image, device, device['fqdn'],
                                              'netelement')

    def remove_image_from_container(self, image, container):
        ''' Remove the image bundle from the specified container.

            Args:
                image (dict): The image info.
                container (dict): The container info.

            Returns:
                response (dict): A dict that contains a status and a list of
                    task ids created (if any).

                    Ex: {u'data': {u'status': u'success', u'taskIds': [u'32']}}
        '''
        return self.remove_image_from_element(image, container,
                                              container['name'], 'container')

    def remove_image_from_element(self, image, element, name, id_type):
        ''' Remove the image bundle from the specified container.

            Args:
                image (dict): The image info.
                element (dict): The container info.
                name (): name.
                id_type (): type.

            Returns:
                response (dict): A dict that contains a status and a list of
                    task ids created (if any).

                    Ex: {u'data': {u'status': u'success', u'taskIds': [u'32']}}
        '''
        self.log.debug('Attempt to remove %s from %s' % (image['name'], name))
        info = 'Remove image: %s from %s' % (image['name'], name)
        node_id = ''
        if 'imageBundleKeys' in image:
            if image['imageBundleKeys']:
                node_id = image['imageBundleKeys'][0]
            self.log.info('Provided image is an image object.'
                          ' Using first value from imageBundleKeys - %s'
                          % node_id)
        if 'id' in image:
            node_id = image['id']
            self.log.info('Provided image is an image bundle object.'
                          ' Found v1 API id field - %s' % node_id)
        elif 'key' in image:
            node_id = image['key']
            self.log.info('Provided image is an image bundle object.'
                          ' Found v2 API key field - %s' % node_id)
        data = {'data': [{'info': info,
                          'infoPreview': info,
                          'note': '',
                          'action': 'associate',
                          'nodeType': 'imagebundle',
                          'nodeId': '',
                          'toId': element['key'],
                          'toIdType': id_type,
                          'fromId': '',
                          'nodeName': '',
                          'fromName': '',
                          'toName': name,
                          'ignoreNodeId': node_id,
                          'ignoreNodeName': image['name'],
                          'childTasks': [],
                          'parentTask': ''}]}
        self._add_temp_action(data)
        return self._save_topology_v2([])

    def get_change_controls(self, query='', start=0, end=0):
        ''' Returns a list of change controls.

            Args:
                query (str): Query to look for in change control names
                start (int): Start index for the pagination.  Default is 0.
                end (int): End index for the pagination.  If end index is 0
                    then all the records will be returned.  Default is 0.

            Returns:
                change controls (list): The list of change controls
        '''
        self.log.debug('get_change_controls: query: %s' % query)
        if self.clnt.apiversion is None:
            self.get_cvp_info()
        if self.clnt.apiversion >= 3.0:
            self.log.debug('v3/v4/v5 getChangeControls API Call')
            self.log.warning(
                'get_change_controls: change control APIs moved for v3/v4/v5')
            return None

        self.log.debug('v2 getChangeControls API Call')
        data = self.clnt.get(
            '/changeControl/getChangeControls.do?searchText=%s'
            '&startIndex=%d&endIndex=%d' % (qplus(query), start, end),
            timeout=self.request_timeout)
        if 'data' not in data:
            return None
        return data['data']

    def change_control_available_tasks(self, query='', start=0, end=0):
        ''' Returns a list of tasks that are available for a change control.

            Args:
                query (str): Query to look for in task
                start (int): Start index for the pagination.  Default is 0.
                end (int): End index for the pagination.  If end index is 0
                    then all the records will be returned.  Default is 0.

            Returns:
                tasks (list): The list of available tasks
        '''
        self.log.debug('change_control_available_tasks: query: %s' % query)
        if self.clnt.apiversion is None:
            self.get_cvp_info()
        if self.clnt.apiversion >= 3.0:
            self.log.debug(
                'v3/v4/v5 uses existing get_task_by_status API Call')
            return self.get_tasks_by_status('PENDING')

        self.log.debug('v2 getTasksByStatus API Call')
        data = self.clnt.get(
            '/changeControl/getTasksByStatus.do?searchText=%s'
            '&startIndex=%d&endIndex=%d' % (qplus(query), start, end),
            timeout=self.request_timeout)
        if 'data' not in data:
            return None
        return data['data']

    def create_change_control(self, name, change_control_tasks, timezone,
                              country_id, date_time, snapshot_template_key='',
                              change_control_type='Custom',
                              stop_on_error='false'):
        ''' Create change control with provided information and return
            change control ID.

            Args:
                name (string): The name for the new change control.
                change_control_tasks (list): A list of key value pairs where
                    the key is the Task ID and the value is the task order
                    as an integer.
                    Ex: [{'taskId': '100', 'taskOrder': 1},
                         {'taskId': '101', 'taskOrder': 1},
                         {'taskId': '102', 'taskOrder': 2}]
                timezone (string): The timezone as a string.
                    Ex: "America/New_York"
                country_id (string): The country ID.
                    Ex: "United States"
                date_time (string): The date and time for execution.
                    Time is military time format.
                    Ex: "2018-08-22 11:30"
                snapshot_template_key (string): ???
                change_control_type (string): The type of change control being
                    created. Options are "Custom" or "Rollback".
                stop_on_error (string): String representation of a boolean
                    to set whether this change control will stop if an error is
                    encountered in one of its tasks.

            Returns:
                response (dict): A dict that contains...

                Ex: {"data": "success", "ccId": "4"}
        '''
        self.log.debug('create_change_control')
        # {
        #  "timeZone": "America/New_York",
        #  "countryId": "United States",
        #  "dateTime": "2018-08-22 11:30",
        #  "ccName": "test2",
        #  "snapshotTemplateKey": "",
        #  "type": "Custom",
        #  "stopOnError": "false",
        #  "deletedTaskIds": [],
        #  "changeControlTasks": [
        #    {
        #      "taskId": "126",
        #      "taskOrder": 1,
        #      "snapshotTemplateKey": "",
        #      "clonedCcId": ""
        #    }
        #  ]
        # }
        if self.clnt.apiversion is None:
            self.get_cvp_info()
        if self.clnt.apiversion >= 3.0:
            self.log.debug('v3/v4/v5 addOrUpdateChangeControl API Call')
            self.log.warning('create_change_control:'
                             ' change control APIs moved for v3/v4/v5')
            return None

        self.log.debug('v2 addOrUpdateChangeControl API Call')
        task_data_list = []
        for task_info in change_control_tasks:
            task_list_entry = {'taskId': task_info['taskId'],
                               'taskOrder': task_info['taskOrder'],
                               'snapshotTemplateKey': snapshot_template_key,
                               'clonedCcId': ''}
            task_data_list.append(task_list_entry)
        data = {'timeZone': timezone,
                'countryId': country_id,
                'dateTime': date_time,
                'ccName': name,
                'snapshotTemplateKey': snapshot_template_key,
                'type': change_control_type,
                'stopOnError': stop_on_error,
                'deletedTaskIds': [],
                'changeControlTasks': task_data_list}
        return self.clnt.post('/changeControl/addOrUpdateChangeControl.do',
                              data=data, timeout=self.request_timeout)

    def create_change_control_v3(self, cc_id, name, tasks):
        ''' Create change control with provided information and return
            change control ID.

            Args:
                cc_id (string): The ID for the new change control.
                name (string): The name for the new change control.
                tasks (list): A list of Task IDs as strings
                    Ex: ['10', '11', '12']

            Returns:
                response (dict): A dict that contains...

                Ex: [{u'id': u'cc_id',
                      u'update_timestamp': u'...'}]
        '''
        self.log.debug('create_change_control_v3')
        if self.clnt.apiversion is None:
            self.get_cvp_info()
        if self.clnt.apiversion < 3.0:
            self.log.debug('Wrong method for API version %s.'
                           ' Use create_change_control method',
                           self.clnt.apiversion)
            self.log.warning('create_change_control_v3:'
                             ' Use old change control APIs for old versions')
            return None

        self.log.debug('v3 Update change control API Call')
        stages = []
        for index, task in enumerate(tasks):
            stage_id = 'stage%d' % index
            stage = {'stage': [{
                'id': stage_id,
                'action': {
                    'name': 'task',
                    'args': {
                        'TaskID': task,
                    }
                }
            }]}
            stages.append(stage)
        data = {'config': {
            'id': cc_id,
            'name': name,
            'root_stage': {
                'id': 'root',
                'stage_row': stages,
            }
        }}
        return self.clnt.post('/api/v3/services/ccapi.ChangeControl/Update',
                              data=data, timeout=self.request_timeout)

    def add_notes_to_change_control(self, cc_id, notes):
        ''' Add provided notes to the specified change control.

            Args:
                cc_id (string): The id for the change control to add notes to.
                notes (string): The notes to add to the change control.

            Returns:
                response (dict): A dict that contains...

                Ex: {"data": "success"}
        '''
        self.log.debug('add_notes_to_change_control: cc_id %s, notes %s'
                       % (cc_id, notes))
        if self.clnt.apiversion is None:
            self.get_cvp_info()
        if self.clnt.apiversion >= 3.0:
            self.log.debug(
                'v3/v4/v5 addNotesToChangeControl API Call deprecated')
            self.log.warning('add_notes_to_change_control:'
                             ' change control APIs not supported for v3/v4/v5')
            return None

        self.log.debug('v2 addNotesToChangeControl API Call')
        data = {'ccId': cc_id,
                'notes': notes}
        return self.clnt.post('/changeControl/addNotesToChangeControl.do',
                              data=data, timeout=self.request_timeout)

    def execute_change_controls(self, cc_ids):
        ''' Execute the change control indicated by its ccId.

            Args:
                cc_ids (list): A list of change control IDs to be executed.
        '''
        if self.clnt.apiversion is None:
            self.get_cvp_info()
        if self.clnt.apiversion >= 3.0:
            self.log.debug(
                'v3/v4/v5 /api/v3/services/ccapi.ChangeControl/Start API Call')
            for cc_id in cc_ids:
                resp_list = []
                data = {'cc_id': cc_id}
                resp = self.clnt.post(
                    '/api/v3/services/ccapi.ChangeControl/Start',
                    data=data, timeout=self.request_timeout)
                resp_list.append(resp)
            return resp_list

        self.log.debug('v2 executeCC API Call')
        cc_id_list = [{'ccId': x} for x in cc_ids]
        data = {'ccIds': cc_id_list}
        return self.clnt.post('/changeControl/executeCC.do', data=data,
                              timeout=self.request_timeout)

    def approve_change_control(self, cc_id,
                               timestamp=datetime.utcnow().isoformat() + 'Z'):
        ''' Cancel the provided change controls.

            Args:
                cc_id (string): The change control IDs to be approved.
                timestamp(string): The change controls timestamp.
        '''
        self.log.debug('approve_change_control')
        if self.clnt.apiversion is None:
            self.get_cvp_info()
        if self.clnt.apiversion < 3.0:
            self.log.debug('Approval methods not valid for API version %s.'
                           ' Functionality did not exist',
                           self.clnt.apiversion)
            return None

        self.log.debug('v3 Approve change control API Call')
        data = {'cc_id': cc_id, 'cc_timestamp': timestamp}
        return self.clnt.post(
            '/api/v3/services/ccapi.ChangeControl/AddApproval',
            data=data, timeout=self.request_timeout)

    def delete_change_control_approval(self, cc_id):
        ''' Cancel the provided change controls.

            Args:
                cc_id (string): The change control IDs to be approved.
        '''
        self.log.debug('delete_change_control_approval')
        if self.clnt.apiversion is None:
            self.get_cvp_info()
        if self.clnt.apiversion < 3.0:
            self.log.debug('Approval methods not valid for API version %s.'
                           ' Functionality did not exist',
                           self.clnt.apiversion)
            return None

        self.log.debug('v3 Delete Approval for change control API Call')
        data = {'cc_id': cc_id}
        return self.clnt.post(
            '/api/v3/services/ccapi.ChangeControl/DeleteApproval',
            data=data, timeout=self.request_timeout)

    def cancel_change_controls(self, cc_ids):
        ''' Cancel the provided change controls.

            Args:
                cc_ids (list): A list of change control IDs to be cancelled.
        '''
        if self.clnt.apiversion is None:
            self.get_cvp_info()
        if self.clnt.apiversion >= 3.0:
            self.log.debug(
                'v3/v4/v5 /api/v3/services/ccapi.ChangeControl/Stop API Call')
            resp_list = []
            for cc_id in cc_ids:
                data = {'cc_id': cc_id}
                resp = self.clnt.post(
                    '/api/v3/services/ccapi.ChangeControl/Stop',
                    data=data, timeout=self.request_timeout)
                resp_list.append(resp)
            return resp_list

        self.log.debug('v2 cancelChangeControl API Call')
        data = {'ccIds': cc_ids}
        return self.clnt.post('/changeControl/cancelChangeControl.do',
                              data=data, timeout=self.request_timeout)

    def delete_change_controls(self, cc_ids):
        ''' Delete the provided change controls.

            Args:
                cc_ids (list): A list of change control IDs to be deleted.
        '''
        if self.clnt.apiversion is None:
            self.get_cvp_info()
        if self.clnt.apiversion >= 3.0:
            self.log.debug('v3/v4/v5 /api/v3/services/'
                           'ccapi.ChangeControl/Delete API Call')
            for cc_id in cc_ids:
                resp_list = []
                data = {'cc_id': cc_id}
                resp = self.clnt.post(
                    '/api/v3/services/ccapi.ChangeControl/Delete',
                    data=data, timeout=self.request_timeout)
                resp_list.append(resp)
            return resp_list

        self.log.debug('v2 deleteChangeControl API Call')
        data = {'ccIds': cc_ids}
        return self.clnt.post('/changeControl/deleteChangeControls.do',
                              data=data, timeout=self.request_timeout)

    def get_change_control_info(self, cc_id):
        ''' Get the detailed information for a single change control.

            Args:
                cc_id (string): The id for the change control to be retrieved.

            Returns:
                response (dict): A dict that contains...

                Ex: {'ccId': '4',
                     'ccName': 'test_api_1541106830',
                     'changeControlTasks': {'data': [<task data>],
                                             'total': 1},
                     'classId': 68,
                     'containerName': '',
                     'countryId': '',
                     'createdBy': 'cvpadmin',
                     'createdTimestamp': 1541106831629,
                     'dateTime': '',
                     'deviceCount': 1,
                     'executedBy': 'cvpadmin',
                     'executedTimestamp': 1541106831927,
                     'factoryId': 1,
                     'id': 68,
                     'key': '4',
                     'notes': '',
                     'postSnapshotEndTime': 0,
                     'postSnapshotStartTime': 0,
                     'preSnapshotEndTime': 0,
                     'preSnapshotStartTime': 0,
                     'progressStatus': {<status>},
                     'scheduledBy': '',
                     'scheduledByPassword': '',
                     'scheduledTimestamp': 0,
                     'snapshotTemplateKey': '',
                     'snapshotTemplateName': None,
                     'status': 'Inprogress',
                     'stopOnError': False,
                     'taskCount': 1,
                     'taskEndTime': 0,
                     'taskStartTime': 0,
                     'timeZone': '',
                     'type': 'Custom'}
        '''
        self.log.debug('get_change_control_info: %s', cc_id)
        if self.clnt.apiversion is None:
            self.get_cvp_info()
        if self.clnt.apiversion >= 3.0:
            self.log.debug('get_change_control_info method deprecated for'
                           ' v3/v4/v5. Moved to get_change_control_status')
            self.log.warning('get_change_control_info:'
                             ' info change control API moved for v3/v4/v5 to'
                             ' status')
            return None

        self.log.debug('v2 getChangeControlInformation.do API Call')
        try:
            resp = self.clnt.get(
                '/changeControl/getChangeControlInformation.do?'
                'startIndex=0&endIndex=0&ccId=%s' % cc_id,
                timeout=self.request_timeout)
        except CvpApiError as error:
            if 'No data found' in error.msg:
                return None
            raise
        return resp

    def get_change_control_status(self, cc_id):
        ''' Get the detailed information for a single change control.

            Args:
                cc_id (string): The id for the change control to be retrieved.

            Returns:
                response (dict): A dict that contains...

                Ex:
                [{u'status': {u'error': u'',
                              u'id': u'cc_id',
                              u'stages': {u' ': {
                                              u'error': u'',
                                              u'state': u'Completed'},
                                          u'Task_0_1': {
                                              u'error': u'',
                                              u'state': u'Completed'}
                                         },
                              u'state': u'Completed'}}]
        '''
        self.log.debug('get_change_control_status: %s', cc_id)
        if self.clnt.apiversion is None:
            self.get_cvp_info()
        if self.clnt.apiversion < 3.0:
            self.log.debug('get_change_control_status method not supported'
                           ' for API version %s. Use old'
                           ' get_change_control_info method'
                           % self.clnt.apiversion)
            return None

        self.log.debug(
            'v3 /api/v3/services/ccapi.ChangeControl/GetStatus API Call')
        data = {'cc_id': cc_id}
        return self.clnt.post(
            '/api/v3/services/ccapi.ChangeControl/GetStatus',
            data=data, timeout=self.request_timeout)

    def reset_device(self, app_name, device, create_task=True):
        ''' Reset device by moving it to the Undefined Container.

            Args:
                app_name (str): String to specify info/signifier of calling app
                device (dict): Device info
                container (dict): Container info
                create_task (bool): Determines whether or not to execute a save
                    and create the tasks (if any)

            Returns:
                response (dict): A dict that contains a status and a list of
                    task ids created (if any).

                    Ex: {u'data': {u'status': u'success', u'taskIds': []}}
        '''
        info = ('App %s reseting device %s and moving it to Undefined'
                % (app_name, device['fqdn']))
        self.log.debug(info)
        if 'parentContainerId' in device:
            from_id = device['parentContainerId']
        else:
            parent_cont = self.get_parent_container_for_device(device['key'])
            from_id = parent_cont['key']
        data = {'data': [{'info': info,
                          'infoPreview': info,
                          'action': 'reset',
                          'nodeType': 'netelement',
                          'nodeId': device['key'],
                          'toId': 'undefined_container',
                          'fromId': from_id,
                          'nodeName': device['fqdn'],
                          'toName': 'Undefined',
                          'toIdType': 'container',
                          'childTasks': [],
                          'parentTask': ''}]}
        try:
            self._add_temp_action(data)
        except CvpApiError as error:
            if 'Data already exists' in str(error):
                self.log.debug('Device %s already in container Undefined'
                               % device['fqdn'])
        if create_task:
            return self._save_topology_v2([])
        return None

    def deploy_device(self, device, container, configlets=None,
                      image_bundle=None, create_task=True,
                      app_name='Deploy_device'):
        ''' Move a device from the undefined container to a target container.
            Optionally apply device-specific configlets and an image.

            Args:
                device (dict): unique key for the device
                container (str): name of container to move device to
                configlets (list): list of dicts with configlet key/name pairs
                image_bundle (str): name of image bundle to apply to device
                create_task (boolean): Create task for this deploy device
                    sequence.
                app_name (str): calling application name for logging purposes

            Returns:
                response (dict): A dict that contains a status and a list of
                    task ids created (if any).

                    Ex: {u'data': {u'status': u'success', u'taskIds': [u'32']}}
        '''
        info = 'Deploy device %s to container %s' % (device['fqdn'], container)
        self.log.debug(info)
        container_info = self.get_container_by_name(container)
        # Add action for moving device to specified container
        self.move_device_to_container(app_name, device, container_info,
                                      create_task=False)

        # Get proposed configlets device will inherit from container it is
        # being moved to.
        prop_conf = self.clnt.get('/provisioning/getTempConfigsByNetElementId.'
                                  'do?netElementId=%s' % device['key'])
        new_configlets = prop_conf['proposedConfiglets']
        if configlets:
            new_configlets.extend(configlets)
        self.apply_configlets_to_device('deploy_device', device,
                                        new_configlets, create_task=False)
        # Apply image to the device
        if image_bundle:
            image_bundle_info = self.get_image_bundle_by_name(image_bundle)
            self.apply_image_to_device(image_bundle_info, device,
                                       create_task=False)
        if create_task:
            return self._save_topology_v2([])
        return None

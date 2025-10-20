# pylint: disable=fixme,too-many-locals,redefined-builtin
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
import operator
import os
import time
# This import is for proper file IO handling support for both Python 2 and 3
from io import open
from datetime import datetime
from re import split

from cvprac.cvp_client_errors import CvpApiError, CvpRequestError

try:
    from urllib import quote_plus as qplus
except (AttributeError, ImportError):
    from urllib.parse import quote_plus as qplus

OPERATOR_DICT = {
    '>': operator.gt,
    '<': operator.lt,
    '>=': operator.ge,
    '<=': operator.le,
    '==': operator.eq
}


def sanitize_warnings(data):
    ''' Sanitize the warnings returned after validation.

        In some cases where the configlets have both errors
        and warnings, CVP may split warnings that have
        `,` across multiple strings.
        This method concatenates the strings back into one string
        per warning, and corrects the warningCount.

        Args:
            data (dict): A dict that contians the result
                of the validation operation
        Returns:
            response (dict): A dict that contains the result of the
                validation operation
    '''
    if "warnings" not in data:
        # nothing to do here, we can return as is
        return data
    # Since there may be warnings incorrectly split on
    # ', ' within the warning text by CVP, we join all the
    # warnings together using ', ' into one large string
    temp_warnings = ", ".join(data['warnings']).strip()

    # To split the large string again we match on the
    # 'at line XXX' that should indicate the end of the warning.
    # We capture as well the remaining \\n or whitespace and include
    # the extra ', ' added in the previous step in the matching criteria.
    # The extra ', ' is not included in the strings of the new list
    temp_warnings = split(
        r'(.*?at line \d+.*?),\s+',
        temp_warnings
    )

    # The behaviour of re.split will add empty strings
    # if the regex matches on the begging or ending of the line.
    # Refer to https://docs.python.org/3/library/re.html#re.split

    # Use filter to remove any empty strings
    # that re.split inserted
    data['warnings'] = list(filter(None, temp_warnings))
    # Update the count of warnings to the correct value
    data['warningCount'] = len(data['warnings'])
    return data


class CvpApi():
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

    def cvp_version_compare(self, opr, version, msg):
        ''' Check provided version with given operator against the current CVP
            version

            Args:
                opr (string): The operator. Valid operators are:
                    >  - Greater Than
                    <  - Less Than
                    >= - Greater Than or Equal To
                    <= - Less Than or Equal To
                    == - Equal To
                version (float): The float API Version number to compare the
                    running CVP version to.
        '''
        if opr not in OPERATOR_DICT:
            self.log.error("%s is an invalid operation for version comparison", opr)
            return False

        # Since CVaaS is automatically the latest version of the API, if
        # operators > or >= are provided we can quickly check if we are running
        # on CVaaS and return True if found.
        if opr in ['>', '>='] and self.clnt.is_cvaas:
            return True

        if self.clnt.apiversion is None:
            self.get_cvp_info()

        # Example: if a version of 6.0 is provided with greater than or equal
        # operator (>=) we are validating that the running CVP version is
        # greater than or equal to API Version 6.0.
        # Hence -- self.clnt.apiversion >= 6.0
        if not OPERATOR_DICT[opr](self.clnt.apiversion, version):
            self.log.warning(msg)
            return False
        return True

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
            self.log.error(f"Invalid status {status}."
                           " Status must be Enabled or Disabled."
                           " Defaulting to Disabled")
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
            self.log.error(f"Invalid status {status}."
                           f" Status must be Enabled or Disabled."
                           f" Defaulting to Disabled")
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
        return self.clnt.post(f"/user/updateUser.do?userId={username}",
                              data=data, timeout=self.request_timeout)

    def get_user(self, username):
        ''' Returns specified user information

            Args:
                username (str): username on CVP
        '''
        return self.clnt.get(f"/user/getUser.do?userId={qplus(username)}",
                             timeout=self.request_timeout)

    def get_users(self, query='', start=0, end=0):
        ''' Returns all users in CVP filtered by an optional query parameter

            Args:
                query (str): Query parameter to filter users by.
                start (int): Start index for the pagination.  Default is 0.
                end (int): End index for the pagination.  If end index is 0
                    then all the records will be returned.  Default is 0.

            Returns:
                response (dict): A dict that contains the users.
                    {'total': 1,
                     'roles': {'cvpadmin': ['network-admin']},
                     'users': [{'userId': 'cvpadmin',
                                'firstName': '',
                                'lastName': '',
                                'description': '',
                                'email': 'cvprac@cvprac.com',
                                'lastAccessed': 1654555139700,
                                'contactNumber': '',
                                'userType': 'Local',
                                'userStatus': 'Enabled',
                                'currentStatus': 'Online',
                                'addedByUser': 'cvp system'}]}
        '''
        self.log.debug(f"get_users: query: {query}")
        return self.clnt.get(f"/user/getUsers.do?"
                             f"queryparam={qplus(query)}&startIndex={start}&endIndex={end}",
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
        self.log.debug(f"get_task_by_id: task_id: {task_id}")
        try:
            task = self.clnt.get(f"/task/getTaskById.do?taskId={task_id}",
                                 timeout=self.request_timeout)
        except CvpApiError as error:
            self.log.debug(f"Caught error: {error} attempting to get task.")
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
        self.log.debug(f"get_tasks_by_status: status: {status}")
        data = self.clnt.get(
            f"/task/getTasks.do?queryparam={status}&startIndex={start}&endIndex={end}",
            timeout=self.request_timeout)
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
        return self.clnt.get(f"/task/getTasks.do?queryparam=&startIndex={start}&"
                             f"endIndex={end}", timeout=self.request_timeout)

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
        self.log.debug(f"get_logs_by_id: task_id: {task_id}")
        if self.clnt.apiversion is None:
            self.get_cvp_info()
        if self.clnt.apiversion < 5.0:
            self.log.debug('v1 - v4 /task/getLogsByID.do?')
            resp = self.clnt.get(f"/task/getLogsById.do?id={task_id}&queryparam="
                                 f"&startIndex={start}&endIndex={end}",
                                 timeout=self.request_timeout)
        else:
            self.log.debug('v5 /audit/getLogs.do')
            task_info = self.get_task_by_id(task_id)
            stage_id = None
            if 'stageId' in task_info:
                stage_id = task_info['stageId']
            else:
                self.log.debug(f"No stage ID found for task {task_id}")
            if 'ccIdV2' in task_info:
                cc_id = task_info['ccIdV2']
                if cc_id == '':
                    self.log.debug(f"No ccIdV2 for task {task_id}."
                                   f" It was likely cancelled."
                                   f" Using old /task/getLogsByID.do?")
                    resp = self.clnt.get(
                        f"/task/getLogsById.do?id={task_id}&queryparam="
                        f"&startIndex={start}&endIndex={end}",
                        timeout=self.request_timeout)
                else:
                    resp = self.get_audit_logs_by_id(cc_id, stage_id)
            else:
                self.log.debug(f"No change ID found for task {task_id}")
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
        self.log.debug(f"add_note_to_task: task_id: {task_id} note: {note}")
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
        self.log.debug(f"execute_task: task_id: {task_id}")
        data = {'data': [task_id]}
        self.clnt.post('/task/executeTask.do', data=data, timeout=self.request_timeout)

    def cancel_task(self, task_id):
        ''' Cancel the task

            Args:
                task_id (str): Task ID
        '''
        self.log.debug(f"cancel_task: task_id: {task_id}")
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
        configlets = self.clnt.get(f"/configlet/getConfiglets.do?"
                                   f"startIndex={start}&endIndex={end}",
                                   timeout=self.request_timeout)
        if self.clnt.apiversion == 1.0 or self.clnt.apiversion >= 4.0:
            self.log.debug('v1/v4+ Inventory API Call')
            return configlets
        self.log.debug('v2 Inventory API Call')
        # New API getConfiglets does not return the actual configlet config
        # Get the actual configlet config using getConfigletByName
        if 'data' in configlets:
            for configlet in configlets['data']:
                full_cfglt_data = self.get_configlet_by_name(configlet['name'])
                configlet['config'] = full_cfglt_data['config']
        return configlets

    def get_configlets_and_mappers(self):
        ''' Returns a list of all defined configlets and associated mappers
        '''
        self.log.debug(
            'get_configlets_and_mappers: getConfigletsAndAssociatedMappers')
        return self.clnt.get('/configlet/getConfigletsAndAssociatedMappers.do',
                             timeout=self.request_timeout)

    def get_configlet_builder(self, c_id):
        ''' Returns the configlet builder data for the given configlet ID.

            Args:
                c_id (str): The ID (key) for the configlet to be queried.
        '''
        return self.clnt.get(f"/configlet/getConfigletBuilder.do?id={c_id}",
                             timeout=self.request_timeout)

    def search_configlets(self, query, start=0, end=0):
        ''' Returns a list of configlets that match a search query.

            Args:
                query (str): A simple string of text to be matched against
                    the existing configlets. Not a regex.
                start (int): Start index for the pagination. Default is 0.
                end (int): End index for the pagination. If end index is 0
                    then all the records will be returned. Default is 0.
        '''
        self.log.debug(f"search_configlets: query: {query}")
        return self.clnt.get(f"/configlet/searchConfiglets.do?"
                             f"queryparam={qplus(query)}&startIndex={start}&endIndex={end}",
                             timeout=self.request_timeout)

    def get_configlet_by_name(self, name):
        ''' Returns the configlet with the specified name

            Args:
                name (str): Name of the configlet.  Can contain spaces.

            Returns:
                configlet (dict): The configlet dict.
        '''
        self.log.debug(f"get_configlets_by_name: name: {name}")
        return self.clnt.get(f"/configlet/getConfigletByName.do?name={qplus(name)}",
                             timeout=self.request_timeout)

    def get_configlets_by_container_id(self, c_id, start=0, end=0):
        ''' Returns a list of configlets applied to the given container.

            Args:
                c_id (str): The container ID (key) to query.
                start (int): Start index for the pagination. Default is 0.
                end (int): End index for the pagination. If end index is 0
                    then all the records will be returned. Default is 0.
        '''
        response = None
        try:
            response = self.clnt.get(f"/provisioning/getConfigletsByContainerId.do?"
                                     f"containerId={c_id}&startIndex={start}&endIndex={end}",
                                     timeout=self.request_timeout)
        except CvpRequestError as err:
            err_str = (f"Error reading configlets for container {c_id}: {err}. There is potentially"
                       " an issue with networkprovisioning service or one of its dependencies."
                       " If running CVP 2025.2.X+ then the networkprovisioning sevice likely needs"
                       " to be enabled and started.")
            self.log.error(err_str)
        return response

    def get_configlets_by_netelement_id(self, d_id, start=0, end=0):
        ''' Returns a list of configlets applied to the given device.

            Args:
                d_id (str): The device ID (key) to query.
                start (int): Start index for the pagination. Default is 0.
                end (int): End index for the pagination. If end index is 0
                    then all the records will be returned. Default is 0.
        '''
        response = None
        try:
            response = self.clnt.get(f"/provisioning/getConfigletsByNetElementId.do?"
                                     f"netElementId={d_id}&startIndex={start}&endIndex={end}",
                                     timeout=self.request_timeout)
        except CvpRequestError as err:
            err_str = (f"Error reading configlets by device id {d_id}: {err}. There is potentially"
                       " an issue with networkprovisioning service or one of its dependencies."
                       " If running CVP 2025.2.X+ then the networkprovisioning sevice likely needs"
                       " to be enabled and started.")
            self.log.error(err_str)
        return response

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
        if scope not in ('true', 'false'):
            self.log.error("scope value must be true or false. %s is an invalid value."
                           " Defaulting back to false", scope)
            scope = 'false'
        response = None
        try:
            response = self.clnt.get(f"/provisioning/getImageBundleByContainerId.do?"
                                     f"containerId={container_id}&startIndex={start}&endIndex={end}"
                                     f"&sessionScope={scope}", timeout=self.request_timeout)
        except CvpRequestError as err:
            err_str = (f"Error reading image bundle for container id {container_id}: {err}."
                       " There is potentially an issue with networkprovisioning service or one"
                       " of its dependencies. If running CVP 2025.2.X+ then the"
                       " networkprovisioning sevice likely needs to be enabled and started.")
            self.log.error(err_str)
        return response

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
        self.log.debug(f"get_configlets_history: key: {key}")
        return self.clnt.get(f"/configlet/getConfigletHistory.do?configletId="
                             f"{key}&queryparam=&startIndex={start}&endIndex={end}",
                             timeout=self.request_timeout)

    def get_inventory(self, start=0, end=0, query='', provisioned=True):
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
            data = self.clnt.get(f"/inventory/getInventory.do?"
                                 f"queryparam={qplus(query)}&startIndex={start}&endIndex={end}",
                                 timeout=self.request_timeout)
            return data['netElementList']
        self.log.debug('v2 Inventory API Call')
        data = self.clnt.get(f"/inventory/devices?provisioned={provisioned}",
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

    # pylint: disable=too-many-locals
    def add_devices_to_inventory(self, device_list, wait=False, move_to_container=True):
        ''' Add list of devices to inventory and optionally move them to specified parent container.

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
                move_to_container (boolean): Specifies if the devices should be moved to container
                    within device_list data in addition to adding the devices to the inventory.

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

        self.log.debug('add_devices_to_inventory: called')
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
                    raise RuntimeError(f"Devices {missing_ips} failed to appear in inventory")

            if move_to_container:
                # Move the devices to their specified containers
                for device in device_list:
                    devs = [dev for dev in inv if 'ipAddress' in dev and
                            device['device_ip'] in dev['ipAddress']]
                    dev = devs[0]
                    container = {'key': device['parent_key'],
                                 'name': device['parent_name']}
                    self.move_device_to_container('add_devices_to_inventory API v2',
                                                  dev, container, False)

    def add_device_to_inventory(self, device_ip, parent_name,
                                parent_key, wait=False, move_to_container=True):
        ''' Add device to inventory and optionally move device to the specified parent container.

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
        self.add_devices_to_inventory([device], wait=wait, move_to_container=move_to_container)

    def retry_add_to_inventory(self, dev_mac, device_ip, username,
                               password):
        '''Retry addition of device to Cvp inventory

            Args:
                dev_mac (str): MAC address of device
                device_ip (str): ip address assigned to device
                username (str): username for device login
                password (str): password for user
        '''
        self.log.debug('retry_add_to_inventory: called')
        if self.clnt.apiversion is None:
            self.get_cvp_info()
        if self.clnt.apiversion == 1.0:
            self.log.debug('v1 Inventory API Call')
            data = {"key": dev_mac,
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

    def delete_device(self, dev_mac):
        '''Delete the device and its pending tasks from Cvp inventory

            Args:
                dev_mac (str): mac address of device we are deleting
                                  For CVP 2020 this param is now required to
                                  be the device serial number instead of MAC
                                  address. This method will handle getting
                                  the device serial number via the provided
                                  MAC address.
            Returns:
                data (dict): Contains success or failure message
        '''
        self.log.debug('delete_device: called')
        return self.delete_devices([dev_mac])

    def delete_devices(self, dev_macs):
        '''Delete the device and its pending tasks from Cvp inventory

            Args:
                dev_macs (list): list of mac address for
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
            data = {'data': dev_macs}
            resp = self.clnt.post('/inventory/deleteDevices.do?', data=data,
                                  timeout=self.request_timeout)
        else:
            self.log.warning('NOTE: The Delete Devices API has updated for'
                             ' CVP 2020.2 and it is not required to send the'
                             ' device serial number instead of mac address'
                             ' when deleting a device. Looking up each devices'
                             'serial num based on provided MAC addresses')
            devices = []
            for dev_mac in dev_macs:
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

    def get_device_by_name(self, fqdn, search_by_hostname=False):
        ''' Returns the net element device dict for the devices fqdn name.

            Args:
                fqdn (str): Fully qualified domain name or hostname of the
                    device.
                search_by_hostname (boolean): if set True will attempt to split
                    the fqdn string to match on the hostname portion
                    specifically which should be the first component

            Returns:
                device (dict): The net element device dict for the device if
                    otherwise returns an empty hash.
        '''
        self.log.debug(f"get_device_by_name: fqdn: {fqdn}")
        # data = self.get_inventory(start=0, end=0, query=fqdn)
        data = self.search_topology(fqdn)
        device = {}
        if 'netElementList' in data:
            for netelem in data['netElementList']:
                if not search_by_hostname:
                    if netelem['fqdn'] == fqdn:
                        device = netelem
                        break
                else:
                    if netelem['fqdn'].split('.')[0] == fqdn:
                        device = netelem
                        break
        return device

    def get_device_by_mac(self, dev_mac):
        ''' Returns the net element device dict for the devices mac address.

            Args:
                dev_mac (str): MAC Address of the device.

            Returns:
                device (dict): The net element device dict for the device if
                    otherwise returns an empty hash.
        '''
        self.log.debug(f"get_device_by_mac: MAC address: {dev_mac}")
        # data = self.get_inventory(start=0, end=0, query=dev_mac)
        data = self.search_topology(dev_mac)
        device = {}
        if 'netElementList' in data:
            for netelem in data['netElementList']:
                if netelem['systemMacAddress'] == dev_mac:
                    device = netelem
                    break
        return device

    def get_device_by_serial(self, device_serial):
        ''' Returns the net element device dict for the devices serial number.

            Args:
                device_serial (str): Serial number of the device.

            Returns:
                device (dict): The net element device dict for the device if
                    otherwise returns an empty hash.
        '''
        self.log.debug(f"get_device_by_serial: Serial Number: {device_serial}")
        data = self.search_topology(device_serial)
        device = {}
        if 'netElementList' in data:
            for netelem in data['netElementList']:
                if netelem['serialNumber'] == device_serial:
                    device = netelem
                    break
        return device

    def get_device_configuration(self, dev_mac):
        ''' Returns the running configuration for the device provided.

            Args:
                dev_mac (str): Mac address of the device to get the running
                    configuration for.

            Returns:
                device (dict): The net element device dict for the device if
                    otherwise returns an empty hash.
        '''
        self.log.debug(f"get_device_configuration: dev_mac: {dev_mac}")
        if self.clnt.apiversion is None:
            self.get_cvp_info()
        if self.clnt.apiversion < 4.0:
            data = self.clnt.get(f"/inventory/getInventoryConfiguration.do?netElementId={dev_mac}",
                                 timeout=self.request_timeout)
        else:
            data = self.clnt.get(f"/inventory/device/config?netElementId={dev_mac}",
                                 timeout=self.request_timeout)
        running_config = ''
        if 'output' in data:
            running_config = data['output']
        return running_config

    def get_device_image_info(self, dev_mac):
        ''' Return a dict of info about a device in CVP.

            Args:
                dev_mac (str): Mac address of the device to get the running
                    configuration for.

            Returns:
                device_image_info (dict): Dict of image info for the device
                    if found. Otherwise returns None.
        '''
        self.log.debug(f"Attempt to get net element data for {dev_mac}")
        response = None
        try:
            response = self.clnt.get(
                f"/provisioning/getNetElementInfoById.do?netElementId={qplus(dev_mac)}",
                timeout=self.request_timeout)
        except CvpRequestError as err:
            err_str = (f"Error reading device image info {dev_mac}: {err}. There is potentially"
                       " an issue with networkprovisioning service or one of its dependencies."
                       " If running CVP 2025.2.X+ then the networkprovisioning sevice likely needs"
                       " to be enabled and started.")
            self.log.error(err_str)
        except CvpApiError as error:
            # Catch error when device for provided MAC is not found
            if 'Invalid Netelement id' in str(error):
                self.log.debug(f"Device with MAC {dev_mac} not found")
                return None
            raise error
        return response

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
            return self.clnt.get(f"/inventory/add/searchContainers.do?"
                                 f"startIndex={start}&endIndex={end}")
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
                    self.log.debug(f"No container parentId found for"
                                   f" parentName {full_cont_info['parentName']}")
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
        self.log.debug(f"Get info for container {name}")
        response = None
        try:
            response = self.clnt.get(
                f"/provisioning/searchTopology.do?queryParam={qplus(name)}"
                f"&startIndex=0&endIndex=0")
        except CvpRequestError as err:
            err_str = (f"Error reading container by name {name}: {err}. There is potentially"
                       " an issue with networkprovisioning service or one of its dependencies."
                       " If running CVP 2025.2.X+ then the networkprovisioning sevice likely needs"
                       " to be enabled and started.")
            self.log.error(err_str)
        if response and response['total'] > 0 and response['containerList']:
            for cont in response['containerList']:
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
        self.log.debug(f"Get info for container {key}")
        response = None
        try:
            response = self.clnt.get(f"/provisioning/getContainerInfoById.do?"
                                     f"containerId={qplus(key)}")
        except CvpRequestError as err:
            err_str = (f"Error reading container data by ID {key}: {err}. There is potentially"
                       " an issue with networkprovisioning service or one of its dependencies."
                       " If running CVP 2025.2.X+ then the networkprovisioning sevice likely needs"
                       " to be enabled and started.")
            self.log.error(err_str)
        return response

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
        self.log.debug(f"get_configlets_by_device: mac: {mac}")
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
                        fieldId (str): "",
                        fieldLabel (str): "",
                        value (str): "",
                        type (str): "", (Options below)
                            ('Text box',
                            'Text area',
                            'Drop down',
                            'Check box',
                            'Radio button',
                            'IP address',
                            'Password')
                        validation: {
                            mandatory (boolean): true,
                        },
                        helpText (str): "",
                        depends (str): "",
                        dataValidationErrorExist (boolean): true,
                        dataValidation (string): ""

            Returns:
                key (str): The key for the configlet
        '''
        if not form:
            form = []

        self.log.debug(f"add_configlet_builder: name: {name} config: {config} form: {form}")
        data = {'name': name,
                'data': {'formList': form,
                         'main_script': {'data': config}}}
        # Create the configlet builder
        self.clnt.post(f"/configlet/addConfigletBuilder.do?isDraft={draft}",
                       data=data, timeout=self.request_timeout)

        # Get the key for the configlet
        data = self.clnt.get(f"/configlet/getConfigletByName.do?name={qplus(name)}",
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
        self.log.debug(f"add_configlet: name: {name} config: {config}")
        body = {'name': name, 'config': config}
        # Create the configlet
        self.clnt.post('/configlet/addConfiglet.do', data=body,
                       timeout=self.request_timeout)

        # Get the key for the configlet
        data = self.clnt.get(f"/configlet/getConfigletByName.do?name={qplus(name)}",
                             timeout=self.request_timeout)
        return data['key']

    def delete_configlet(self, name, key):
        ''' Delete the configlet.

            Args:
                name (str): Configlet name
                key (str): Configlet key
        '''
        self.log.debug(f"delete_configlet: name: {name} key: {key}")
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
        self.log.debug(f"update_configlet: config: {config} key: {key} name: {name}")

        # Update the configlet
        body = {'config': config, 'key': key, 'name': name,
                'waitForTaskIds': wait_task_ids}
        return self.clnt.post('/configlet/updateConfiglet.do', data=body,
                              timeout=self.request_timeout)

    def update_configlet_builder(self, name, key, config, draft=False,
                                 wait_for_task=False, form=None):
        ''' Update an existing configlet builder.
            Args:
                config (str): Contents of the configlet builder configuration
                key: (str): key/id of the configlet builder to be updated
                name: (str): name of the configlet builder
                draft (boolean): is update a draft
                wait_for_task (boolean): wait for task IDs to be generated
                form (list): Array/list of form data
                    Parameters:
                        fieldId (str): "",
                        fieldLabel (str): "",
                        value (str): "",
                        type (str): "", (Options below)
                            ('Text box',
                            'Text area',
                            'Drop down',
                            'Check box',
                            'Radio button',
                            'IP address',
                            'Password')
                        validation: {
                            mandatory (boolean): true,
                        },
                        helpText (str): "",
                        depends (str): "",
                        dataValidationErrorExist (boolean): true,
                        dataValidation (string): ""
        '''
        if not form:
            form = []

        data = {
            "name": name,
            "waitForTaskIds": wait_for_task,
            "data": {
                "formList": form,
                "main_script": {
                    "data": config
                }
            }
        }
        self.log.debug(f"update_configlet_builder: config: {config}"
                       f" key: {key} name: {name} form: {form}")
        # Update the configlet builder
        url_string = f"/configlet/updateConfigletBuilder.do?isDraft={draft}&id={key}&action=save"
        return self.clnt.post(url_string, data=data, timeout=self.request_timeout)

    def update_reconcile_configlet(self, dev_mac, config, key, name,
                                   reconciled=False):
        ''' Update the reconcile configlet.

            Args:
                dev_mac (str): Mac address/Key for device whose reconcile
                    configlet is being updated
                config (str): Reconciled config statements
                key (str): Reconcile Configlet key
                name (str): Reconcile Configlet name
                reconciled (boolean): Wait for task IDs to generate

            Returns:
                data (dict): Contains success or failure message
        '''
        self.log.debug(f"update_reconcile_configlet: dev_mac: {dev_mac}"
                       f" config: {config} key: {key} name: {name}")

        url_str = f"/provisioning/updateReconcileConfiglet.do?netElementId={dev_mac}"
        body = {
            'config': config,
            'key': key,
            'name': name,
            'reconciled': reconciled,
            'unCheckedLines': '',
        }
        response = None
        try:
            response = self.clnt.post(url_str, data=body, timeout=self.request_timeout)
        except CvpRequestError as err:
            err_str = (f"Error updating reconcile configlet for device {dev_mac}: {err}."
                       " There is potentially an issue with networkprovisioning service or one"
                       " of its dependencies. If running CVP 2025.2.X+ then the"
                       " networkprovisioning sevice likely needs to be enabled and started.")
            self.log.error(err_str)
        return response

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

    def validate_config_for_device(self, dev_mac, config):
        ''' Validate a config against a device

            Args:
                dev_mac (str): Device MAC address
                config (str): Switch config statements

            Returns:
                response (dict): A dict that contains the result of the
                    validation operation
        '''
        self.log.debug(f"validate_config_for_device: dev_mac: {dev_mac} config: {config}")
        body = {'netElementId': dev_mac, 'config': config}
        return sanitize_warnings(
            self.clnt.post(
                '/configlet/validateConfig.do',
                data=body,
                timeout=self.request_timeout
            )
        )

    def validate_config(self, dev_mac, config):
        ''' Validate a config against a device and parse response to
            produce log messages are return a flag for the config validity.

            Args:
                dev_mac (str): Device MAC address
                config (str): Switch config statements

            Returns:
                response (boolean): A flag signifying if the config is valid or
                    not.
        '''
        self.log.debug(f"validate_config: dev_mac: {dev_mac} config: {config}")
        result = self.validate_config_for_device(dev_mac, config)
        validated = True
        if 'warningCount' in result and result['warnings']:
            for warning in result['warnings']:
                self.log.warning(f"Validation of config produced warning - {warning}")
        if 'errorCount' in result:
            self.log.error(f"Validation of config produced {result['errorCount']} errors")
            if 'errors' in result:
                for error in result['errors']:
                    self.log.error(f"Validation of config produced error - {error}")
            validated = False
        if 'result' in result:
            for item in result['result']:
                if 'messages' in item:
                    for message in item['messages']:
                        self.log.info(f"Validation of config returned message - {message}")
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
        url = (f"/provisioning/getAllTempActions.do?startIndex={start}&endIndex={end}")
        response = None
        try:
            response = self.clnt.get(url, timeout=self.request_timeout)
        except CvpRequestError as err:
            err_str = (f"Error reading all temp actions: {err}. There is potentially"
                       " an issue with networkprovisioning service or one of its dependencies."
                       " If running CVP 2025.2.X+ then the networkprovisioning sevice likely needs"
                       " to be enabled and started.")
            self.log.error(err_str)
        return response

    def _add_temp_action(self, data):
        ''' Adds temp action that requires a saveTopology call to take effect.

            Args:
                data (dict): a data dict with a specific format for the
                    desired action.

                    Base Ex: data = {'data': [{specific key/value pairs}]}
        '''
        url = ('/provisioning/addTempAction.do?'
               'format=topology&queryParam=&nodeId=root')
        try:
            self.clnt.post(url, data=data, timeout=self.request_timeout)
        except CvpRequestError as err:
            err_str = (f"Error adding temp action for data {data}: {err}. There is potentially"
                       " an issue with networkprovisioning service or one of its dependencies."
                       " If running CVP 2025.2.X+ then the networkprovisioning sevice likely needs"
                       " to be enabled and started.")
            self.log.error(err_str)

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
        response = None
        try:
            response = self.clnt.post(url, data=data, timeout=self.request_timeout)
        except CvpRequestError as err:
            err_str = (f"Error saving topology v2 for data {data}: {err}. There is potentially"
                       " an issue with networkprovisioning service or one of its dependencies."
                       " If running CVP 2025.2.X+ then the networkprovisioning sevice likely needs"
                       " to be enabled and started.")
            self.log.error(err_str)
        return response

    def apply_configlets_to_device(self, app_name, dev, new_configlets, # pylint: disable=too-many-locals
                                   create_task=True, reorder_configlets=False, validate=False):
        ''' Apply the configlets to the device.

            Args:
                app_name (str): The application name to use in info field.
                dev (dict): The switch device dict
                new_configlets (list): List of configlet name and key pairs
                create_task (bool): Determines whether or not to execute a save
                    and create the tasks (if any)
                reorder_configlets (bool): Defaults to False. To use this
                    parameter you must first get the full list of configlets
                    applied to the device (for example via the
                    get_configlets_by_device_id function) and provide the
                    full list of configlets (in addition to any new configlets
                    being applied) in the desired order as the new_configlets
                    parameter. It is also important to keep in mind configlets
                    that are applied to parent containers because they will
                    be applied before configlets applied to the device
                    directly. Set this parameter to True only with the full
                    list of configlets being applied to the device provided
                    via the new_configlets parameter.
                validate (bool): Defaults to False. If set to True, the function
                    will validate and compare the configlets to be attached and
                    populate the configCompareCount field in the data dict. In case
                    all keys are 0, ie there is no difference between designed-config
                    and running-config after applying the configlets, no task will be
                    generated.

            Returns:
                response (dict): A dict that contains a status and a list of
                    task ids created (if any).

                    Ex: {u'data': {u'status': u'success', u'taskIds': [u'32']}}
        '''
        self.log.debug(f"apply_configlets_to_device: dev: {dev} names: {new_configlets}")
        # Get a list of the names and keys of the configlets
        cnames = []
        ckeys = []

        if not reorder_configlets:
            # Get all the configlets assigned to the device.
            configlets = self.get_configlets_by_device_id(
                dev['systemMacAddress'])
            for configlet in configlets:
                cnames.append(configlet['name'])
                ckeys.append(configlet['key'])

        # Add the new configlets to the end of the arrays
        for entry in new_configlets:
            cnames.append(entry['name'])
            ckeys.append(entry['key'])

        info = f"{app_name}: Configlet Assign: to Device {dev['fqdn']}"
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
        if validate:
            validation_result = self.validate_configlets_for_device(dev['systemMacAddress'], ckeys)
            data['data'][0].update(
                {
                    "configCompareCount":
                    {
                        "mismatch": validation_result['mismatch'],
                        "reconcile": validation_result['reconcile'],
                        "new": validation_result['new']
                    }
                }
            )
        self.log.debug(f"apply_configlets_to_device: saveTopology data:\n{data['data']}")
        self._add_temp_action(data)
        if create_task:
            return self._save_topology_v2([])
        return None

    # pylint: disable=too-many-locals
    def remove_configlets_from_device(self, app_name, dev, del_configlets,
                                      create_task=True, validate=False):
        ''' Remove the configlets from the device.

            Args:
                app_name (str): The application name to use in info field.
                dev (dict): The switch device dict
                del_configlets (list): List of configlet name and key pairs
                create_task (bool): Determines whether or not to execute a save
                    and create the tasks (if any)
                validate (bool): Defaults to False. If set to True, the function
                    will validate and compare the configlets to be attached and
                    populate the configCompareCount field in the data dict. In case
                    all keys are 0, ie there is no difference between designed-config
                    and running-config after applying the configlets, no task will be
                    generated.

            Returns:
                response (dict): A dict that contains a status and a list of
                    task ids created (if any).

                    Ex: {u'data': {u'status': u'success', u'taskIds': [u'35']}}
        '''
        self.log.debug(f"remove_configlets_from_device: dev: {dev} names: {del_configlets}")

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

        info = f"{app_name} Configlet Remove: from Device {dev['fqdn']}"
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
        if validate:
            validation_result = self.validate_configlets_for_device(dev['systemMacAddress'],
                                                                    keep_keys)
            data['data'][0].update(
                {
                    "configCompareCount": {
                        "mismatch": validation_result['mismatch'],
                        "reconcile": validation_result['reconcile'],
                        "new": validation_result['new']
                    }
                }
            )
        self.log.debug(f"remove_configlets_from_device: saveTopology data:\n{data['data']}")
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
        self.log.debug(f"apply_configlets_to_container: container: {container}"
                       f" names: {new_configlets}")
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

        info = f"{app_name}: Configlet Assign: to Container {container['name']}"
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
        self.log.debug(f"apply_configlets_to_container: saveTopology data:\n{data['data']}")
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
        self.log.debug(f"remove_configlets_from_container: container: {container}"
                       f" names: {del_configlets}")

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

        info = f"{app_name} Configlet Remove: from Container {container['name']}"
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
        self.log.debug(f"remove_configlets_from_container: saveTopology data:\n{data['data']}")
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
        self.log.debug(f"validate_configlets_for_device: "
                       f"MAC: {mac} - conf keys: {configlet_keys} - page_type: {page_type}")
        data = {'configIdList': configlet_keys,
                'netElementId': mac,
                'pageType': page_type}
        response = None
        try:
            response = self.clnt.post(
                '/provisioning/v2/validateAndCompareConfiglets.do',
                data=data, timeout=self.request_timeout)
        except CvpRequestError as err:
            err_str = (f"Error validating configlets for device {mac}: {err}. There is potentially"
                       " an issue with networkprovisioning service or one of its dependencies."
                       " If running CVP 2025.2.X+ then the networkprovisioning sevice likely needs"
                       " to be enabled and started.")
            self.log.error(err_str)
        return response

    def get_applied_devices(self, configlet_name, start=0, end=0):
        ''' Returns a list of devices to which the named configlet is applied.

            Args:
                configlet_name (str): The name of the configlet to be queried.
                start (int): Start index for the pagination. Default is 0.
                end (int): End index for the pagination. If end index is 0
                    then all the records will be returned. Default is 0.
        '''
        return self.clnt.get(f"/configlet/getAppliedDevices.do?"
                             f"configletName={configlet_name}&startIndex={start}&endIndex={end}",
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
        return self.clnt.get(f"/configlet/getAppliedContainers.do?"
                             f"configletName={configlet_name}&startIndex={start}&endIndex={end}",
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
        msg = (f"{operation} container {container_name} under container {parent_name}")
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
        self.log.debug(f"add_container: container: {container_name}"
                       f" parent: {parent_name} parent_key: {parent_key}")
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
        self.log.debug(f"delete_container: container: {container_name}"
                       f" container_key: {container_key} parent: {parent_name}"
                       f" parent_key: {parent_key}")
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
            raise
        if still_exists is not None:
            raise CvpApiError('Container was not deleted. Check for children')
        return resp

    def get_parent_container_for_device(self, dev_mac):
        ''' Add the container to the specified parent.

            Args:
                dev_mac (str): Device mac address

            Returns:
                response (dict): A dict that contains the parent container info
        '''
        self.log.debug(f"get_parent_container_for_device: called for {dev_mac}")
        response = None
        try:
            response = self.clnt.get(f"/provisioning/searchTopology.do?"
                                     f"queryParam={dev_mac}&startIndex=0&endIndex=0",
                                     timeout=self.request_timeout)
        except CvpRequestError as err:
            err_str = (f"Error reading parent container for device {dev_mac}: {err}. There is"
                       " potentially an issue with networkprovisioning service or one of its"
                       " dependencies. If running CVP 2025.2.X+ then the networkprovisioning"
                       " sevice likely needs to be enabled and started.")
            self.log.error(err_str)
        if response and response['total'] > 0:
            cont_name = response['netElementContainerList'][0]['containerName']
            return self.get_container_by_name(cont_name)
        return response

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
        info = f"Device Add {device['fqdn']} to container {container['name']} by {app_name}"
        self.log.debug(f"Attempting to move device {device['fqdn']} to"
                       f" container {container['name']}")
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
                self.log.debug(f"Device {device['fqdn']} already in container {container}")
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
        self.log.debug(f"search_topology: query: {query} start: {start} end: {end}")
        if self.clnt.apiversion is None:
            self.get_cvp_info()
        if self.clnt.apiversion <= 6.0:
            # Original search topology endpoint
            req_url = (f"/provisioning/searchTopology.do?queryParam={qplus(query)}&"
                       f"startIndex={start}&endIndex={end}")
        else:
            # Newer CVP versions should use the V3 version of search topology endpoint
            req_url = (f"/provisioning/v3/searchTopology.do?queryParam={qplus(query)}&"
                       f"startIndex={start}&endIndex={end}")

        response = None
        try:
            response = self.clnt.get(req_url, timeout=self.request_timeout)
        except CvpRequestError as err:
            err_str = (f"Error searching topology for query {query}: {err}. There is potentially"
                       " an issue with networkprovisioning service or one of its dependencies."
                       " If running CVP 2025.2.X+ then the networkprovisioning sevice likely needs"
                       " to be enabled and started.")
            self.log.error(err_str)

        if response and 'netElementList' in response:
            for device in response['netElementList']:
                device['status'] = device['deviceStatus']
                device['parentContainerKey'] = device['parentContainerId']
                if 'isMLAGEnabled' in device:
                    # original key was mlagEnabled but it changed to isMLAGEnabled
                    device['mlagEnabled'] = device['isMLAGEnabled']
                elif 'mlagEnabled' in device:
                    # Key for V3 search topology changes back to mlagEnabled again
                    device['isMLAGEnabled'] = device['mlagEnabled']
                # Key isDANZEnabled for V3 search topology is no longer in return data.
                device['danzEnabled'] = device.get('isDANZEnabled', '')
                # Key bootupTimeStamp for V3 search topology is no longer in return data.
                device['bootupTimestamp'] = device.get('bootupTimeStamp', '')
                # Key internalBuildId for V3 search topology is no longer in return data.
                device['internalBuild'] = device.get('internalBuildId', '')
        return response

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
        url = (f"/provisioning/filterTopology.do?nodeId={node_id}&"
               f"format={fmt}&startIndex={start}&endIndex={end}")
        response = None
        try:
            response = self.clnt.get(url, timeout=self.request_timeout)
        except CvpRequestError as err:
            err_str = (f"Error filtering topology: {err}. There is potentially"
                       " an issue with networkprovisioning service or one of its dependencies."
                       " If running CVP 2025.2.X+ then the networkprovisioning sevice likely needs"
                       " to be enabled and started.")
            self.log.error(err_str)
        return response

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
        self.log.debug(f"check_compliance: node_key: {node_key} node_type: {node_type}")
        data = {'nodeId': node_key, 'nodeType': node_type}
        response = None
        try:
            response = self.clnt.post('/provisioning/checkCompliance.do', data=data,
                                      timeout=self.request_timeout)
        except CvpRequestError as err:
            err_str = (f"Error checking compliance: {err}. There is potentially"
                       " an issue with networkprovisioning service or one of its dependencies."
                       " If running CVP 2025.2.X+ then the networkprovisioning sevice likely needs"
                       " to be enabled and started.")
            self.log.error(err_str)
        if self.clnt.apiversion is None:
            self.get_cvp_info()
        if self.clnt.apiversion >= 2.0:
            if response and response['complianceIndication'] == '':
                response['complianceIndication'] = 'NONE'
        return response

    def get_event_by_id(self, e_id):
        ''' Return information on the requested event ID.

            Args:
                e_id (str): The event id to be queried.
        '''
        return self.clnt.get(f"/event/getEventById.do?eventId={e_id}",
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
        with open(image_path, 'rb') as image_data:
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
        return self.clnt.get(f"/image/getImages.do?queryparam=&startIndex={start}&"
                             f"endIndex={end}", timeout=self.request_timeout)

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
        return self.clnt.get(f"/image/getImageBundles.do?queryparam=&"
                             f"startIndex={start}&endIndex={end}",
                             timeout=self.request_timeout)

    def get_image_bundle_by_name(self, name):
        ''' Return a dict of info about an image bundle.

            Args:
                name (str): Name of image bundle to return info about.

            Returns:
                image bundle (dict): Dict of info specific to the image bundle
                    requested or None if the name requested doesn't exist.
        '''
        self.log.debug(f"Attempt to get image bundle {name}")
        try:
            image = self.clnt.get(f"/image/getImageBundleByName.do?name={qplus(name)}",
                                  timeout=self.request_timeout)
        except CvpApiError as error:
            # Catch an invalid task_id error and return None
            if 'Entity does not exist' in str(error):
                self.log.debug(f"Bundle with name {name} does not exist")
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
        self.log.debug(f"Attempt to apply {image['name']} to {id_type} {name}")
        info = f"Apply image: {image['name']} to {id_type} {name}"
        node_id = ''
        if 'imageBundleKeys' in image:
            if image['imageBundleKeys']:
                node_id = image['imageBundleKeys'][0]
            self.log.info(f"Provided image is an image object."
                          f" Using first value from imageBundleKeys - {node_id}")
        if 'id' in image:
            node_id = image['id']
            self.log.info(f"Provided image is an image bundle object."
                          f" Found v1 API id field - {node_id}")
        elif 'key' in image:
            node_id = image['key']
            self.log.info(f"Provided image is an image bundle object."
                          f" Found v2 API key field - {node_id}")
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
        self.log.debug(f"Attempt to remove {image['name']} from {name}")
        info = f"Remove image: {image['name']} from {name}"
        node_id = ''
        if 'imageBundleKeys' in image:
            if image['imageBundleKeys']:
                node_id = image['imageBundleKeys'][0]
            self.log.info(f"Provided image is an image object."
                          f" Using first value from imageBundleKeys - {node_id}")
        if 'id' in image:
            node_id = image['id']
            self.log.info(f"Provided image is an image bundle object."
                          f" Found v1 API id field - {node_id}")
        elif 'key' in image:
            node_id = image['key']
            self.log.info(f"Provided image is an image bundle object."
                          f" Found v2 API key field - {node_id}")
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
        self.log.debug(f"get_change_controls: query: {query}")
        if self.clnt.apiversion is None:
            self.get_cvp_info()
        if self.clnt.apiversion >= 3.0:
            self.log.debug('v3/v4/v5 getChangeControls API Call')
            self.log.warning(
                'get_change_controls: change control APIs moved for v3/v4/v5')
            return None

        self.log.debug('v2 getChangeControls API Call')
        data = self.clnt.get(
            f"/changeControl/getChangeControls.do?searchText={qplus(query)}"
            f"&startIndex={start}&endIndex={end}",
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
        self.log.debug(f"change_control_available_tasks: query: {query}")
        if self.clnt.apiversion is None:
            self.get_cvp_info()
        if self.clnt.apiversion >= 3.0:
            self.log.debug(
                'v3/v4/v5 uses existing get_task_by_status API Call')
            return self.get_tasks_by_status('PENDING')

        self.log.debug('v2 getTasksByStatus API Call')
        data = self.clnt.get(
            f"/changeControl/getTasksByStatus.do?searchText={qplus(query)}"
            f"&startIndex={start}&endIndex={end}",
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

    def create_change_control_v3(self, cc_id, name, tasks, sequential=True):
        ''' Create change control with provided information and return
            change control ID.

            Args:
                cc_id (string): The ID for the new change control.
                name (string): The name for the new change control.
                tasks (list): A list of Task IDs as strings
                    Ex: ['10', '11', '12']
                sequential (bool): A flag for running tasks sequentially or
                    in parallel. Defaults to True for running sequentially.

            Returns:
                response (dict): A dict that contains...

                Ex: [{u'id': u'cc_id',
                      u'update_timestamp': u'...'}]
        '''
        self.log.debug('create_change_control_v3')
        if self.clnt.apiversion is None:
            self.get_cvp_info()
        if self.clnt.apiversion < 3.0:
            self.log.debug(f"Wrong method for API version {self.clnt.apiversion}."
                           f" Use create_change_control method")
            self.log.warning('create_change_control_v3:'
                             ' Use old change control APIs for old versions')
            return None

        self.log.debug('v3 Update change control API Call')
        stages = []
        if sequential:
            for index, task in enumerate(tasks):
                stage_id = f"stage{index}"
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
        else:
            stage_rows = []
            for index, task in enumerate(tasks):
                stage_id = f"stage{index}"
                stage_row = {
                    'id': stage_id,
                    'action': {
                        'name': 'task',
                        'args': {
                            'TaskID': task,
                        }
                    }
                }
                stage_rows.append(stage_row)
            stages.append({'stage': stage_rows})
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
        self.log.debug(f"add_notes_to_change_control: cc_id {cc_id}, notes {notes}")
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

    def approve_change_control(self, cc_id, timestamp=None):
        ''' Cancel the provided change controls.

            Args:
                cc_id (string): The change control IDs to be approved.
                timestamp(string): The change controls timestamp.
        '''
        if not timestamp:
            timestamp = datetime.utcnow().isoformat() + 'Z'
        self.log.debug('approve_change_control')
        if self.clnt.apiversion is None:
            self.get_cvp_info()
        if self.clnt.apiversion < 3.0:
            self.log.debug(f"Approval methods not valid for API version {self.clnt.apiversion}."
                           f" Functionality did not exist")
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
            self.log.debug(f"Approval methods not valid for API version {self.clnt.apiversion}."
                           f" Functionality did not exist")
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
        msg = 'Change Control Resource APIs supported from 2021.2.0 or newer.'
        if self.cvp_version_compare('>=', 6.0, msg):
            self.log.debug(
                'v6+ Using Resource API Change Control Delete API Call')
            resp_list = []
            for cc_id in cc_ids:
                resp = self.change_control_delete(cc_id)
                resp_list.append(resp)
            return resp_list

        msg = 'Change Control Service APIs supported from 2019.0.0 to 2021.2.0'
        if self.cvp_version_compare('>=', 3.0, msg):
            self.log.debug(
                'v3/v4/v5 /api/v3/services/ccapi.ChangeControl/Delete'
                ' API Call')
            resp_list = []
            for cc_id in cc_ids:
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
        self.log.debug(f"get_change_control_info: {cc_id}")
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
                f"/changeControl/getChangeControlInformation.do?"
                f"startIndex=0&endIndex=0&ccId={cc_id}",
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
        self.log.debug(f"get_change_control_status: {cc_id}")
        if self.clnt.apiversion is None:
            self.get_cvp_info()
        if self.clnt.apiversion < 3.0:
            self.log.debug(f"get_change_control_status method not supported"
                           f" for API version {self.clnt.apiversion}. Use old"
                           f" get_change_control_info method")
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
                create_task (bool): Determines whether or not to execute a save
                    and create the tasks (if any)

            Returns:
                response (dict): A dict that contains a status and a list of
                    task ids created (if any).

                    Ex: {u'data': {u'status': u'success', u'taskIds': []}}
        '''
        info = (f"App {app_name} resetting device {device['fqdn']} and moving it to Undefined")
        self.log.debug(info)

        if 'parentContainerId' in device:
            from_id = device['parentContainerId']
        else:
            parent_cont = self.get_parent_container_for_device(device['key'])
            if parent_cont and 'key' in parent_cont:
                from_id = parent_cont['key']
            else:
                from_id = ''

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
                self.log.debug(f"Device {device['fqdn']} already in container Undefined")
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
        info = f"Deploy device {device['fqdn']} to container {container}"
        self.log.debug(info)
        container_info = self.get_container_by_name(container)
        # Add action for moving device to specified container
        self.move_device_to_container(app_name, device, container_info,
                                      create_task=False)

        # Get proposed configlets device will inherit from container it is
        # being moved to.
        prop_conf = None
        try:
            prop_conf = self.clnt.get(f"/provisioning/getTempConfigsByNetElementId."
                                      f"do?netElementId={device['key']}")
        except CvpRequestError as err:
            err_str = (f"Error reading temp configs for device {device['key']}: {err}."
                       " There is potentially an issue with networkprovisioning service or one"
                       " of its dependencies. If running CVP 2025.2.X+ then the"
                       " networkprovisioning sevice likely needs to be enabled and started.")
            self.log.error(err_str)
        new_configlets = []
        if prop_conf:
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

    def create_enroll_token(self, duration, devices=None):
        ''' Create TerminAttr enrollment token for device authentication
            via certificates.

            Args:
               devices (list): list of device Serial Numbers for which the
                   token should be generated. The default is all devices.
               duration (string): the token's validity time (max 1 month),
                  accepted formats for the legacy endpoint: "24h", "86400s", "60m"
                  accepted format for the new endpoint: "86400s" (only seconds)
            Returns:
                response (list) on CVaaS: A list that contains the generated
                    enrollment token.

                    Ex: [{'enrollmentToken':{'token': <token>, 'groups': [],
                    'reenrollDevices': <devices list>,
                    'validFor': <duration e.g 86400s>, 'field_mask': None}}]
                response (dict) on CV on-prem: A dictionary that contains the
                    generated enrollment token.

                    Ex: {'data': <token>}
        '''
        if not devices:
            devices = ["*"]
        if self.clnt.apiversion is None:
            self.get_cvp_info()
        response = None
        if self.clnt.apiversion >= 14.0:
            # Use resource API for CVP 2024.3.0+
            data = {
                "enrollmentToken": {"reenrollDevices": devices,
                                    "validFor": duration}
            }
            response = self.clnt.post(
                '/api/resources/admin.Enrollment/AddEnrollmentToken',
                data=data, timeout=self.request_timeout)
        elif self.clnt.apiversion >= 6.0:
            # User service API for CVP 2021.2.0 - 2024.2.X
            self.log.debug('v6 /cvpservice/enroll/createToken')
            data = {"reenrollDevices": devices, "duration": duration}
            response = self.clnt.post(
                '/cvpservice/enroll/createToken', data=data, timeout=self.request_timeout)
        else:
            self.log.warning('Enrollment Tokens only supported on CVP 2021.2.0+')
        return response

    def get_all_tags(self, element_type='ELEMENT_TYPE_UNSPECIFIED', workspace_id=''):
        ''' Get all device and/or interface tags from the mainline workspace or all other workspaces
            Args:
               element_type (str): Can be ELEMENT_TYPE_DEVICE, ELEMENT_TYPE_INTERFACE and
                  ELEMENT_TYPE_UNSPECIFIED
                  set to ELEMENT_TYPE_UNSPECIFIED by default which fetches all tags
               workspace_id (str): The ID of the workspace, by default it is set to an empty string
                  which will use the mainline workspace
            Returns:
               response (dict): A dict that contains a list of key-value tags
        '''
        msg = 'Tag.V2 Resource APIs are supported from 2021.2.0 or newer.'
        # For on-prem check the version as it is only supported from 2021.2.0+
        if self.cvp_version_compare('>=', 6.0, msg):
            tag_url = '/api/resources/tag/v2/Tag/all'
            payload = {
                "partialEqFilter": [
                    {
                        "key": {
                            "elementType": element_type,
                            "workspaceId": workspace_id
                        }
                    }
                ]
            }
            self.log.debug(f"v6 {tag_url}")
            return self.clnt.post(tag_url, data=payload)
        return None

    def get_tag_edits(self, workspace_id):
        ''' Show all tags edits in a workspace

            Args:
                workspace_id: The ID of the workspace

            Returns:
               response (dict): A dict that contains...
                    Ex.: {'data': [{'result': {'value': {'key': {'workspaceId': 'testget',
                          'elementType': 'string', 'label': 'string', 'value': 'string'},
                          'remove': False}, 'time': 'rfc3339 time', 'type': 'INITIAL'}}]}
        '''
        msg = 'Tag.V2 Resource APIs are supported from 2021.2.0 or newer.'
        # For on-prem check the version as it is only supported from 2021.2.0+
        if self.cvp_version_compare('>=', 6.0, msg):
            tag_url = '/api/resources/tag/v2/TagConfig/all'
            payload = {
                "partialEqFilter": [
                    {
                        "key": {
                            "workspace_id": workspace_id
                        }
                    }
                ]
            }
            self.log.debug('v6 ' + tag_url + ' ' + str(payload))
            return self.clnt.post(tag_url, data=payload)
        return None

    def get_tag_assignment_edits(self, workspace_id):
        ''' Show all tags assignment edits in a workspace

            Args:
                workspace_id: The ID of the workspace

            Returns:
               response (dict): A dict that contains...
                Ex: {'result': {'value': {'key': {'workspaceId': 'string', 'elementType': 'string',
                'label': 'string', 'value': 'string', 'deviceId': 'string'},
                'remove': False}, 'time': 'rfc3339', 'type': 'INITIAL'}}
        '''
        msg = 'Tag.V2 Resource APIs are supported from 2021.2.0 or newer.'
        # For on-prem check the version as it is only supported from 2021.2.0+
        if self.cvp_version_compare('>=', 6.0, msg):
            tag_url = '/api/resources/tag/v2/TagAssignmentConfig/all'
            payload = {
                "partialEqFilter": [
                    {
                        "key": {
                            "workspace_id": workspace_id
                        }
                    }
                ]
            }
            self.log.debug('v6 ' + tag_url + ' ' + str(payload))
            return self.clnt.post(tag_url, data=payload)
        return None

    def tag_config(self, element_type, workspace_id, tag_label, tag_value, remove=False):
        ''' Create/Delete device or interface tags.
            Tag creation with the tag.v2 resource API has to be done within a workspace.

            Args:
               element_type (str): Can be ELEMENT_TYPE_DEVICE or ELEMENT_TYPE_INTERFACE to
                    create device and interface tag respectively.
               workspace_id(str): The ID of the workspace.
                    This should be generated by the create_workspace() API call.
               tag_label(str): the label of the desired tag
               tag_value(str): the value of the desired tag
               remove (Boolean): When set to True it will remove the device/interface tag.
                    When set to False (default) it will create the device/interface tag.

            Returns:
                response (dict): A dict that contains...
                    Ex: {'value': {'key': {'workspaceId': 'string', 'elementType': 'string',
                                        'label': 'string', 'value': 'string'}},
                         'time': 'rfc3339 time'}
        '''
        msg = 'Tag.V2 Resource APIs are supported from 2021.2.0 or newer.'
        # For on-prem check the version as it is only supported from 2021.2.0+
        if self.cvp_version_compare('>=', 6.0, msg):
            tag_url = '/api/resources/tag/v2/TagConfig'
            payload = {
                "key": {
                    "elementType": element_type,
                    "workspaceId": workspace_id,
                    "label": tag_label,
                    "value": tag_value
                },
                "remove": remove
            }
            self.log.debug(f"v6 {tag_url} " + str(payload))
            return self.clnt.post(tag_url, data=payload)
        return None

    def tag_assignment_config(self, element_type, workspace_id, tag_label,
                              tag_value, device_id, interface_id, remove=False):
        ''' Assign/Unassign device or interface tags.
            Tag assignment with the tag.v2 resource API has to be done within a workspace.

            Args:
               element_type (str): can be ELEMENT_TYPE_DEVICE or ELEMENT_TYPE_INTERFACE to
                    create device and interface tag respectively
               workspace_id(str): the ID of the workspace. This should be generated by
                    the create_workspace() API call.
               tag_label(str): the label of the desired tag
               tag_value(str): the value of the desired tag
               device_id (str): the Serial Number of the device
               interface_id (str): the interface name of the device, e.g.: Ethernet1
               remove (Boolean): When set to True it will remove the device/interface
                    tag assignment.
                    When set to False (default) it will create the device/interface tag assignment.
            Returns:
               response (dict): A dict that contains...

                    Ex: {'value': {'key': {'workspaceId': 'string', 'elementType': 'string',
                                           'label': 'string', 'value': 'string',
                                           'deviceId': 'string', 'interfaceId': 'string'},
                                   'remove': Boolean},'time': 'rfc3339 time'}

        '''
        msg = 'Tag.V2 Resource APIs are supported from 2021.2.0 or newer.'
        # For on-prem check the version as it is only supported from 2021.2.0+
        if self.cvp_version_compare('>=', 6.0, msg):
            tag_url = '/api/resources/tag/v2/TagAssignmentConfig'
            payload = {
                "key": {
                    "elementType": element_type,
                    "workspaceId": workspace_id,
                    "label": tag_label,
                    "value": tag_value,
                    "deviceId": device_id,
                    "interfaceId": interface_id
                },
                "remove": remove
            }
            self.log.debug(f"v6 {tag_url} " + str(payload))
            return self.clnt.post(tag_url, data=payload)
        return None

    def get_all_workspaces(self):
        ''' Get state information for all workspaces

            Returns:
               response (dict): A dict that contains a list of key-values for workspaces
        '''
        msg = 'Workspace Resource APIs are supported from 2021.2.0 or newer.'
        # For on-prem check the version as it is only supported from 2021.2.0+
        if self.cvp_version_compare('>=', 6.0, msg):
            workspace_url = '/api/resources/workspace/v1/Workspace/all'
            payload = {}
            self.log.debug(f"v6 {workspace_url}")
            return self.clnt.post(workspace_url, data=payload)
        return None

    def get_workspace(self, workspace_id):
        ''' Get state information for all workspaces

            Returns:
               response (dict): A dict that contains a list of key-values for workspaces
        '''
        msg = 'Workspace Resource APIs are supported from 2021.2.0 or newer.'
        # For on-prem check the version as it is only supported from 2021.2.0+
        if self.cvp_version_compare('>=', 6.0, msg):
            workspace_url = f"/api/resources/workspace/v1/Workspace?key.workspaceId={workspace_id}"
            self.log.debug(f"v6 {workspace_url}")
            return self.clnt.get(workspace_url)
        return None

    def workspace_config(self, workspace_id, display_name,
                         description='', request='REQUEST_UNSPECIFIED',
                         request_id=''):
        ''' Create, Build and Submit workspaces.

            Args:
                workspace_id (str): The (unique) name of the workspace.
                    Previously used names cannot be used if the workspace was closed or abandoned.
                display_name (str): The display name of the workspace.
                description (str): The description of the workspace.
                request (string): Can have the following values:
                    - REQUEST_UNSPECIFIED
                    - REQUEST_START_BUILD
                    - REQUEST_CANCEL_BUILD
                    - REQUEST_SUBMIT
                    - REQUEST_ABANDON
                    - REQUEST_ROLLBACK
                request_id (str): An arbitrary requestId that is required for the
                    build and submit process.

            Returns:
               response (dict): A dict that contains...
                    Ex: {'value': {'key': {'workspaceId': 'string'},
                                'displayName': 'string','description': 'string',
                                'requestParams': {'requestId': 'string'}
                                },
                         'time': 'rfc3339 time'}
        '''
        msg = 'Workspace Resource APIs are supported from 2021.2.0 or newer.'
        # For on-prem check the version as it is only supported from 2021.2.0+
        if self.cvp_version_compare('>=', 6.0, msg):
            workspace_url = '/api/resources/workspace/v1/WorkspaceConfig'
            payload = {
                "key": {
                    "workspaceId": workspace_id
                },
                "displayName": display_name,
                "description": description,
                "request": request,
                "requestParams": {
                    "requestId": request_id
                }
            }
            self.log.debug('v6 ' + str(workspace_url) + ' ' + str(payload))
            return self.clnt.post(workspace_url, data=payload)
        return None

    def workspace_build_status(self, workspace_id, build_id):
        ''' Verify the state of the workspace build process.

            Args:
                workspace_id (str): The (unique) name of the workspace.
                build_id (str): The buildId of the workspace for which the
                    build process was requested.
            Returns:
                response (dict): A dict that contains...
                    Ex: {'value': {'key': {'workspaceId': 'string', 'buildId': 'string'},
                         'state': 'BUILD_STATE_SUCCESS', 'buildResults': {'values': ...
        '''
        msg = 'Workspace Resource APIs are supported from 2021.2.0 or newer.'
        # For on-prem check the version as it is only supported from 2021.2.0+
        if self.cvp_version_compare('>=', 6.0, msg):
            params = f"key.workspaceId={workspace_id}&key.buildId={build_id}"
            workspace_url = '/api/resources/workspace/v1/WorkspaceBuild?' + params
            self.log.debug(f"v6 {workspace_url + params}")
            return self.clnt.get(workspace_url, timeout=self.request_timeout)
        return None

    def change_control_get_one(self, cc_id, cc_time=None):
        ''' Get the configuration and status of a change control using Resource APIs.
            Supported versions: CVP 2021.2.0 or newer and CVaaS.

            Args:
               cc_id (str): The ID of the change control.
               cc_time (str): Time indicates the time for which you are interested in the data.
                    If no time is given, the server will use the time at which it makes the request.
                    The time format is RFC 3339, e.g.: 2021-12-24T11:30:00.00Z.
            Returns:
               response (dict): A dict that contains...
                  Ex: {"value":{"key":{"id":"rL6Tog6UU"}, "change":{"name":"Change 20211213_210554",
                       "rootStageId":"kZUWqyIArD",
                       "stages":{"values":{"kZUWqyIArD":{"name":"Change 20211213_210554 Root",
                       "rows":{"values":[{"values":["vazWhKyVRR"]}]}},
                       "vazWhKyVRR":{"name":"Update Config",
                       "action":{"name":"task", "timeout":3000,
                       "args":{"values":{"TaskID":"538"}}}}}},
                       "notes":"", "time":"2021-12-13T21:05:58.813750128Z", "user":"cvpadmin"},
                       "approve":{"value":true, "time":"2021-12-13T21:11:26.788753264Z",
                       "user":"cvpadmin"}}, "time":"2021-12-13T21:11:26.788753264Z"}%
        '''
        msg = 'Change Control Resource APIs are supported from 2021.2.0 or newer.'
        # For on-prem check the version as it is only supported from 2021.2.0+
        if self.cvp_version_compare('>=', 6.0, msg):
            if cc_time is None:
                params = f"key.id={cc_id}"
            else:
                params = f"key.id={cc_id}&time={cc_time}"
            cc_url = '/api/resources/changecontrol/v1/ChangeControl?' + params
            self.log.debug(f"v6 {cc_url}")
            try:
                response = self.clnt.get(cc_url, timeout=self.request_timeout)
            except Exception as error:
                if 'resource not found' in str(error):
                    return None
                raise error
            return response
        return None

    def change_control_get_all(self):
        ''' Get the configuration and status of all Change Controls using Resource APIs.
            Supported versions: CVP 2021.2.0 or newer and CVaaS.

            Returns:
               response (dict): A dict that contains a list of all Change Controls.
        '''
        msg = 'Change Control Resource APIs are supported from 2021.2.0 or newer.'
        # For on-prem check the version as it is only supported from 2021.2.0+
        if self.cvp_version_compare('>=', 6.0, msg):
            cc_url = '/api/resources/changecontrol/v1/ChangeControl/all'
            self.log.debug(f"v6 {cc_url}")
            return self.clnt.get(cc_url, timeout=self.request_timeout)
        return None

    def change_control_approval_get_one(self, cc_id, cc_time=None):
        ''' Get the state of a specific Change Control's approve config using Resource APIs.
            Supported versions: CVP 2021.2.0 or newer and CVaaS.

            Args:
               cc_id (str): The ID of the change control.
               cc_time (str): Time indicates the time for which you are interested in the data.
                    If no time is given, the server will use the time at which it makes the request.
                    The time format is RFC 3339, e.g.: 2021-12-24T11:30:00.00Z.
            Returns:
               response (dict): A dict that contains...
                    Ex: {'value': {'key': {'id': '<CC ID>'}, 'approve': {'value': True},
                         'version': '2021-12-13T21:05:58.813750128Z'},
                         'time': '2021-12-13T21:11:26.788753264Z'}
        '''
        msg = 'Change Control Resource APIs are supported from 2021.2.0 or newer.'
        # For on-prem check the version as it is only supported from 2021.2.0+
        if self.cvp_version_compare('>=', 6.0, msg):
            if cc_time is None:
                params = f"key.id={cc_id}"
            else:
                params = f"key.id={cc_id}&time={cc_time}"
            cc_url = '/api/resources/changecontrol/v1/ApproveConfig?' + params
            cc_status = self.change_control_get_one(cc_id)
            if cc_status is None:
                return None
            if 'value' in cc_status and 'approve' not in cc_status['value']:
                self.log.warning("The change has not been approved yet."
                                 " A change has to be approved at least once for the 'approve'"
                                 " state to be populated.")
                return None
            return self.clnt.get(cc_url, timeout=self.request_timeout)
        return None

    def change_control_approval_get_all(self):
        ''' Get state information for all Change Control Approvals using Resource APIs.
            Supported versions: CVP 2021.2.0 or newer and CVaaS.

            Returns:
               response (dict): A dict that contains a list of all Change Control Approval Configs.
        '''
        msg = 'Change Control Resource APIs are supported from 2021.2.0 or newer.'
        # For on-prem check the version as it is only supported from 2021.2.0+
        if self.cvp_version_compare('>=', 6.0, msg):
            cc_url = '/api/resources/changecontrol/v1/ApproveConfig/all'
            self.log.debug(f"v6 {cc_url}")
            return self.clnt.get(cc_url, timeout=self.request_timeout)
        return None

    def change_control_approve(self, cc_id, notes="", approve=True):
        ''' Approve/Unapprove a change control using Resource APIs.
            Supported versions: CVP 2021.2.0 or newer and CVaaS.

            Args:
              cc_id (str): The ID of the change control.
              notes (str): An optional approval note.
              approve (bool): Set to True to approve a change and to False to unapprove a change.
              The default is True.
        '''
        cc_url = '/api/resources/changecontrol/v1/ApproveConfig'
        # For on-prem check the version as it is only supported from 2021.2.0+
        # Since the get_change_control already checks this, no need to check it again
        cc_status = self.change_control_get_one(cc_id)
        if cc_status is None:
            return None
        if ('value' in cc_status and 'change' in cc_status['value'] and
                'time' in cc_status['value']['change']):
            version = cc_status['value']['change']['time']
        else:
            self.log.error('The version timestamp was not found in the CC status.')
            return None
        payload = {
            "key": {
                "id": cc_id
            },
            "approve": {
                "value": approve,
                "notes": notes
            },
            "version": version
        }
        return self.clnt.post(cc_url, data=payload, timeout=self.request_timeout)

    def change_control_delete(self, cc_id):
        ''' Delete a pending Change Control using Resource APIs.
            Supported versions: CVP 2021.2.0 or newer and CVaaS.

            Args:
              cc_id (str): The ID of the change control.
        '''
        msg = 'Change Control Resource APIs are supported from 2021.2.0 or newer.'
        # For on-prem check the version as it is only supported from 2021.2.0+
        if self.cvp_version_compare('>=', 6.0, msg):
            params = f"key.id={cc_id}"
            cc_url = '/api/resources/changecontrol/v1/ChangeControlConfig?' + params
            self.log.debug(f"v6 {cc_url}")
            return self.clnt.delete(cc_url, timeout=self.request_timeout)
        return None

    def change_control_create_with_custom_stages(self, custom_cc=None):
        ''' Create a Change Control with custom stage hierarchy using Resource APIs.
            Supported versions: CVP 2021.2.0 or newer and CVaaS.

            Args:
                custom_cc (dict): A dictionary with the entire stage hierarchy.
                Ex1: {'key': {'id': '409b94d1-c0cb-4d74-8f88-89f66f13f109'},
                     'change': {'name': 'Change_20211217_034338',
                     'notes': 'cvprac CC',
                     'rootStageId': 'root',
                     'stages': {'values': {'root': {'name': 'root',
                                                'rows': {'values': [{'values': ['1-2']},
                                                                    {'values': ['3']}]}},
                                        '1-2': {'name': 'stages 1-2',
                                                'rows': {'values': [{'values': ['1ab']},
                                                                    {'values': ['2']}]}},
                                        '1a': {'action': {'args': {'values': {'TaskID': '1242'}},
                                                            'name': 'task',
                                                            'timeout': 3000},
                                                'name': 'stage 1a'},
                                        '1ab': {'name': 'stage 1ab',
                                                'rows': {'values': [{'values': ['1a',
                                                                                '1b']}]}},
                                        '1b': {'action': {'args': {'values': {'TaskID': '1243'}},
                                                            'timeout': 3000},
                                                'name': 'stage 1b'},
                                        '2': {'action': {'args': {'values': {'TaskID': '1240'}},
                                                        'name': 'task',
                                                        'timeout': 3000},
                                                'name': 'stage 2'},
                                        '3': {'action': {'args': {'values': {'TaskID': '1241'}},
                                                        'name': 'task',
                                                        'timeout': 3000},
                                                'name': 'stage 3'},
                                        }}}}
                The above would result in the following hierarchy:
                    root (series)
                    |- stages 1-2 (series)
                    |  |- stage 1ab (parallel)
                    |  |    |- stage 1a
                    |  |    |- stage 1b
                    |  |- stage 2
                    |- stage 3

                Ex2 (MLAG ISSU):
                    {'key': {'id': 'PXs9cKimC'},
                     'change': {'name': 'Change 20211217_040530',
                     'notes': '',
                     'rootStageId': 'root',
                     'stages': {'values': { 'root': {'name': 'Change 20211217_040530 Root',
                                                     'rows': {
                                                         'values': [{'values': ['left-leafs']}],
                                                     }},
                                            'upgrade1': {'action': {
                                                             'args': {'values': {'TaskID': '1242'}},
                                                             'name': 'task',
                                                             'timeout': 3000},
                                                         'name': 'Image Upgrade'},
                                            'pre-mlag-check-l2': {'action': {
                                                                      'args': {
                                                                          'values': {
                                                                              'DeviceID': 'SN2'}},
                                                                      'name': 'mlaghealthcheck'},
                                                          'name': 'Check MLAG Health'},
                                            'left-leafs': {'name': 'left-leafs',
                                                          'rows': {
                                                              'values': [{'values': ['leaf1']},
                                                                         {'values': ['leaf2']}]}},
                                            'upgrade2': {'action': {'args': {
                                                                      'values': {'TaskID': '1243'}},
                                                                      'name': 'task',
                                                                      'timeout': 3000},
                                                           'name': 'Image Upgrade'},
                                            'pre-mlag-check-l1': {'action': {
                                                                      'args': {
                                                                          'values': {
                                                                              'DeviceID': 'SN1'}},
                                                                      'name': 'mlaghealthcheck'},
                                                          'name': 'Check MLAG Health'},
                                            'post-mlag-check-l2': {'action': {
                                                                       'args': {
                                                                           'values': {
                                                                               'DeviceID': 'SN1'}},
                                                                       'name': 'mlaghealthcheck'},
                                                           'name': 'Check MLAG Health'},
                                            'leaf1': {'name': 'leaf1',
                                                          'rows': {
                                                              'values': [{'values': [
                                                                              'pre-mlag-check-l1']},
                                                                         {'values': [
                                                                              'upgrade1']},
                                                                         {'values': [
                                                                              'post-mlag-check-l1'],
                                                                         }]}},
                                            'post-mlag-check-l1': {'action': {
                                                                       'args': {
                                                                           'values': {
                                                                               'DeviceID': 'SN2'}},
                                                                      'name': 'mlaghealthcheck'},
                                                           'name': 'Check MLAG Health'},
                                            'leaf2': {'name': 'leaf2',
                                                      'rows': {'values': [{'values': [
                                                                              'pre-mlag-check-l2']},
                                                                          {'values': [
                                                                               'upgrade2']},
                                                                          {'values': [
                                                                              'post-mlag-check-l2'],
                                                                          }]}}}}}
                    }
                    The above would result in the following hierarchy:
                    root (series)
                    |- left-leafs (series)
                       |- leaf1 (series)
                       |    |- pre-mlag-check-l1
                       |    |- upgrade1
                       |    |- post-mlag-check-l1
                       |- leaf2 (series)
                            |- pre-mlag-check-l1
                            |- upgrade1
                            |- post-mlag-check-l1

            Returns:
                response (dict): A dict that contains...
                Ex: {'value': {'key': {'id':cc_id,
                      'time': '...'}
        '''
        msg = 'Change Control Resource APIs are supported from 2021.2.0 or newer.'
        # For on-prem check the version as it is only supported from 2021.2.0+
        if self.cvp_version_compare('>=', 6.0, msg):
            payload = custom_cc
            cc_url = '/api/resources/changecontrol/v1/ChangeControlConfig'
            self.log.debug('v6 ' + str(cc_url) + ' ' + str(payload))
            return self.clnt.post(cc_url, data=payload)
        return None

    def change_control_create_for_tasks(self, cc_id, name, tasks, series=True):
        ''' Create a simple Change Control for tasks using Resource APIs.
            Supported versions: CVP 2021.2.0 or newer and CVaaS.

            This function will create a change with either all Task actions in series or parallel.
            For custom stage hierarchy the change_control_create_with_custom_stages()
            should be used.
            Args:
                cc_id (string): The ID for the new change control.
                name (string): The name for the new change control.
                tasks (list): A list of Task IDs as strings
                    Ex: ['10', '11', '12']
                series (bool): A flag for running tasks in series or
                    in parallel. Defaults to True for running in series.
            Returns:
                response (dict): A dict that contains...
                Ex: {'value': {'key': {'id':cc_id,
                      'time': '...'}
        '''
        stages = {'values': {'root': {'name': 'root', 'rows': {'values': []}}}}
        if series:
            for index, task in enumerate(tasks):
                stage_id = f"stage{index}"
                stages['values']['root']['rows']['values'].append({'values': [stage_id]})
                stages['values'][stage_id] = {
                    'action': {
                        'args': {
                            'values': {
                                'TaskID': task,
                            },
                        },
                        'name': 'task',
                        'timeout': 3000,
                    },
                    'name': stage_id,
                }
        else:
            stages['values']['root']['rows']['values'].append({'values': []})
            for index, task in enumerate(tasks):
                stage_id = f"stage{index}"
                stages['values']['root']['rows']['values'][0]['values'].append(stage_id)
                stages['values'][stage_id] = {
                    'action': {
                        'args': {
                            'values': {
                                'TaskID': task,
                            },
                        },
                        'name': 'task',
                        'timeout': 3000,
                    },
                    'name': stage_id,
                }
        msg = 'Change Control Resource APIs are supported from 2021.2.0 or newer.'
        # For on-prem check the version as it is only supported from 2021.2.0+
        if self.cvp_version_compare('>=', 6.0, msg):
            payload = {
                'key': {
                    'id': cc_id
                },
                'change': {
                    'name': name,
                    'rootStageId': 'root',
                    'notes': 'randomString',
                    'stages': stages
                }
            }
            cc_url = '/api/resources/changecontrol/v1/ChangeControlConfig'
            self.log.debug('v6 ' + str(cc_url) + ' ' + str(payload))
            return self.clnt.post(cc_url, data=payload, timeout=self.request_timeout)
        return None

    def change_control_start(self, cc_id, notes=""):
        ''' Start a Change Control using Resource APIs.
            Supported versions: CVP 2021.2.0 or newer and CVaaS.
            Args:
                cc_id (string): The ID for the new change control.
                notes (string): An optional note.
            Returns:
                response (dict): A dict that contains...
                Ex: {"value":{"key":{"id":cc_id}, "start":{"value":true, "notes":"note"}},
                     "time":"2021-12-14T21:02:21.830306071Z"}
        '''
        msg = 'Change Control Resource APIs are supported from 2021.2.0 or newer.'
        # For on-prem check the version as it is only supported from 2021.2.0+
        if self.cvp_version_compare('>=', 6.0, msg):
            payload = {
                "key": {
                    "id": cc_id
                },
                "start": {
                    "value": True,
                    "notes": notes
                }
            }
            cc_url = '/api/resources/changecontrol/v1/ChangeControlConfig'
            self.log.debug('v6 ' + str(cc_url) + ' ' + str(payload))
            return self.clnt.post(cc_url, data=payload, timeout=self.request_timeout)
        return None

    def change_control_stop(self, cc_id, notes=""):
        ''' Stop a Change Control using Resource APIs.
            Supported versions: CVP 2021.2.0 or newer and CVaaS.

            Args:
                cc_id (string): The ID for the new change control.
                notes (string): An optional note.
            Returns:
                response (dict): A dict that contains...
                Ex: {"value":{"key":{"id":cc_id}, "start":{"value":false, "notes":"note"}},
                     "time":"2021-12-14T21:02:21.830306071Z"}
        '''
        msg = 'Change Control Resource APIs are supported from 2021.2.0 or newer.'
        # For on-prem check the version as it is only supported from 2021.2.0+
        if self.cvp_version_compare('>=', 6.0, msg):
            payload = {
                "key": {
                    "id": cc_id
                },
                "start": {
                    "value": False,
                    "notes": notes
                }
            }
            cc_url = '/api/resources/changecontrol/v1/ChangeControlConfig'
            self.log.debug('v6 ' + str(cc_url) + ' ' + str(payload))
            return self.clnt.post(cc_url, data=payload, timeout=self.request_timeout)
        return None

    def change_control_schedule(self, cc_id, schedule_time, notes=""):
        ''' Schedule a Change Control using Resource APIs.
            Supported versions: CVP 2022.1.0 or newer and CVaaS.

            Args:
                cc_id (string): The ID for the new change control.
                schedule_time (string): rfc3339 time format, e.g: 2021-12-23T02:07:00.0Z
                notes (string): An optional note.
            Returns:
                response (dict): A dict that contains...
                Ex: {"value":{"key":{"id":"5821c7c1-e276-4387-b60a"},
                              "schedule":{"value":"2021-12-23T02:07:00Z",
                                          "notes":"CC schedule via curl"}},
                     "time":"2021-12-23T02:06:18.739965204Z"}
        '''
        msg = 'Change Control Scheduling via Resource APIs are supported from 2022.1.0 or newer.'
        # For on-prem check the version as it is only supported from 2022.1.0+
        if self.cvp_version_compare('>=', 8.0, msg):
            payload = {
                "key": {
                    "id": cc_id
                },
                "schedule": {
                    "value": schedule_time,
                    "notes": notes
                }
            }
            cc_url = '/api/resources/changecontrol/v1/ChangeControlConfig'
            self.log.debug('v8 ' + str(cc_url) + ' ' + str(payload))
            return self.clnt.post(cc_url, data=payload, timeout=self.request_timeout)
        return None

    def device_decommissioning(self, device_id, request_id):
        ''' Decommission a device using Resource APIs.
            Supported versions: CVP 2021.3.0 or newer and CVaaS.
            Args:
                device_id (string): Serial Number of the device.
                request_id (string): Key identifies the request to decommission the device.
                    Recommended to generate uuid with str(uuid.uuid4()).
            Returns:
                response (dict): Returns None if device is not found else return dict that contains
                Ex: {'value': {'key': {'requestId': '4a4ba5a2-9886-4cd5-84d6-bdaf85a9f091'},
                     'deviceId': 'BAD032986065E8DC14CBB6472EC314A6'},
                     'time': '2022-02-12T02:58:30.765459650Z'}
        '''
        device_exists = False
        inventory = self.get_inventory(provisioned=False)
        for device in inventory:
            if device['serialNumber'] == device_id:
                device_exists = True
                break
        if device_exists:
            msg = 'Decommissioning via Resource APIs are supported from 2021.3.0 or newer.'
            # For on-prem check the version as it is only supported from 2021.3.0+
            if self.cvp_version_compare('>=', 7.0, msg):
                payload = {
                    "key": {
                        "request_id": request_id
                    },
                    "device_id": device_id
                }
                url = '/api/resources/inventory/v1/DeviceDecommissioningConfig'
                self.log.debug('v7 ' + str(url) + ' ' + str(payload))
                return self.clnt.post(url, data=payload, timeout=self.request_timeout)
        else:
            self.log.warning("Device with %s serial number does not exist (or is not registered)"
                             " to decommission", device_id)
        return None

    def device_decommissioning_status_get_one(self, request_id):
        ''' Get the decommission status of a device using Resource APIs.
            Supported versions: CVP 2021.3.0 or newer and CVaaS.
            Args:
                request_id (string): key identifies the request to decommission the device
            Returns:
                response (dict): A dict that contains...
                Ex:{"result":{"value":{"key":{"requestId":"123456789"},
                  "status":"DECOMMISSIONING_STATUS_IN_PROGRESS",
                  "statusMessage":"Disabled TerminAttr, waiting for device to be marked inactive"},
                  "time":"2022-02-04T19:41:46.376310308Z","type":"INITIAL"}}
        '''
        msg = 'Decommissioning via Resource APIs are supported from 2021.3.0 or newer.'
        # For on-prem check the version as it is only supported from 2021.3.0+
        if self.cvp_version_compare('>=', 7.0, msg):
            params = f"key.requestId={request_id}"
            url = '/api/resources/inventory/v1/DeviceDecommissioning?' + params
            self.log.debug('v7 ' + str(url))
            return self.clnt.get(url, timeout=self.request_timeout)
        return None

    def device_decommissioning_status_get_all(self, status="DECOMMISSIONING_STATUS_UNSPECIFIED"):
        ''' Get the decommissioning status of all devices using Resource APIs.
            Supported versions: CVP 2021.3.0 or newer and CVaaS.
            Args:
                status (enum): By default it will get the decommissioning status for all devices.
                    Possible values:
                        "DECOMMISSIONING_STATUS_UNSPECIFIED" or 0,
                        "DECOMMISSIONING_STATUS_IN_PROGRESS" or 1,
                        "DECOMMISSIONING_STATUS_FAILURE" or 2,
                        "DECOMMISSIONING_STATUS_SUCCESS" or 3
            Returns:
                response (dict): A dict that contains...
                Ex: {"result":{"value":{"key":{"requestId":"123456789"},
                "status":"DECOMMISSIONING_STATUS_IN_PROGRESS",
                "statusMessage":"Disabled TerminAttr, waiting for device to be marked inactive"},
                "time":"2022-02-04T19:41:46.376310308Z","type":"INITIAL"}}
        '''
        msg = 'Decommissioning via Resource APIs are supported from 2021.3.0 or newer.'
        # For on-prem check the version as it is only supported from 2021.3.0+
        if self.cvp_version_compare('>=', 7.0, msg):
            payload = {
                "partialEqFilter": [
                    {
                        "status": status,
                    }
                ]
            }
            url = '/api/resources/inventory/v1/DeviceDecommissioning/all'
            self.log.debug('v7 ' + str(url))
            return self.clnt.post(url, data=payload, timeout=self.request_timeout)
        return None

    def add_role(self, name, description, moduleList):
        ''' Add new local role to the CVP UI.
            Args:
                name (str): local role name on CVP
                description (str): role description
                moduleList (list): list of modules (name (str) and mode (str))
        '''
        data = {"name": name,
                "description": description,
                "moduleList": moduleList}
        return self.clnt.post('/role/createRole.do', data=data,
                              timeout=self.request_timeout)

    def update_role(self, rolekey, name, description, moduleList):
        ''' Updates role information, like
            role name, description and role modules.
            Args:
                rolekey (str): local role key on CVP
                name (str): local role name on CVP
                description (str): role description
                moduleList (list): list of modules (name (str) and mode (str))
        '''
        data = {"key": rolekey,
                "name": name,
                "description": description,
                "moduleList": moduleList}
        return self.clnt.post('/role/updateRole.do', data=data,
                              timeout=self.request_timeout)

    def get_role(self, rolekey):
        ''' Returns specified role information.
            Args:
                rolekey (str): role key on CVP
            Returns:
               response (dict): Returns a dict that contains the role.
               Ex: {'name': 'Test Role', 'key': 'role_1599019487020581247',
                    'description': 'Test'...}
        '''
        return self.clnt.get(f"/role/getRole.do?roleId={rolekey}",
                             timeout=self.request_timeout)

    def get_roles(self):
        ''' Get all the user roles in CloudVision.
            Returns:
               response (dict): Returns a dict that contains all the user role states..
               Ex: {'total': 7, 'roles': [{'name': 'Test Role', 'key': 'role_1599019487020581247',
               'description': 'Test'...}]}
        '''
        url = '/role/getRoles.do?startIndex=0&endIndex=0'
        return self.clnt.get(url, timeout=self.request_timeout)

    def delete_role(self, rolekey):
        ''' Remove specified role from CVP
            Args:
                rolekey (str): role key on CVP
        '''
        data = [rolekey]
        return self.delete_roles(data)

    def delete_roles(self, rolekeys):
        ''' Remove specified roles from CVP
            Args:
                rolekeys (list): list of role keys (str) on CVP
        '''
        return self.clnt.post('/role/deleteRoles.do', data=rolekeys,
                              timeout=self.request_timeout)

    def svc_account_token_get_all(self):
        ''' Get all service account token states using Resource APIs.
            Supported versions: CVP 2021.3.0 or newer and CVaaS.
            Returns:
                response (list): Returns a list of dictionaries that contains...
                Ex: [{'value': {'key': {'id': 'randomId'}, 'user': 'string',
                      'description': 'string','valid_until': '2022-11-02T06:58:53Z',
                      'created_by': 'string', 'last_used': None},
                      'time': '2022-05-03T15:38:53.725014447Z', 'type': 'INITIAL'}, ...]
        '''
        msg = 'Service Account Resource APIs are supported from 2021.3.0+.'
        if self.cvp_version_compare('>=', 14.0, msg):
            url = '/api/resources/serviceaccount/v1/Token/all'
            self.log.debug(f"v14 {url}")
            # Pull list of tokens out of data key of return for new resource APIs
            resp = self.clnt.get(url)
            tokens = []
            if "data" in resp:
                tokens = resp["data"]
            return tokens
        if self.cvp_version_compare('>=', 7.0, msg):
            url = '/api/v3/services/arista.serviceaccount.v1.TokenService/GetAll'
            self.log.debug(f"v7 {url}")
            return self.clnt.post(url)
        return None

    def svc_account_token_get_one(self, token_id):
        ''' Get a service account token's state using Resource APIs
            Supported versions: CVP 2021.3.0 or newer and CVaaS.
            Args:
                token_id (string): The id of the service account token.
            Returns:
                response (list): Returns a list of dict that contains...
                Ex: [{'value': {'key': {'id': 'randomId'}, 'user': 'string',
                      'description': 'string', 'valid_until': '2022-11-02T06:58:53Z',
                      'created_by': 'cvpadmin', 'last_used': None},
                      'time': '2022-05-03T15:38:53.725014447Z', 'type': 'INITIAL'}]
        '''
        msg = 'Service Account Resource APIs are supported from 2021.3.0+.'
        if self.cvp_version_compare('>=', 14.0, msg):
            endpoint = '/api/resources/serviceaccount/v1/Token'
            query_param = f"?key.id={token_id}"
            self.log.debug(f'v14 {endpoint + query_param}')
            return self.clnt.get(endpoint + query_param)
        if self.cvp_version_compare('>=', 7.0, msg):
            endpoint = '/api/v3/services/arista.serviceaccount.v1.TokenService/GetOne'
            payload = {"key": {"id": token_id}}
            self.log.debug(f'v7 {endpoint} {payload}')
            return self.clnt.post(endpoint, data=payload)
        return None

    def svc_account_token_delete(self, token_id):
        ''' Delete a service account token using Resource APIs.
            Supported versions: CVP 2021.3.0 or newer and CVaaS.
            Args:
                token_id (string): The id of the service account token.
            Returns:
                response (list): Returns a list of dict that contains the time of deletion:
                Ex: [{'key': {'id': '<token_id>'},
                      'time': '2022-07-26T15:29:03.687167871Z'}]
        '''
        msg = 'Service Account Resource APIs are supported from 2021.3.0+.'
        if self.cvp_version_compare('>=', 14.0, msg):
            endpoint = f'/api/resources/serviceaccount/v1/TokenConfig?key.id={token_id}'
            self.log.debug(f'v14 {endpoint}')
            return self.clnt.delete(endpoint)
        if self.cvp_version_compare('>=', 7.0, msg):
            endpoint = '/api/v3/services/arista.serviceaccount.v1.TokenConfigService/Delete'
            payload = {"key": {"id": token_id}}
            self.log.debug(f'v7 {endpoint} {payload}')
            return self.clnt.post(endpoint, data=payload)
        return None

    def svc_account_token_set(self, username, duration, description):
        ''' Create a service account token using Resource APIs.
            Supported versions: CVP 2021.3.0 or newer and CVaaS.
            Args:
                username (string): The service account username for which the token will be
                    generated.
                duration (string): The validity of the service account in seconds e.g.: "20000s"
                    The maximum value is 1 year in seconds e.g.: "31536000s"
                description (string): The description of the service account token.
            Returns:
                response (list): Returns a list of dict that contains the token:
                Ex: [{'value': {'key': {'id': '<userId>'}, 'user': 'ansible',
                      'description': 'cvprac test',
                      'valid_for': '550s', 'token': '<ey...>'}]
        '''
        msg = 'Service Account Resource APIs are supported from 2021.3.0+.'
        if self.cvp_version_compare('>=', 14.0, msg):
            payload = {
                'key': {
                    'id': ''
                },
                'description': description,
                'user': username,
                'validFor': duration,
                'token': ''
            }
            endpoint = '/api/resources/serviceaccount/v1/TokenConfig'
            self.log.debug(f'v14 {endpoint} {payload}')
            return self.clnt.post(endpoint, data=payload)
        if self.cvp_version_compare('>=', 7.0, msg):
            payload = {
                'value': {
                    'description': description,
                    'user': username,
                    'valid_for': duration
                }
            }
            endpoint = '/api/v3/services/arista.serviceaccount.v1.TokenConfigService/Set'
            self.log.debug(f'v7 {endpoint} {payload}')
            return self.clnt.post(endpoint, data=payload)
        return None

    def svc_account_get_all(self):
        ''' Get all service account states using Resource APIs.
            Supported versions: CVP 2021.3.0 or newer and CVaaS.
            Returns:
                response (list): Returns a list of dictionaries that contains...
                Ex: [{'value': {'key': {'name': 'ansible'}, 'status': 'ACCOUNT_STATUS_ENABLED',
                      'description': 'lab-tests', 'groups': {'values': ['network-admin']}},
                      'time': '2022-02-10T04:28:14.251684869Z', 'type': 'INITIAL'}, ...]
        '''
        msg = 'Service Account Resource APIs are supported from 2021.3.0+.'
        if self.cvp_version_compare('>=', 14.0, msg):
            endpoint = '/api/resources/serviceaccount/v1/Account/all'
            self.log.debug(f"v14 {endpoint}")
            # Pull list of accounts out of data key of return for new resource APIs
            resp = self.clnt.get(endpoint)
            svc_accounts = []
            if "data" in resp:
                svc_accounts = resp["data"]
            return svc_accounts
        if self.cvp_version_compare('>=', 7.0, msg):
            endpoint = '/api/v3/services/arista.serviceaccount.v1.AccountService/GetAll'
            self.log.debug(f"v7 {endpoint}")
            return self.clnt.post(endpoint)
        return None

    def svc_account_get_one(self, username):
        ''' Get a service account's state using Resource APIs
            Supported versions: CVP 2021.3.0 or newer and CVaaS.
            Args:
                username (string): The service account username.
            Returns:
                response (list): Returns a list of dict that contains...
                Ex: [{'value': {'key': {'name': 'ansible'}, 'status': 'ACCOUNT_STATUS_ENABLED',
                      'description': 'lab-tests', 'groups': {'values': ['network-admin']}},
                      'time': '2022-02-10T04:28:14.251684869Z'}]
        '''
        msg = 'Service Account Resource APIs are supported from 2021.3.0+.'
        if self.cvp_version_compare('>=', 14.0, msg):
            endpoint = '/api/resources/serviceaccount/v1/Account'
            query_param = f"?key.name={username}"
            self.log.debug(f"v14 {endpoint + query_param}")
            return self.clnt.get(endpoint + query_param)
        if self.cvp_version_compare('>=', 7.0, msg):
            endpoint = '/api/v3/services/arista.serviceaccount.v1.AccountService/GetOne'
            payload = {"key": {"name": username}}
            self.log.debug(f"v7 {endpoint} {payload}")
            return self.clnt.post(endpoint, data=payload)
        return None

    def _get_valid_role_ids(self, roles):
        ''' Helper function to validate and retrieve role IDs based on provided roles.
            Args:
                roles (list): The list of role names.
            Returns:
                role_ids (list): The list of role IDs.
        '''
        role_ids = []
        all_roles = self.get_roles()
        for role in all_roles['roles']:
            if role['key'] in roles or role['name'] in roles:
                role_ids.append(role['key'])
        if len(roles) != len(role_ids):
            self.log.warning(f"Not all provided roles {roles} are valid. "
                             f"Only using the found valid roles {role_ids}")
        return role_ids

    def svc_account_set(self, username, description, roles, status):
        ''' Create a service account using Resource APIs.
            Supported versions: CVP 2021.3.0 or newer and CVaaS.
            Args:
                username (string): The service account username.
                description (string): The description of the service account.
                roles (list): The list of role IDs. Default roles have a human readable name,
                    e.g.: 'network-admin', 'network-operator';
                    other roles will have the format of 'role_<unix_timestamp>',
                    e.g. 'role_1658850344592739349'.
                    cvprac automatically converts non-default role names to role IDs.
                status (enum): The status of the service account. Possible values:
                    0 or 'ACCOUNT_STATUS_UNSPECIFIED'
                    1 or 'ACCOUNT_STATUS_ENABLED'
                    2 or 'ACCOUNT_STATUS_DISABLED'
            Returns:
                response (list): Returns a list of dict that contains...
                Ex: [{'value': {'key': {'name': 'cvprac2'}, 'status': 'ACCOUNT_STATUS_ENABLED',
                      'description': 'testapi', 'groups': {'values':
                      ['network-admin', 'role_1658850344592739349']}},
                      'time': '2022-07-26T18:19:55.392173445Z'}]
        '''
        msg = 'Service Account Resource APIs are supported from 2021.3.0+.'
        # Retrieve valid role IDs
        role_ids = self._get_valid_role_ids(roles)
        if self.cvp_version_compare('>=', 14.0, msg):
            payload = {
                'description': description,
                'groups': {'values': role_ids},
                'key': {'name': username},
                'status': status
            }
            endpoint = '/api/resources/serviceaccount/v1/AccountConfig'
            self.log.debug(f"v14 {endpoint} {payload}")
            return self.clnt.post(endpoint, data=payload)
        if self.cvp_version_compare('>=', 7.0, msg):
            payload = {'value': {'description': description,
                                 'groups': {'values': role_ids},
                                 'key': {'name': username},
                                 'status': status}}
            endpoint = '/api/v3/services/arista.serviceaccount.v1.AccountConfigService/Set'
            self.log.debug(f"v7 {endpoint} {payload}")
            return self.clnt.post(endpoint, data=payload)
        return None

    def svc_account_delete(self, username):
        ''' Delete a service account using Resource APIs.
            Supported versions: CVP 2021.3.0 or newer and CVaaS.
            Args:
                username (string): The service account username.
            Returns:
                response (list): Returns a list of dict that contains the time of deletion:
                Ex: [{'key': {'name': 'cvprac2'},
                      'time': '2022-07-26T18:26:53.637425846Z'}]
        '''
        msg = 'Service Account Resource APIs are supported from 2021.3.0+.'
        if self.cvp_version_compare('>=', 14.0, msg):
            endpoint = f'/api/resources/serviceaccount/v1/AccountConfig?key.name={username}'
            self.log.debug(f"v14 {endpoint}")
            return self.clnt.delete(endpoint)
        if self.cvp_version_compare('>=', 7.0, msg):
            payload = {"key": {"name": username}}
            endpoint = '/api/v3/services/arista.serviceaccount.v1.AccountConfigService/Delete'
            self.log.debug(f"v7 {endpoint} {payload}")
            return self.clnt.post(endpoint, data=payload)
        return None

    def svc_account_delete_expired_tokens(self):
        ''' Delete all service account tokens using Resource APIs.
            Supported versions: CVP 2021.3.0 or newer and CVaaS.
            Returns:
                response (list): Returns a list of dict that contains the list of tokens
                that were deleted:
                Ex: [{'value': {'key': {'id': '091f48a2808'},'user': 'cvprac3',
                'description': 'cvprac test', 'valid_until': '2022-07-26T18:31:18Z',
                'created_by': 'cvpadmin', 'last_used': None},
                'time': '2022-07-26T18:30:28.022504853Z','type': 'INITIAL'},
                {'value': {'key': {'id': '2f6325d9c'},...]
        '''
        msg = 'Service Account Resource APIs are supported from 2021.3.0+.'
        valid_until_format = "valid_until"
        resource_api_schema = False
        if self.cvp_version_compare('>=', 14.0, msg):
            resource_api_schema = True
            valid_until_format = "validUntil"
        tokens = self.svc_account_token_get_all()
        expired_tokens = []
        for tok in tokens:
            if resource_api_schema:
                token_data = tok['result']['value']
            else:
                token_data = tok['value']
            if (datetime.strptime(token_data[valid_until_format], "%Y-%m-%dT%H:%M:%SZ") <
                    datetime.utcnow()):
                self.svc_account_token_delete(token_data['key']['id'])
                expired_tokens.append(tok)
        return expired_tokens

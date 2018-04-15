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
import urllib
from cvprac.cvp_client_errors import CvpApiError


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
        return self.clnt.get('/cvpInfo/getCvpInfo.do',
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
        self.log.debug('get_log_by_id: task_id: %s' % task_id)
        return self.clnt.get('/task/getLogsById.do?id=%s&queryparam='
                             '&startIndex=%d&endIndex=%d' %
                             (task_id, start, end),
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
        self.clnt.post('/task/cancelTask.do', data=data,
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
                             % urllib.quote_plus(name),
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
        data = self.clnt.get('/inventory/getInventory.do?'
                             'queryparam=%s&startIndex=%d&endIndex=%d' %
                             (urllib.quote_plus(query), start, end),
                             timeout=self.request_timeout)
        return data['netElementList']

    def add_device_to_inventory(self, device_ip, parent_name, parent_key):
        ''' Add the device to the specified parent container.

            Args:
                device_ip (str): ip address of device we are adding
                parent_name (str): Parent container name
                parent_key (str): Parent container key
        '''
        self.log.debug('add_device_to_inventory: called')
        data = {'data': [
            {
                'containerName' : parent_name,
                'containerId' : parent_key,
                'containerType' : 'Existing',
                'ipAddress' : device_ip,
                'containerList' : []
            }]}
        self.clnt.post('/inventory/add/addToInventory.do?'
                       'startIndex=0&endIndex=0', data=data,
                       timeout=self.request_timeout)

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
        data = {"key" : device_mac,
                "ipAddress" : device_ip,
                "userName" : username,
                "password" : password}
        self.clnt.post('/inventory/add/retryAddDeviceToInventory.do?'
                       'startIndex=0&endIndex=0',
                       data=data,
                       timeout=self.request_timeout)

    def delete_device(self, device_mac):
        '''Delete the device and its pending tasks from Cvp inventory

            Args:
                device_mac (str): mac address of device we are deleting
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
            Returns:
                data (dict): Contains success or failure message
        '''
        self.log.debug('delete_devices: called')
        data = {'data': device_macs}
        return self.clnt.post('/inventory/deleteDevices.do?', data=data,
                              timeout=self.request_timeout)

    def get_non_connected_device_count(self):
        '''Returns number of devices not accessible/connected in the temporary
           inventory.

            Returns:
                data (int): Number of temporary inventory devices not
                            accessible/connected
        '''
        self.log.debug('get_non_connected_device_count: called')
        data = self.clnt.get('/inventory/add/getNonConnectedDeviceCount.do',
                             timeout=self.request_timeout)
        return data['data']

    def save_inventory(self):
        '''Saves Cvp inventory state
        '''
        self.log.debug('save_inventory: called')
        return self.clnt.post('/inventory/add/saveInventory.do',
                              timeout=self.request_timeout)

    def get_devices_in_container(self, name):
        ''' Returns a dict of the devices under the named container.

            Args:
                name (str): The name of the container to get devices from
        '''
        self.log.debug('get_devices_in_container: called')
        devices = []
        container = self.get_container_by_name(name)
        if container:
            data = self.clnt.get('/inventory/getInventory.do?'
                                 'queryparam=%s&startIndex=0&'
                                 'endIndex=0' % urllib.quote_plus(name),
                                 timeout=self.request_timeout)
            for device in data['netElementList']:
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
        self.log.debug('get_device_from_name: fqdn: %s' % fqdn)
        data = self.clnt.get('/inventory/getInventory.do?'
                             'queryparam=%s&startIndex=0&endIndex=0'
                             % urllib.quote_plus(fqdn),
                             timeout=self.request_timeout)
        if len(data['netElementList']) > 0:
            for netelement in data['netElementList']:
                if netelement['fqdn'] == fqdn:
                    device = netelement
                    break
            else:
                device = {}
        else:
            device = {}
        return device

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
        return self.clnt.get('/inventory/add/searchContainers.do?'
                             'startIndex=%d&endIndex=%d' % (start, end))

    def get_container_by_name(self, name):
        ''' Returns a container that exactly matches the name.

            Args:
                name (str): String to search for in container names.

            Returns:
                container (dict): Container info in dictionary format or None
        '''
        self.log.debug('Get info for container %s' % name)
        conts = self.clnt.get('/provisioning/searchTopology.do?queryParam=%s'
                              '&startIndex=0&endIndex=0'
                              % urllib.quote_plus(name))
        if conts['total'] > 0 and conts['containerList']:
            for cont in conts['containerList']:
                if cont['name'] == name:
                    return cont
        return None

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
        data = self.clnt.get('/provisioning/getConfigletsByNetElementId.do?'
                             'netElementId=%s&queryParam=&startIndex=%d&'
                             'endIndex=%d' % (mac, start, end),
                             timeout=self.request_timeout)
        return data['configletList']

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
                             % urllib.quote_plus(name),
                             timeout=self.request_timeout)
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

    def update_configlet(self, config, key, name):
        ''' Update a configlet.

            Args:
                config (str): Switch config statements
                key (str): Configlet key
                name (str): Configlet name

            Returns:
                data (dict): Contains success or failure message
        '''
        self.log.debug('update_configlet: config: %s key: %s name: %s' %
                       (config, key, name))

        # Update the configlet
        body = {'config': config, 'key': key, 'name': name}
        return self.clnt.post('/configlet/updateConfiglet.do', data=body,
                              timeout=self.request_timeout)

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
        if operation is 'add':
            data['data'][0]['toId'] = parent_key
            data['data'][0]['toName'] = parent_name
        elif operation is 'delete':
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
        return self._container_op(container_name, container_key, parent_name,
                                  parent_key, 'delete')

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
        info = '%s moving device %s to container %s' % (app_name,
                                                        device['fqdn'],
                                                        container['name'])
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
                             % (urllib.quote_plus(query), start, end),
                             timeout=self.request_timeout)
        return data

    def check_compliance(self, node_key, node_type):
        ''' Check that a device is in compliance, that is the configlets
            applied to the device match the devices running configuration.

            Args:
                node_key (str): The device key.
                node_type (str): The device type.

            Returns:
                response (dict): A dict that contains the results of the
                    compliance check.
        '''
        self.log.debug('check_compliance: node_key: %s node_type: %s' %
                       (node_key, node_type))
        data = {'nodeId': node_key, 'nodeType': node_type}
        return self.clnt.post('/provisioning/checkCompliance.do', data=data,
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
                                  % urllib.quote_plus(name),
                                  timeout=self.request_timeout)
        except CvpApiError as error:
            # Catch an invalid task_id error and return None
            if 'Entity does not exist' in str(error):
                self.log.debug('Bundle with name %s does not exist' % name)
                return None
            raise error
        return image

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
        data = {'data': [{'info': info,
                          'infoPreview': info,
                          'note': '',
                          'action': 'associate',
                          'nodeType': 'imagebundle',
                          'nodeId': image['id'],
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
                          'ignoreNodeId': image['id'],
                          'ignoreNodeName': image['name'],
                          'childTasks': [],
                          'parentTask': ''}]}
        self._add_temp_action(data)
        return self._save_topology_v2([])

    def deploy_device(self, device, container, configlets=None, image=None):
        ''' Move a device from the undefined container to a target container.
            Optionally apply device-specific configlets and an image.

            Args:
                device (dict): unique key for the device
                container (str): name of container to move device to
                configlets (list): list of dicts with configlet key/name pairs
                image (str): name of image to apply to device

            Returns:
                response (dict): A dict that contains a status and a list of
                    task ids created (if any).

                    Ex: {u'data': {u'status': u'success', u'taskIds': [u'32']}}
        '''
        info = 'Deploy device %s to container %s' % (device['fqdn'], container)
        self.log.debug(info)
        container_info = self.get_container_by_name(container)
        # Add action for moving device to specified container
        self.move_device_to_container('Deploy device', device, container_info,
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
        if image:
            image_info = self.get_image_bundle_by_name(image)
            self.apply_image_to_device(image_info, device, create_task=False)

        return self._save_topology_v2([])

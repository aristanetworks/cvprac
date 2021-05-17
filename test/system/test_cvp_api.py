# pylint: disable=wrong-import-position
# pylint: disable=too-many-lines
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

''' System test for the CvpApi class

    Requirements for CVP Node:
    1) Test has dedicated access to the CVP node.
    2) Contains at least one device in a container.
    3) Container or device has at least one configlet applied.
    4) Device has a user account and password that matches the CVP username
       and password.  If device does not have correct username and/or password
       then the tests that execute tasks will fail with the following error:

         AssertionError: Execution for task id 220 failed

       and in the test log is the error:

         Failure response received from the netElement : ' Unauthorized User '
'''
import os
import re
import shutil
import sys
import time
import unittest
from pprint import pprint
from requests.exceptions import Timeout

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from cvprac.cvp_client import CvpClient
from cvprac.cvp_client_errors import CvpApiError

sys.path.append(os.path.join(os.path.dirname(__file__), '../lib'))
from systestlib import DutSystemTest


class TestCvpClient(DutSystemTest):
    ''' Test cases for the CvpClient class.
    '''
    # pylint: disable=too-many-public-methods
    # pylint: disable=invalid-name
    def setUp(self):
        ''' Instantiate the CvpClient class and connect to the CVP node.
            Log messages to the /tmp/TestCvpClient.log
        '''
        super(TestCvpClient, self).setUp()
        self.clnt = CvpClient(filename='/tmp/TestCvpClient.log')
        self.assertIsNotNone(self.clnt)
        self.assertIsNone(self.clnt.last_used_node)
        dut = self.duts[0]
        cert = False
        if 'cert' in dut:
            cert = dut['cert']
        self.clnt.connect([dut['node']], dut['username'], dut['password'], 10,
                          cert=cert)
        self.api = self.clnt.api
        self.assertIsNotNone(self.api)

        # Verify that there is at least one device in the inventory
        err_msg = 'CVP node must contain at least one device'
        result = self.api.get_inventory()
        self.assertIsNotNone(result)
        self.assertGreaterEqual(len(result), 1, msg=err_msg)
        self.device = result[0]

        # Get the container for the device on the list and
        # use that container as the parent container.
        result = self.api.search_topology(self.device['fqdn'])
        self.assertIsNotNone(result)
        dev_container = result['netElementContainerList']
        self.assertGreaterEqual(len(dev_container), 1)
        info = dev_container[0]
        result = self.api.search_topology(info['containerName'])
        self.assertIsNotNone(result)
        self.container = result['containerList'][0]

        # Get the configlets assigned to the device.  There must be at least 1.
        err_msg = 'CVP node device must have at least one configlet assigned'
        key = info['netElementKey']
        result = self.api.get_configlets_by_device_id(key)
        self.assertGreaterEqual(len(result), 1, msg=err_msg)
        self.dev_configlets = result

    def tearDown(self):
        ''' Destroy the CvpClient class.
        '''
        super(TestCvpClient, self).tearDown()
        self.api = None
        self.clnt = None

    def _get_next_task_id(self):
        ''' Return the next task id.

            Returns:
                task_id (str): Task ID
        '''
        # Get all the tasks and the task id of the next task created is
        # the length + 1.
        results = self.api.get_tasks()
        self.assertIsNotNone(results)
        return str(int(results['total']) + 1)

    def _create_task(self):
        ''' Create a task by making a simple change to a configlet assigned
            to the device.

            Returns:
                (task_id, config)
                task_id (str): Task ID
                config (str): Previous configlets contents
        '''
        task_id = self._get_next_task_id()

        # Update the lldp time in the first configlet in the list.
        configlet = None
        for conf in self.dev_configlets:
            if conf['netElementCount'] == 1:
                configlet = conf
                break
        if configlet is None:
            configlet = self.dev_configlets[0]

        config = configlet['config']
        org_config = config

        match = re.match(r'lldp timer (\d+)', config)
        if match is not None:
            value = int(match.group(1)) + 1
            repl = 'lldp timer %d' % value
            config = re.sub(match.group(0), repl, config)
        else:
            value = 13
            config = ('lldp timer %d\n' % value) + config
        configlet['config'] = config

        # Updating the configlet will cause a task to be created to apply
        # the change to the device.
        self.api.update_configlet(config, configlet['key'], configlet['name'])

        # Wait 30 seconds for task to get created
        cnt = 30
        if self.clnt.apiversion is None:
            self.api.get_cvp_info()
        if self.clnt.apiversion >= 2.0:
            # Increase timeout by 30 sec for CVP 2018.2 and beyond
            cnt += 30
        while cnt > 0:
            time.sleep(1)
            result = self.api.get_task_by_id(task_id)
            if result is not None:
                break
            cnt -= 1
        err_msg = 'Timeout waiting for task id %s to be created' % task_id
        self.assertGreater(cnt, 0, msg=err_msg)

        return task_id, org_config

    def test_api_get_cvp_info(self):
        ''' Verify get_cvp_info and verify setting of client last_used_node
            parameter
        '''
        result = self.api.get_cvp_info()
        self.assertIsNotNone(result)
        self.assertIn('version', result)
        self.assertIn(self.clnt.last_used_node, self.clnt.url_prefix)
        self.assertEqual(self.clnt.version, result['version'])
        self.assertIsNotNone(self.clnt.apiversion)

    def test_api_user_operations(self):
        ''' Verify get_user, add_user and update_user
        '''
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches
        dut = self.duts[0]
        # Test Get User
        result = self.api.get_user(dut['username'])
        self.assertIsNotNone(result)
        self.assertIn('user', result)
        self.assertIn('userId', result['user'])
        self.assertEqual(result['user']['userId'], 'cvpadmin')
        self.assertIn('userStatus', result['user'])
        self.assertIsNotNone(result['roles'])

        # Check if test user exists
        try:
            result = self.api.get_user('test_cvp_user')
            self.assertIsNotNone(result)
            self.assertIn('user', result)
            self.assertIn('userId', result['user'])
            self.assertEqual(result['user']['userId'], 'test_cvp_user')
            initial_user_status = result['user']['userStatus']
            initial_user_email = result['user']['email']
            initial_user_type = result['user']['userType']
            initial_first_name = result['user']['firstName']
            initial_last_name = result['user']['lastName']
            initial_user_role = result['roles'][0]
        except CvpApiError:
            # Test Create User
            result = self.api.add_user('test_cvp_user', 'test_cvp_pass',
                                       'network-admin', 'Enabled', 'Net',
                                       'Op', 'test_cvp_pass@email.com',
                                       'Local')
            self.assertIsNotNone(result)
            self.assertIn('data', result)
            self.assertIn('userId', result['data'])
            self.assertEqual(result['data']['userId'], 'test_cvp_user')
            self.assertIn('userStatus', result['data'])
            self.assertEqual(result['data']['userStatus'], 'Enabled')

            # Check created user
            result = self.api.get_user('test_cvp_user')
            self.assertIsNotNone(result)
            self.assertIn('user', result)
            self.assertIn('userId', result['user'])
            self.assertEqual(result['user']['userId'], 'test_cvp_user')
            self.assertIn('userStatus', result['user'])
            self.assertEqual(result['user']['userStatus'], 'Enabled')
            self.assertIn('userType', result['user'])
            self.assertEqual(result['user']['userType'], 'Local')
            self.assertIsNotNone(result['roles'])
            self.assertEqual(result['roles'], ['network-admin'])
            initial_user_status = result['user']['userStatus']
            initial_user_role = result['roles'][0]
            initial_user_type = result['user']['userType']
            initial_user_email = result['user']['email']
            initial_first_name = result['user']['firstName']
            initial_last_name = result['user']['lastName']

        if initial_user_status == 'Enabled':
            update_user_status = 'Disabled'
        else:
            update_user_status = 'Enabled'

        if initial_user_role == 'network-admin':
            update_user_role = 'network-operator'
        else:
            update_user_role = 'network-admin'

        if initial_user_type == 'Local':
            update_user_type = 'TACACS'
        else:
            update_user_type = 'Local'

        if initial_user_email == 'test_cvp_pass@email.com':
            update_user_email = 'test_cvp_pass2@email.com'
        else:
            update_user_email = 'test_cvp_pass@email.com'

        if initial_first_name == "Net":
            update_first_name = "Network"
        else:
            update_first_name = "Net"

        if initial_last_name == "Op":
            update_last_name = "Operator"
        else:
            update_last_name = "Op"

        # Test Update User
        result = self.api.update_user('test_cvp_user', 'password',
                                      update_user_role, update_user_status,
                                      update_first_name, update_last_name,
                                      update_user_email, update_user_type)
        self.assertIsNotNone(result)
        self.assertIn('data', result)
        self.assertEqual(result['data'], 'success')
        result = self.api.get_user('test_cvp_user')
        self.assertIsNotNone(result)
        self.assertIn('user', result)
        self.assertIn('userId', result['user'])
        self.assertEqual(result['user']['userId'], 'test_cvp_user')
        self.assertIn('userStatus', result['user'])
        self.assertEqual(result['user']['userStatus'], update_user_status)
        self.assertIn('userType', result['user'])
        self.assertEqual(result['user']['userType'], update_user_type)
        self.assertIn('email', result['user'])
        self.assertEqual(result['user']['email'], update_user_email)
        self.assertIsNotNone(result['roles'])
        self.assertEqual(result['roles'], [update_user_role])

        # Test Delete User
        result = self.api.delete_user('test_cvp_user')
        self.assertIsNotNone(result)
        self.assertIn('data', result)
        self.assertEqual(result['data'], 'success')

        # Verify the user successfully deleted and doesn't exist
        with self.assertRaises(CvpApiError):
            self.api.get_user('test_cvp_user')

    def test_api_check_compliance(self):
        ''' Verify check_compliance
        '''
        key = self.device['key']
        ntype = self.device['type']
        result = self.api.check_compliance(key, ntype)
        self.assertEqual(result['complianceCode'], '0000')
        self.assertEqual(result['complianceIndication'], 'NONE')

    def test_api_task_operations(self):
        ''' Verify get_task_by_id, get_task_by_status, add_note_to_task,
             get_logs_by_id, and cancel_task
        '''
        (task_id, org_config) = self._create_task()

        # Test get_task_by_id
        result = self.api.get_task_by_id(task_id)
        self.assertIsNotNone(result)
        self.assertEqual(result['workOrderId'], task_id)

        # Test get_task_by_status
        results = self.api.get_tasks_by_status('PENDING')
        # More than one task may be returned.
        found = False
        for result in results:
            actual_task_id = result['workOrderId']
            if actual_task_id == task_id:
                found = True
                break
        err_msg = 'Task id: %s not in list of PENDING tasks' % task_id
        self.assertTrue(found, msg=err_msg)

        # Test add_note_to_task
        note = 'Test Generated'
        self.api.add_note_to_task(task_id, note)

        # Verify task operations
        result = self.api.get_task_by_id(task_id)
        self.assertIsNotNone(result)
        self.assertEqual(result['note'], note)
        self.assertEqual(result['workOrderUserDefinedStatus'], 'Pending')

        result = self.api.check_compliance(self.device['key'],
                                           self.device['type'])
        self.assertEqual(result['complianceCode'], '0001')

        # Test cancel_task
        self.api.cancel_task(task_id)
        time.sleep(1)
        result = self.api.get_task_by_id(task_id)
        self.assertIsNotNone(result)
        self.assertEqual(result['workOrderUserDefinedStatus'], 'Cancelled')

        result = self.api.check_compliance(self.device['key'],
                                           self.device['type'])
        self.assertEqual(result['complianceCode'], '0001')

        # Get the task logs
        result = self.api.get_logs_by_id(task_id)
        self.assertIsNotNone(result)

        result = self.api.check_compliance(self.device['key'],
                                           self.device['type'])
        self.assertEqual(result['complianceCode'], '0001')

        # Restore the configlet to what it was before the task was created.
        task_id = self._get_next_task_id()
        configlet = None
        for conf in self.dev_configlets:
            if conf['netElementCount'] == 1:
                configlet = conf
                break
        if configlet is None:
            configlet = self.dev_configlets[0]
        self.api.update_configlet(org_config, configlet['key'],
                                  configlet['name'])
        time.sleep(2)
        # Cancel task
        self.api.cancel_task(task_id)

        # Check compliance
        self.test_api_check_compliance()

    def test_api_get_logs(self):
        ''' Verify get_logs_by_id and get_audit_logs_by_id
        '''
        # pylint: disable=too-many-branches
        if not self.clnt.apiversion:
            self.api.get_cvp_info()
        if self.clnt.apiversion < 5.0:
            tasks = self.api.get_tasks()
            for task in tasks['data']:
                if 'workOrderId' in task:
                    result = self.api.get_logs_by_id(task['workOrderId'])
                    self.assertIsNotNone(result)
                    if 'data' in result:
                        self.assertIsNotNone(result['data'])
                    break
        else:
            tasks = self.api.get_tasks()
            task_cc = None
            task_no_cc = None
            for task in tasks['data']:
                if 'ccIdV2' in task:
                    if task['ccIdV2'] == '':
                        task_no_cc = task
                    else:
                        task_cc = task
            if task_cc:
                result = self.api.get_logs_by_id(task_cc['workOrderId'])
                self.assertIsNotNone(result)
                if 'data' in result:
                    self.assertIsNotNone(result['data'])
            if task_no_cc:
                result = self.api.get_logs_by_id(task_cc['workOrderId'])
                self.assertIsNotNone(result)
                if 'data' in result:
                    self.assertIsNotNone(result['data'])
                result = self.api.get_audit_logs_by_id(task_cc['ccIdV2'],
                                                       task_cc['stageId'],
                                                       75)
                self.assertIsNotNone(result)
                if 'data' in result:
                    self.assertIsNotNone(result['data'])

    def test_api_validate_config(self):
        ''' Verify valid config returns True
        '''
        config = 'interface ethernet1\n description test'
        result = self.api.validate_config(self.device['key'], config)
        self.assertEqual(result, True)

    def test_api_validate_config_error(self):
        ''' Verify an invalid config returns False
        '''
        config = 'interface ethernet1\n typocommand test'
        result = self.api.validate_config(self.device['key'], config)
        self.assertEqual(result, False)

    def test_api_get_task_by_id_bad(self):
        ''' Verify get_task_by_id with bad task id
        '''
        result = self.api.get_task_by_id(10000000)
        self.assertIsNone(result)

    def test_api_get_task_by_id_fmt_bad(self):
        ''' Verify get_task_by_id with bad task id
        '''
        result = self.api.get_task_by_id('BOGUS')
        self.assertIsNone(result)

    def test_api_get_tasks_by_s_bad(self):
        ''' Verify get_tasks_by_status
        '''
        result = self.api.get_tasks_by_status('BOGUS')
        self.assertIsNotNone(result)

    def test_api_search_configlets(self):
        ''' Verify search_configlets
        '''
        result = self.api.search_configlets('TelemetryBuilder')

        # Make sure at least 1 configlet has been returned as noted
        # by the 'total' key, and that the data is a list.
        self.assertIn('total', result)
        self.assertGreater(result['total'], 0)
        self.assertIn('data', result)
        self.assertIsInstance(result['data'], list)

    def test_api_get_configlets(self):
        ''' Verify get_configlets
        '''
        result = self.api.get_configlets()

        # Format the configlet lists into name keyed dictionaries
        dev_cfglts = {}
        for cfglt in self.dev_configlets:
            dev_cfglts.update({cfglt['name']: cfglt})

        rslt_cfglts = {}
        for cfglt in result['data']:
            rslt_cfglts.update({cfglt['name']: cfglt})

        # Make sure the device configlets are all returned by the
        # get_configlets call
        for cfglt_name in dev_cfglts:
            self.assertIn(cfglt_name, rslt_cfglts)
            self.assertDictEqual(dev_cfglts[cfglt_name],
                                 rslt_cfglts[cfglt_name])

    def test_api_get_configlets_and_mappers(self):
        ''' Verify get_configlets_and_mappers
        '''
        result = self.api.get_configlets_and_mappers()
        self.assertIsNotNone(result)
        self.assertIn('data', result)
        data = result['data']
        self.assertIn('configlets', data)
        self.assertIn('configletBuilders', data)
        self.assertIn('generatedConfigletMappers', data)
        self.assertIn('configletMappers', data)
        configlets = data['configlets']
        self.assertIsNotNone(configlets)
        self.assertGreater(len(configlets), 0)
        configlet_mappers = data['configletMappers']
        self.assertIsNotNone(configlet_mappers)
        self.assertGreater(len(configlet_mappers), 0)

    def test_api_get_configlet_builder(self):
        ''' Verify get_configlet_builder
        '''
        try:
            # Configlet Builder for pre 2019.x
            cfglt = self.api.get_configlet_by_name('SYS_TelemetryBuilderV2')
        except CvpApiError as e:
            if 'Entity does not exist' in e.msg:
                # Configlet Builder for 2019.x
                try:
                    cfglt = self.api.get_configlet_by_name(
                        'SYS_TelemetryBuilderV3')
                except CvpApiError as e:
                    if 'Entity does not exist' in e.msg:
                        # Configlet Builder for 2021.x
                        cfglt = self.api.get_configlet_by_name(
                            'SYS_TelemetryBuilderV4')
                    else:
                        raise
            else:
                raise
        result = self.api.get_configlet_builder(cfglt['key'])

        # Verify the following keys and types are
        # returned by the request
        exp_data = {
            u'isAssigned': bool,
            u'formList': list,
            u'main_script': dict,
        }
        # Handle unicode type for Python 2 vs Python 3
        if sys.version_info.major < 3:
            exp_data[u'name'] = (unicode, str)
        else:
            exp_data[u'name'] = str
        for key in exp_data:
            self.assertIn(key, result['data'])
            self.assertIsInstance(result['data'][key], exp_data[key])

    def test_api_get_configlet_by_name(self):
        ''' Verify get_configlet_by_name
        '''
        configlet = None
        for conf in self.dev_configlets:
            if conf['netElementCount'] == 1:
                configlet = conf
                break
        if configlet is None:
            configlet = self.dev_configlets[0]
        result = self.api.get_configlet_by_name(configlet['name'])
        self.assertIsNotNone(result)
        self.assertEqual(result['key'], configlet['key'])

    def test_api_get_configlets_by_container_id(self):
        ''' Verify get_configlets_by_container_id
        '''
        result = self.api.get_configlets_by_container_id(
            self.container['key'])

        # Verify the following keys and types are returned by the request
        exp_data = {
            'configletList': list,
            'total': int,
            'configletMapper': dict,
        }
        for key in exp_data:
            self.assertIn(key, result)
            self.assertIsInstance(result[key], exp_data[key])

    def test_api_get_configlets_by_netelement_id(self):
        ''' Verify get_configlets_by_netelement_id
        '''
        result = self.api.get_configlets_by_netelement_id(self.device['key'])

        # Verify the following keys and types are returned by the request
        exp_data = {
            'configletList': list,
            'total': int,
            'configletMapper': dict,
        }
        for key in exp_data:
            self.assertIn(key, result)
            self.assertIsInstance(result[key], exp_data[key])

    def test_api_get_applied_devices(self):
        ''' Verify get_applied_devices
        '''
        for cfglt in self.dev_configlets:
            result = self.api.get_applied_devices(cfglt['name'])

            # Verify the following keys and types are
            # returned by the request
            exp_data = {
                'data': list,
                'total': int,
            }
            for key in exp_data:
                self.assertIn(key, result)
                self.assertIsInstance(result[key], exp_data[key])

    def test_api_get_applied_containers(self):
        ''' Verify get_applied_containers
        '''
        for cfglt in self.dev_configlets:
            result = self.api.get_applied_containers(cfglt['name'])

            # Verify the following keys and types are
            # returned by the request
            exp_data = {
                'data': list,
                'total': int,
            }
            for key in exp_data:
                self.assertIn(key, result)
                self.assertIsInstance(result[key], exp_data[key])

    def test_api_get_configlet_history(self):
        ''' Verify get_configlet_history
        '''
        key = None
        for conf in self.dev_configlets:
            if conf['netElementCount'] == 1:
                key = conf['key']
                break
        if key is None:
            key = self.dev_configlets[0]['key']
        result = self.api.get_configlet_history(key)
        self.assertIsNotNone(result)

    def test_api_get_device_by_name(self):
        ''' Verify get_device_by_name
        '''
        result = self.api.get_device_by_name(self.device['fqdn'])
        self.assertIsNotNone(result)
        for key in result:
            self.assertIn(key, self.device)
            # Some differences in result values between inventory
            # and searchTopology. For example "no" vs "False" or
            # "false" vs "False"
            # self.assertEqual(result[key], self.device[key])

    def test_api_get_device_configuration(self):
        ''' Verify get_device_configuration
        '''
        result = self.api.get_device_configuration(self.device['key'])
        self.assertIsNotNone(result)
        config_lines = result.splitlines()
        for line in config_lines:
            if 'hostname' in line:
                self.assertEqual(line, 'hostname %s' % self.device['fqdn'])

    def test_api_get_device_by_name_bad(self):
        ''' Verify get_device_by_name with bad fqdn
        '''
        result = self.api.get_device_by_name('bogus_host_name')
        self.assertIsNotNone(result)
        self.assertEqual(result, {})

    def test_api_get_device_by_name_substring(self):
        ''' Verify get_device_by_name with partial fqdn returns nothing
        '''
        result = self.api.get_device_by_name(self.device['fqdn'][1:])
        self.assertIsNotNone(result)
        self.assertEqual(result, {})

    def test_api_get_device_by_mac(self):
        ''' Verify get_device_by_mac with partial fqdn returns nothing
        '''
        result = self.api.get_device_by_mac(self.device['systemMacAddress'])
        self.assertIsNotNone(result)
        self.assertEqual(result['systemMacAddress'],
                         self.device['systemMacAddress'])

    def test_api_get_device_by_mac_bad(self):
        ''' Verify get_device_by_mac with bad mac
        '''
        result = self.api.get_device_by_mac('bogus_mac')
        self.assertIsNotNone(result)
        self.assertEqual(result, {})

    def _create_configlet_builder(self, name, config, draft, form=None):
        # Delete configlet builder in case it was left by a previous test run
        try:
            result = self.api.get_configlet_by_name(name)
            self.api.delete_configlet(name, result['key'])
        except CvpApiError:
            pass

        # Add the configlet builder
        key = self.api.add_configlet_builder(name, config, draft, form)
        self.assertIsNotNone(key)
        return key

    def test_api_add_update_delete_configlet_builder(self):
        ''' Verify add_configlet_builder and delete_configlet
            Will test a configlet builder with form data and without
        '''
        name = 'test_configlet_builder'
        name2 = 'test_configlet_builder_noform'
        config = ("from cvplibrary import Form\n\n" +
                  "dev_host = Form.getFieldById('txt_hostname').getValue()" +
                  "\n\nprint('hostname {0}'.format(dev_host))")

        draft = False
        forms = [{
            'fieldId': 'txt_hostname',
            'fieldLabel': 'Hostname',
            'type': 'Text box',
            'validation': {
                'mandatory': False
            },
            'helpText': 'Hostname for the device'
        }]

        # Add the configlet builder
        key = self._create_configlet_builder(name, config, draft, forms)
        key2 = self._create_configlet_builder(name2, config, draft)

        # Verify the configlet builder was added
        # Form data
        result = self.api.get_configlet_by_name(name)
        self.assertIsNotNone(result)
        self.assertEqual(result['name'], name)
        # self.assertEqual(result['config'], config)
        self.assertEqual(result['type'], 'Builder')
        self.assertEqual(result['key'], key)

        # No Form data
        result2 = self.api.get_configlet_by_name(name2)
        self.assertIsNotNone(result2)
        self.assertEqual(result2['name'], name2)
        # self.assertIn("dev_host", result2['config'])
        # self.assertNotIn("device_hostname", result2['config'])
        self.assertEqual(result2['type'], 'Builder')
        self.assertEqual(result2['key'], key2)

        # Update No Form data
        config2 = ("from cvplibrary import Form\n\n" +
                   "device_hostname = Form.getFieldById" +
                   "('txt_hostname').getValue()" +
                   "\n\nprint('Hostname {0}'.format(device_hostname))")
        update_result2 = self.api.update_configlet_builder(name2, key2,
                                                           config2)
        self.assertIsNotNone(update_result2)
        update_info2 = self.api.get_configlet_by_name(name2)
        self.assertIsNotNone(update_info2)
        self.assertEqual(update_info2['name'], name2)
        # self.assertIn("device_hostname", update_info2['config'])
        # self.assertNotIn("dev_host", update_info2['config'])
        self.assertEqual(update_info2['type'], 'Builder')
        self.assertEqual(update_info2['key'], key2)

        # Delete the configlet builder
        self.api.delete_configlet(name, key)
        self.api.delete_configlet(name2, key2)

        # Verify the configlet builder was deleted
        with self.assertRaises(CvpApiError):
            self.api.get_configlet_by_name(name)

        with self.assertRaises(CvpApiError):
            self.api.get_configlet_by_name(name2)

    def test_api_update_reconcile_configlet(self):
        ''' Verify update_reconcile_configlet
        '''
        rec_configlet_name = 'RECONCILE_{}'.format(self.device['ipAddress'])
        # Verify this reconcile configlet doesn't already exist
        with self.assertRaises(CvpApiError):
            self.api.get_configlet_by_name(rec_configlet_name)
        config = 'lldp timer 25'
        # create reconcile configlet
        result = self.api.update_reconcile_configlet(self.device['key'],
                                                     config, "",
                                                     rec_configlet_name,
                                                     reconciled=True)
        self.assertIsNotNone(result)
        # Verify this reconcile configlet exists
        new_rec_configlet = self.api.get_configlet_by_name(rec_configlet_name)
        self.assertIsNotNone(new_rec_configlet)
        self.assertEqual(new_rec_configlet['config'], 'lldp timer 25\n')
        self.api.delete_configlet(new_rec_configlet['name'],
                                  new_rec_configlet['key'])
        # Verify this reconcile configlet has been removed
        with self.assertRaises(CvpApiError):
            self.api.get_configlet_by_name(rec_configlet_name)

    def test_api_get_device_image_info(self):
        ''' Verify get_device_image_info
        '''
        result = self.api.get_device_image_info(self.device['key'])
        self.assertIsNotNone(result)
        self.assertIn('bundleName', result)

    def test_api_get_device_image_info_no_device(self):
        ''' Verify get_device_image_info returns none when no device with MAC
        '''
        result = self.api.get_device_image_info("NOPE")
        self.assertIsNone(result)

    def _create_configlet(self, name, config):
        # Delete the configlet in case it was left by previous test run
        try:
            result = self.api.get_configlet_by_name(name)
            self.api.delete_configlet(name, result['key'])
        except CvpApiError:
            pass

        # Add the configlet
        key = self.api.add_configlet(name, config)
        self.assertIsNotNone(key)
        return key

    def test_api_add_delete_configlet(self):
        ''' Verify add_configlet and delete_configlet
        '''
        name = 'test_configlet'
        config = 'lldp timer 9'

        # Add the configlet
        key = self._create_configlet(name, config)

        # Verify configlet was added
        result = self.api.get_configlet_by_name(name)
        self.assertIsNotNone(result)
        self.assertEqual(result['name'], name)
        self.assertEqual(result['config'], config)
        self.assertEqual(result['key'], key)

        # Delete the configlet
        self.api.delete_configlet(name, key)

        # Verify configlet was deleted
        with self.assertRaises(CvpApiError):
            self.api.get_configlet_by_name(name)

    def test_api_add_note_to_configlet(self):
        ''' Verify add_note_to_configlet
        '''
        name = 'test_configlet_with_note_%d' % time.time()
        config = 'lldp timer 9'

        # Add the configlet
        key = self._create_configlet(name, config)

        # Add a note to the configlet
        note = 'Updated by cvprac test'
        result = self.api.add_note_to_configlet(key, note)

        # Verify note was added to configlet
        result = self.api.get_configlet_by_name(name)
        self.assertIsNotNone(result)
        self.assertEqual(result['name'], name)
        self.assertEqual(result['config'], config)
        self.assertEqual(result['key'], key)
        self.assertEqual(result['note'], note)
        # Delete test configlet
        self.api.delete_configlet(name, key)

    def _execute_task(self, task_id):
        ''' Execute a task and wait for it to complete.
        '''
        # Test add_note_to_task
        self.api.add_note_to_task(task_id, 'Test Generated')

        self.api.execute_task(task_id)

        # Verify task executed within 30 seconds
        cnt = 30
        while cnt > 0:
            time.sleep(1)
            result = self.api.get_task_by_id(task_id)
            status = result['workOrderUserDefinedStatus']
            if status == 'Completed' or status == 'Failed':
                break
            cnt -= 1
        err_msg = 'Execution for task id %s failed' % task_id
        self.assertNotEqual(status, 'Failed', msg=err_msg)
        err_msg = 'Timeout waiting for task id %s to execute' % task_id
        self.assertGreater(cnt, 0, msg=err_msg)

    def _execute_long_running_task(self, task_id):
        ''' Execute a long running task and wait for it to complete.
        '''
        # Test add_note_to_task
        self.api.add_note_to_task(task_id, 'Test Generated')

        self.api.execute_task(task_id)

        # Verify task executed within 10 minutes
        cnt = 60
        while cnt > 0:
            time.sleep(10)
            result = self.api.get_task_by_id(task_id)
            status = result['workOrderUserDefinedStatus']
            if status == 'Completed' or status == 'Failed':
                break
            cnt -= 1
        err_msg = 'Execution for task id %s failed' % task_id
        self.assertNotEqual(status, 'Failed', msg=err_msg)
        err_msg = ('Timeout waiting for long running task id %s to execute'
                   % task_id)
        self.assertGreater(cnt, 0, msg=err_msg)

    def test_api_execute_task(self):
        ''' Verify execute_task
        '''
        # Create task and execute it
        (task_id, _) = self._create_task()
        self._execute_long_running_task(task_id)

        # Check compliance
        self.test_api_check_compliance()

    def test_api_get_containers(self):
        ''' Verify get containers
        '''
        result = self.api.get_containers()
        self.assertIsNotNone(result)
        total = result['total']
        self.assertEqual(len(result['data']), total)

    def test_api_no_container_by_name(self):
        ''' Verify searching for a container name that doesn't exist returns
            None
        '''
        container = self.api.get_container_by_name('NonExistentContainer')
        self.assertIsNone(container)

    def test_api_get_devices_in_container(self):
        ''' Verify searching for devices in a container returns only the
            devices under the given container name.
        '''
        # Get All Devices
        all_devices = self.api.get_inventory()

        # Grab key of container to test from first device in inventory
        device = all_devices[0]
        parent_cont = device['parentContainerId']

        # Make list of all devices from full inventory that are in the
        # same container as the first device
        devices_in_container = []
        for dev in all_devices:
            if dev['parentContainerId'] == parent_cont:
                devices_in_container.append(dev)

        # Get the name of the container for the container key from
        # the first device
        all_containers = self.api.get_containers()
        container_name = None
        for container in all_containers['data']:
            if container['key'] == parent_cont:
                container_name = container['name']

        result = self.api.get_devices_in_container(container_name)
        self.assertEqual(result, devices_in_container)

    def test_api_search_topology(self):
        ''' Verify search_topology return data
        '''
        full_inv = self.api.get_inventory()
        device = full_inv[0]
        result = self.api.search_topology(device['fqdn'])
        self.assertIsNotNone(result)
        self.assertIn('containerList', result)
        self.assertIn('keywordList', result)
        self.assertIn('total', result)
        self.assertIn('netElementList', result)
        self.assertIn('netElementContainerList', result)

    def test_api_containers(self):
        ''' Verify add_container, get_container_by_name and delete_container
        '''
        name = 'CVPRACTEST'
        parent = self.container
        # Verify create container
        self.api.add_container(name, parent['name'], parent['key'])

        # Verify get container for exact container name returns only that
        # container
        container = self.api.get_container_by_name(name)
        self.assertIsNotNone(container)
        self.assertEqual(container['name'], name)

        # Verify finding created container using search topology
        result = self.api.search_topology(name)
        self.assertEqual(len(result['containerList']), 1)
        container = result['containerList'][0]
        self.assertEqual(container['name'], name)
        key = container['key']
        # Verify newly created container has no devices in it
        new_cont_devices = self.api.get_devices_in_container(name)
        self.assertEqual(new_cont_devices, [])

        # Verify move device to container
        device = self.api.get_inventory()[0]
        orig_cont = self.api.get_parent_container_for_device(
            device['key'])
        if orig_cont['key'] != 'undefined_container':
            task = self.api.move_device_to_container(
                'test', device, container)['data']['taskIds'][0]
            self.api.cancel_task(task)
            curr_cont = self.api.get_parent_container_for_device(device['key'])
            self.assertEqual(curr_cont['key'], key)
            device = self.api.get_device_by_name(device['fqdn'])
            if 'parentContainerId' in device:
                self.assertEqual(device['parentContainerId'], key)
            task = self.api.move_device_to_container(
                'test', device, orig_cont)['data']['taskIds'][0]
            self.api.cancel_task(task)
            curr_cont = self.api.get_parent_container_for_device(device['key'])
            self.assertEqual(curr_cont['key'], orig_cont['key'])
            device = self.api.get_device_by_name(device['fqdn'])
            if 'parentContainerId' in device:
                self.assertEqual(device['parentContainerId'], orig_cont['key'])

        # Verify delete container
        self.api.delete_container(name, key, parent['name'], parent['key'])
        result = self.api.search_topology(name)
        self.assertEqual(len(result['containerList']), 0)

    def test_api_delete_container_with_children(self):
        ''' Verify delete_container returns a failure when attempting to delete
            a container with a child container
        '''
        name = 'CVPRACTEST'
        parent = self.container
        # Verify create container
        self.api.add_container(name, parent['name'], parent['key'])

        # Verify get container for exact container name returns only that
        # container
        new_container = self.api.get_container_by_name(name)
        self.assertIsNotNone(new_container)
        self.assertEqual(new_container['name'], name)

        child_name = 'CVPRACTESTCHILD'
        self.api.add_container(child_name, new_container['name'],
                               new_container['key'])
        # Verify get container for exact container name returns only that
        # container
        new_child_container = self.api.get_container_by_name(child_name)
        self.assertIsNotNone(new_child_container)
        self.assertEqual(new_child_container['name'], child_name)

        # Verify failure status when attempting to delete new parent container
        # with self.assertRaises(CvpApiError):
        #    self.api.delete_container(new_container['name'],
        #                              new_container['key'],
        #                              parent['name'], parent['key'])
        try:
            self.api.delete_container(new_container['name'],
                                      new_container['key'],
                                      parent['name'], parent['key'])
        except CvpApiError as error:
            if 'Only empty container can be deleted' in error.msg:
                pprint('CVP Version {} raises error when attempting to'
                       ' delete container with'
                       ' children'.format(self.clnt.apiversion))
            elif 'Container was not deleted. Check for children' in error.msg:
                pprint('CVP Version {} does not raise error when attempting to'
                       ' delete container with'
                       ' children'.format(self.clnt.apiversion))

        # Delete child container first
        resp = self.api.delete_container(new_child_container['name'],
                                         new_child_container['key'],
                                         new_container['name'],
                                         new_container['key'])
        self.assertIsNotNone(resp)
        self.assertIn('data', resp)
        self.assertIn('status', resp['data'])
        self.assertEqual('success', resp['data']['status'])
        result = self.api.search_topology(new_child_container['name'])
        self.assertEqual(len(result['containerList']), 0)

        # Now delete new parent container
        resp = self.api.delete_container(new_container['name'],
                                         new_container['key'],
                                         parent['name'],
                                         parent['key'])
        self.assertIsNotNone(resp)
        self.assertIn('data', resp)
        self.assertIn('status', resp['data'])
        self.assertEqual('success', resp['data']['status'])
        result = self.api.search_topology(new_container['name'])
        self.assertEqual(len(result['containerList']), 0)

    def test_api_container_url_encode_name(self):
        ''' Verify special characters can be used in container names
        '''
        new_cont_name = 'Rack2+_DC11'
        parent = self.container
        # Verify create container
        self.api.add_container(new_cont_name, parent['name'], parent['key'])
        # Verify get container for container with special characters in name
        container = self.api.get_container_by_name(new_cont_name)
        self.assertIsNotNone(container)
        self.assertEqual(container['name'], new_cont_name)
        # Verify delete container
        self.api.delete_container(new_cont_name, container['key'],
                                  parent['name'], parent['key'])
        result = self.api.search_topology(new_cont_name)
        self.assertEqual(len(result['containerList']), 0)

    def test_api_configlets_to_device(self):
        ''' Verify apply_configlets_to_device and
            remove_configlets_from_device
        '''
        # Create a new configlet
        name = 'test_device_configlet'
        config = 'alias srie show running-config interface ethernet 1'

        # Add the configlet
        key = self._create_configlet(name, config)

        # Get the next task ID
        task_id = self._get_next_task_id()

        # Apply the configlet to the device
        label = 'cvprac device configlet test'
        param = {'name': name, 'key': key}
        self.api.apply_configlets_to_device(label, self.device, [param])

        # Validate task was created to apply the configlet to device
        # Wait 30 seconds for task to get created
        cnt = 30
        while cnt > 0:
            time.sleep(1)
            result = self.api.get_task_by_id(task_id)
            if result is not None:
                break
            cnt -= 1
        self.assertIsNotNone(result)
        self.assertEqual(result['workOrderId'], task_id)
        self.assertIn(label, result['description'])

        # Execute Task
        self._execute_long_running_task(task_id)

        # Get the next task ID
        task_id = self._get_next_task_id()

        # Remove configlet from device
        self.api.remove_configlets_from_device(label, self.device, [param])

        # Validate task was created to remove the configlet to device
        # Wait 30 seconds for task to get created
        cnt = 30
        while cnt > 0:
            time.sleep(1)
            result = self.api.get_task_by_id(task_id)
            if result is not None:
                break
            cnt -= 1
        self.assertIsNotNone(result)
        self.assertEqual(result['workOrderId'], task_id)
        self.assertIn(label, result['description'])

        # Execute Task
        self._execute_long_running_task(task_id)

        # Delete the configlet
        self.api.delete_configlet(name, key)

        # Check compliance
        self.test_api_check_compliance()

    def test_api_configlets_to_container(self):
        ''' Verify apply_configlets_to_container and
            remove_configlets_from_container
        '''
        # pylint: disable=too-many-statements
        # Create a new container to move our device to
        # This is to make sure applying a new configlet to container only
        # affects our one device
        new_cont_name = 'CVPRAC_ConfCont_TEST'
        # Verify create container
        self.api.add_container(new_cont_name,
                               self.container['name'],
                               self.container['key'])
        new_cont_info = self.api.get_container_by_name(new_cont_name)
        self.assertIsNotNone(new_cont_info)
        self.assertEqual(new_cont_info['name'], new_cont_name)
        new_cont_key = new_cont_info['key']

        dev_orig_cont = self.api.get_parent_container_for_device(
            self.device['key'])
        # Verify device is not currently in Undefined container
        self.assertNotEqual(dev_orig_cont, 'undefined_container')
        # Move device to new container
        task_id = self.api.move_device_to_container(
            'test', self.device, new_cont_info)['data']['taskIds'][0]
        self.api.cancel_task(task_id)
        # Verify device is in new container
        dev_curr_cont = self.api.get_parent_container_for_device(
            self.device['key'])
        self.assertEqual(dev_curr_cont['key'], new_cont_key)
        moved_dev_info = self.api.get_device_by_name(self.device['fqdn'])
        if 'parentContainerId' in moved_dev_info:
            self.assertEqual(moved_dev_info['parentContainerId'], new_cont_key)

        # Create a new configlet
        name = 'test_container_configlet'
        config = 'alias srie show running-config interface ethernet 2'

        # Add the configlet
        key = self._create_configlet(name, config)

        # Get the next task ID
        task_id = self._get_next_task_id()

        # Apply the configlet to the new container
        label = 'cvprac container configlet test'
        param = {'name': name, 'key': key}
        # Apply the new configlet to the new container
        self.api.apply_configlets_to_container(label, new_cont_info,
                                               [param])

        # Validate task was created to apply the configlet to container
        # Wait 30 seconds for task to get created
        result = None
        cnt = 30
        while cnt > 0:
            time.sleep(1)
            result = self.api.get_task_by_id(task_id)
            if result is not None:
                break
            cnt -= 1
        self.assertIsNotNone(result)
        self.assertEqual(result['workOrderId'], task_id)

        # Execute Task
        self._execute_long_running_task(task_id)

        # Get the next task ID
        task_id = self._get_next_task_id()

        # Remove configlet from container
        self.api.remove_configlets_from_container(label, new_cont_info,
                                                  [param])

        # Validate task was created to remove the configlet from container
        # Wait 30 seconds for task to get created
        result = None
        cnt = 30
        while cnt > 0:
            time.sleep(1)
            result = self.api.get_task_by_id(task_id)
            if result is not None:
                break
            cnt -= 1
        self.assertIsNotNone(result)
        self.assertEqual(result['workOrderId'], task_id)

        # Execute Task
        self._execute_long_running_task(task_id)

        # Delete the configlet
        self.api.delete_configlet(name, key)

        # Move device back to original container
        task_id = self.api.move_device_to_container(
            'test', moved_dev_info, dev_orig_cont)['data']['taskIds'][0]
        self.api.cancel_task(task_id)
        dev_curr_cont = self.api.get_parent_container_for_device(
            self.device['key'])
        self.assertEqual(dev_curr_cont['key'], dev_orig_cont['key'])
        moved_dev_info = self.api.get_device_by_name(self.device['fqdn'])
        if 'parentContainerId' in moved_dev_info:
            self.assertEqual(moved_dev_info['parentContainerId'],
                             dev_orig_cont['key'])

        # Verify delete container
        self.api.delete_container(new_cont_name, new_cont_key,
                                  self.container['name'],
                                  self.container['key'])
        result = self.api.search_topology(new_cont_name)
        self.assertEqual(len(result['containerList']), 0)

        # Check compliance
        self.test_api_check_compliance()

    def test_api_validate_configlets_for_device(self):
        ''' Verify validate_configlets_for_device
        '''
        # Create a new configlet
        name = 'test_validate_configlet_for_dev'
        config = 'alias srie7 show running-config interface ethernet 7'

        # Add the configlet
        new_conf_key = self._create_configlet(name, config)

        # Get device current configlets
        current_configlets = self.api.get_configlets_by_device_id(
            self.device['key'])
        compare_configlets = [new_conf_key]
        for configlet in current_configlets:
            compare_configlets.append(configlet['key'])

        # Run validate and compare for existing device configlets plus new one.
        # This should result in a reconciled config with 1 new line.
        resp = self.api.validate_configlets_for_device(self.device['key'],
                                                       compare_configlets,
                                                       'validateConfig')
        self.assertIn('reconciledConfig', resp)
        self.assertIn('new', resp)
        self.assertEqual(resp['new'], 1)

        # Delete the configlet
        self.api.delete_configlet(name, new_conf_key)

        # Check compliance
        self.test_api_check_compliance()

    def test_api_request_timeout(self):
        ''' Verify api timeout
        '''
        self.assertEqual(self.api.request_timeout, 30)
        self.api.request_timeout = 0.0001
        with self.assertRaises(Timeout):
            self.api.get_cvp_info()
        self.api.request_timeout = 30.0

    def test_api_get_all_temp_actions(self):
        ''' Verify get_all_temp_actions
        '''
        # pylint: disable=protected-access
        test_configlet_name = 'test_configlet'
        test_configlet_config = 'lldp timer 9'

        # Add a configlet
        test_configlet_key = self._create_configlet(test_configlet_name,
                                                    test_configlet_config)

        # Apply the configlet to the container
        data = {
            'data': [{
                'info': 'test_api_get_all_temp_actions',
                'infoPreview': 'test_api_get_all_temp_actions',
                'action': 'associate',
                'nodeType': 'configlet',
                'nodeId': '',
                'toId': self.container['key'],
                'fromId': '',
                'nodeName': '',
                'fromName': '',
                'toName': self.container['name'],
                'toIdType': 'container',
                'configletList': [test_configlet_key],
                'configletNamesList': [test_configlet_name],
                'ignoreConfigletList': [],
                'ignoreConfigletNamesList': [],
                'configletBuilderList' : [],
                'configletBuilderNamesList' : [],
                'ignoreConfigletBuilderList' : [],
                'ignoreConfigletBuilderNamesList': [],
            }]
        }
        self.api._add_temp_action(data)

        # Request the list of temp actions
        result = self.api.get_all_temp_actions()

        # Validate the results
        # There should be 1 temp action for CVP versions before 2020.2.4
        if self.clnt.apiversion < 5.0:
            self.assertEqual(result['total'], 1)
        else:
            # For CVP versions starting with CVP 2020.2.4 there will be 2
            # temp actions
            self.assertEqual(result['total'], 2)

        # The temp action should contain the data from the add action
        for tempaction in result['data']:
            if tempaction['info'] == data['data'][0]['info']:
                for dkey in data['data'][0]:
                    self.assertIn(dkey, tempaction.keys())
                    self.assertEqual(data['data'][0][dkey], tempaction[dkey])

        # Delete the temporary action and the configlet
        self.clnt.post('//provisioning/deleteAllTempAction.do')
        self.api.delete_configlet(test_configlet_name, test_configlet_key)

    def test_api_get_event_by_id_bad(self):
        ''' Verify get_event_by_id returns an error for a bad ID
        '''
        try:
            # The api request should fail
            result = self.api.get_event_by_id('\n*')
            self.assertIsNone(result)
        except CvpApiError as ebi_err:
            # The error should contain 'Invalid Event Id'
            self.assertIn('Invalid Event Id', str(ebi_err))

    def test_api_get_default_snapshot_template(self):
        ''' Verify get_default_snapshot_template.
        '''
        result = self.api.get_default_snapshot_template()
        if result is not None:
            expected = {
                u'ccTasksTagged': 0,
                u'classId': 63,
                u'commandCount': 1,
                u'createdBy': u'System',
                u'default': True,
                u'factoryId': 1,
                u'id': 63,
                u'isDefault': True,
                u'key': u'Initial_Template',
                u'name': u'Show_Inventory',
                u'note': u'',
            }

            # Remove the snapshotCount, totalSnapshotCount and
            # createdTimestamp, since these can change with usage
            result.pop('snapshotCount', None)
            result.pop('totalSnapshotCount', None)
            result.pop('createdTimestamp', None)
            self.assertDictEqual(result, expected)

    def test_api_capture_container_level_snapshot(self):
        ''' Verify capture_container_level_snapshot
        '''
        # Get the container and snapshot keys
        container_key = self.container['key']
        default_snap = self.api.get_default_snapshot_template()
        if default_snap is not None:
            snapshot_key = default_snap['key']

            # Initialize the snapshot event
            result = self.api.capture_container_level_snapshot(
                snapshot_key, container_key)
            self.assertIn('data', result)
            self.assertIn('eventId', result)
            self.assertEqual('success', result['data'])

    def test_api_add_image_cancel_image(self):
        ''' Verify add_image and cancel_image
        '''
        # Get number of current images
        orig_images = self.api.get_images()

        # Copy the test image file with a timestamp appended
        image_file_name = 'image-file-%s.swix' % time.time()
        image_file = 'test/fixtures/%s' % image_file_name
        shutil.copyfile('test/fixtures/image-file.swix', image_file)

        # Upload the image to the cluster
        add_response = self.api.add_image(image_file)

        # Remove the timestamp copy from the local filesystem
        os.remove(image_file)

        # Check return status good
        self.assertIn('result', add_response)
        self.assertEqual(add_response['result'], 'success')

        # Verify image added
        post_add_images = self.api.get_images()
        self.assertEqual(orig_images['total'] + 1, post_add_images['total'])

        # Cancel/Discard added image
        cancel_resp = self.api.cancel_image(image_file_name)
        self.assertEqual(cancel_resp['data'], 'success')

        # Verify image cancelled/discarded
        post_cancel_images = self.api.get_images()
        self.assertEqual(orig_images['total'], post_cancel_images['total'])

    def test_api_get_images(self):
        ''' Verify get images
        '''
        result = self.api.get_images()
        self.assertIsNotNone(result)
        self.assertEqual(result['total'], len(result['data']))

    def test_api_get_image_bundles(self):
        ''' Verify get image bundles
        '''
        result = self.api.get_image_bundles()
        self.assertIsNotNone(result)
        self.assertEqual(result['total'], len(result['data']))

    def test_api_get_image_bundle_by_container_id(self):
        ''' Verify get image bundle by container id
        '''
        # Test that an invalid scope defaults to false
        result = self.api.get_image_bundle_by_container_id('root', 0, 0,
                                                           'invalid')
        self.assertIsNotNone(result)
        self.assertEqual(result['total'], 0)

    def test_api_save_update_delete_image_bundle(self):
        ''' Verify save_image_bundle and update_image_bundle
        '''
        # pylint: disable=too-many-locals
        # Get an existing bundle
        bundles = self.api.get_image_bundles()
        total = bundles['total']
        bundle = self.api.get_image_bundle_by_name(bundles['data'][0]['name'])

        # Get the list of images from the existing bundle
        images = bundle['images']
        # Remove the unused keys from the images
        remove_keys = ['appliedContainersCount', 'appliedDevicesCount',
                       'factoryId', 'id', 'imageFile', 'imageFileName',
                       'isHotFix', 'uploadedDateinLongFormat', 'user']
        for image in images:
            for key in remove_keys:
                image.pop(key, None)

        # Create a new bundle with the same images
        original_name = 'test_image_bundle_%d' % time.time()
        result = self.api.save_image_bundle(original_name, images)
        expected = r'Bundle\s*:\s+%s successfully created' % original_name
        self.assertRegexpMatches(result['data'], expected)

        # Assert bundle added
        new_bundles = self.api.get_image_bundles()
        new_total = new_bundles['total']
        self.assertEqual(total + 1, new_total)

        # Get the bundle ID from the new bundle
        bundle = self.api.get_image_bundle_by_name(original_name)
        bundle_id = bundle['id']

        # Update the name of the bundle and mark it as uncertified
        updated_name = original_name + "_updated"
        result = self.api.update_image_bundle(bundle_id, updated_name, images,
                                              certified=False)
        self.assertRegexpMatches(result['data'],
                                 'Image bundle updated successfully')

        # Verify the updated bundle name has the correct bundle ID
        # and is not a certified image bundle
        bundle = self.api.get_image_bundle_by_name(updated_name)
        bundle_id = bundle['id']
        bundle_name = bundle['name']
        self.assertEqual(bundle['id'], bundle_id)
        self.assertEqual(bundle['isCertifiedImage'], 'false')

        # Verify the original bundle name does not exist
        bundle = self.api.get_image_bundle_by_name(original_name)
        self.assertIsNone(bundle)

        # Remove new bundle
        result = self.api.delete_image_bundle(bundle_id,
                                              bundle_name)
        self.assertEqual(result['data'], 'success')

        # Assert new bundle successfully removed
        new_bundles = self.api.get_image_bundles()
        new_total = new_bundles['total']
        self.assertEqual(total, new_total)

    def test_api_get_image_bundle_by_name(self):
        ''' Verify get image bundle by name
        '''
        bundles = self.api.get_image_bundles()
        if bundles['total'] > 0:
            bundle_name = bundles['data'][0]['name']
            bundle = self.api.get_image_bundle_by_name(bundle_name)
            self.assertEqual(bundle['name'], bundle_name)

    def test_api_get_image_bundle_by_name_doesnt_exist(self):
        ''' Verify get image bundle by name returns none if image bundle
            doesn't exist
        '''
        result = self.api.get_image_bundle_by_name('nonexistantimagebundle')
        self.assertIsNone(result)

    def test_api_apply_remove_image_device(self):
        ''' Verify task gets created when applying an image bundle to a device.
            This test only runs if at least one image bundle and one device
            exist in the CVP instance being used for testing.
        '''
        bundles = self.api.get_image_bundles()
        devices = self.api.get_inventory()
        # Verify at least one image bundle and device exist
        if bundles['total'] > 0 and devices:
            # Get device and image bundle
            b = self.api.get_image_bundle_by_name(bundles['data'][0]['name'])
            d = self.api.get_device_by_name(devices[0]['fqdn'])
            applied_devices_count = b['appliedDevicesCount']

            # Apply image and verify at least one task id was created
            result = self.api.apply_image_to_device(b, d)
            self.assertIsNotNone(result)
            self.assertEqual(result['data']['status'], 'success')
            taskids = result['data']['taskIds']
            self.assertIsNotNone(taskids)

            # Verify image bundle has been applied to one additional device
            b = self.api.get_image_bundle_by_name(bundles['data'][0]['name'])
            self.assertEqual((applied_devices_count + 1),
                             b['appliedDevicesCount'])

            # Verify task was created and in pending state
            task = self.api.get_task_by_id(taskids[0])
            self.assertIsNotNone(task)
            self.assertEqual(task['workOrderUserDefinedStatus'], 'Pending')

            # Cancel task and verify it is cancelled
            self.api.cancel_task(taskids[0])
            time.sleep(1)
            task = self.api.get_task_by_id(taskids[0])
            self.assertIsNotNone(task)
            self.assertEqual(task['workOrderUserDefinedStatus'], 'Cancelled')

            # Un-apply image bundle from device
            result = self.api.remove_image_from_device(b, d)
            self.assertIsNotNone(result)
            self.assertEqual(result['data']['status'], 'success')
            taskids = result['data']['taskIds']
            self.assertIsNotNone(taskids)

            # Verify image bundle applied to one less device
            b = self.api.get_image_bundle_by_name(bundles['data'][0]['name'])
            self.assertEqual(applied_devices_count, b['appliedDevicesCount'])

    def test_api_apply_remove_image_container(self):
        ''' Verify image bundle is applied to container and removed.
            Test only runs if at least one image bundle exists. Test creates
            a container to apply bundle then removes the container at the end.
        '''
        bundles = self.api.get_image_bundles()
        if bundles['total'] > 0:
            # Create container, get container info, get bundle info
            name = 'imagecontainer'
            parent = self.container
            self.api.add_container(name, parent['name'], parent['key'])
            c = self.api.get_container_by_name(name)
            b = self.api.get_image_bundle_by_name(bundles['data'][0]['name'])
            applied_container_count = b['appliedContainersCount']

            # Apply bundle to new container
            result = self.api.apply_image_to_container(b, c)
            self.assertIsNotNone(result)
            b = self.api.get_image_bundle_by_name(bundles['data'][0]['name'])
            self.assertEqual(b['appliedContainersCount'],
                             (applied_container_count + 1))

            # Remove bundle from container
            result = self.api.remove_image_from_container(b, c)
            self.assertIsNotNone(result)
            b = self.api.get_image_bundle_by_name(bundles['data'][0]['name'])
            self.assertEqual(b['appliedContainersCount'],
                             applied_container_count)

            # Remove container
            self.api.delete_container(name, c['key'], parent['name'],
                                      parent['key'])

    def test_api_inventory(self):
        ''' Verify add_device_to_inventory and delete_device(s)
        '''
        # Get a device
        full_inv = self.api.get_inventory()
        device = full_inv[0]
        # Record number of current/original non connected devices
        orig_non_connect_count = self.api.get_non_connected_device_count()
        # Get devices current container assigned
        orig_cont = self.api.get_parent_container_for_device(device['key'])
        # Get devices current configlets
        orig_configlets = self.api.get_configlets_by_device_id(device['key'])
        # delete from inventory
        self.api.delete_device(device['systemMacAddress'])
        # sleep to allow delete to complete
        time.sleep(1)
        # verify not found in inventory
        res = self.api.get_device_by_name(device['fqdn'])
        self.assertEqual(res, {})
        # add back to inventory
        self.api.add_device_to_inventory(device['ipAddress'],
                                         orig_cont['name'],
                                         orig_cont['key'], True)
        # get non connected device count until it is back to equal or less
        # than the original non connected device count
        non_connect_count = self.api.get_non_connected_device_count()
        for _ in range(3):
            if non_connect_count <= orig_non_connect_count:
                break
            time.sleep(1)
            non_connect_count = self.api.get_non_connected_device_count()
        results = self.api.save_inventory()
        # Save Inventory is deprecated for 2018.2 and beyond
        if self.clnt.apiversion == 1.0:
            self.assertEqual(results['data'], 1)
        else:
            save_msg = 'Save Inventory not implemented/necessary for' +\
                       ' CVP 2018.2 and beyond'
            self.assertEqual(results['data'], 0)
            self.assertEqual(results['message'], save_msg)
        post_save_inv = self.api.get_inventory()
        self.assertEqual(len(post_save_inv), len(full_inv))
        # verify device is found in inventory again
        re_added_dev = self.api.get_device_by_name(device['fqdn'])
        self.assertEqual(re_added_dev['systemMacAddress'],
                         device['systemMacAddress'])
        # apply original configlets back to device
        results = self.api.apply_configlets_to_device("test_api_inventory",
                                                      device, orig_configlets,
                                                      create_task=True)
        # execute returned task and wait for it to complete
        task_res = self.api.execute_task(results['data']['taskIds'][0])
        self.assertEqual(task_res, None)
        task_status = self.api.get_task_by_id(results['data']['taskIds'][0])
        while task_status['taskStatus'] != 'COMPLETED':
            task_status = self.api.get_task_by_id(
                results['data']['taskIds'][0])
            time.sleep(1)

        # delete from inventory
        # self.api.delete_device(device['systemMacAddress'])
        # verify not found in inventory
        # res = self.api.get_device_by_name(device['fqdn'])
        # self.assertEqual(res, {})
        # dut = self.duts[0]
        # self.api.retry_add_to_inventory(device['ipAddress'],
        #                                device['systemMacAddress'],
        #                                dut['username'], dut['password'])

    def test_api_change_control(self):
        ''' Verify get_change_control_info and execute_change_control.
        '''
        # Set client apiversion if it is not already set
        if self.clnt.apiversion is None:
            self.api.get_cvp_info()
        if self.clnt.apiversion < 3.0:
            chg_ctrl_name = 'test_api_%d' % time.time()
            (task_id, _) = self._create_task()
            chg_ctrl_tasks = [{
                'taskId': task_id,
                'taskOrder': 1
            }]
            chg_ctrl = self.api.create_change_control(chg_ctrl_name,
                                                      chg_ctrl_tasks,
                                                      '', '', '')
            cc_id = chg_ctrl['ccId']

            # Verify the pending change control information
            chg_ctrl_pending = self.api.get_change_control_info(cc_id)
            self.assertEqual(chg_ctrl_pending['status'], 'Pending')

            # Execute the change control
            self.api.execute_change_controls([cc_id])

            # Verify the in progress/completed change control information
            chg_ctrl_executed = self.api.get_change_control_info(cc_id)
            self.assertIn(chg_ctrl_executed['status'],
                          ('Inprogress', 'Completed'))
            # Wait until change control is completed before continuing
            # to next test
            for _ in range(3):
                chg_ctrl_executed = self.api.get_change_control_info(cc_id)
                if chg_ctrl_executed['status'] == 'Completed':
                    break
                else:
                    time.sleep(2)
            # For 2018.2 give a few extra seconds for device status to get
            # back in compliance.
            if self.clnt.apiversion >= 2.0:
                time.sleep(5)
            else:
                time.sleep(2)
        else:
            pprint('SKIPPING TEST FOR API - {0}'.format(
                self.clnt.apiversion))
            time.sleep(1)

    def test_api_cancel_change_control(self):
        ''' Verify cancel_change_control.
        '''
        # Set client apiversion if it is not already set
        if self.clnt.apiversion is None:
            self.api.get_cvp_info()
        if self.clnt.apiversion < 3.0:
            chg_ctrl_name = 'test_api_%d' % time.time()
            (task_id, _) = self._create_task()
            chg_ctrl_tasks = [{
                'taskId': task_id,
                'taskOrder': 1
            }]
            chg_ctrl = self.api.create_change_control(chg_ctrl_name,
                                                      chg_ctrl_tasks,
                                                      '', '', '')
            cc_id = chg_ctrl['ccId']

            # Verify the pending change control information
            chg_ctrl_pending = self.api.get_change_control_info(cc_id)
            self.assertEqual(chg_ctrl_pending['status'], 'Pending')

            # Cancel the change control
            self.api.cancel_change_controls([cc_id])
            time.sleep(3)

            # Verify the cancelled change control information
            chg_ctrl_cancelled = self.api.get_change_control_info(cc_id)
            self.assertEqual(chg_ctrl_cancelled['status'], 'Cancelled')
        else:
            pprint('SKIPPING TEST FOR API - {0}'.format(
                self.clnt.apiversion))
            time.sleep(1)

    def test_api_delete_change_control(self):
        ''' Verify delete_change_control.
        '''
        # Set client apiversion if it is not already set
        if self.clnt.apiversion is None:
            self.api.get_cvp_info()
        if self.clnt.apiversion < 3.0:
            chg_ctrl_name = 'test_api_%d' % time.time()
            (task_id, _) = self._create_task()
            chg_ctrl_tasks = [{
                'taskId': task_id,
                'taskOrder': 1
            }]
            chg_ctrl = self.api.create_change_control(chg_ctrl_name,
                                                      chg_ctrl_tasks,
                                                      '', '', '')
            cc_id = chg_ctrl['ccId']

            # Verify the pending change control information
            chg_ctrl_pending = self.api.get_change_control_info(cc_id)
            self.assertEqual(chg_ctrl_pending['status'], 'Pending')

            # Delete the change control
            self.api.delete_change_controls([cc_id])
            time.sleep(3)

            # Verify the deleted change control information no longer exists
            chg_ctrl_cancelled = self.api.get_change_control_info(cc_id)
            self.assertIsNone(chg_ctrl_cancelled)

            # Cancel previously created task
            cancel_task_resp = self.api.cancel_task(task_id)
            time.sleep(1)
            self.assertIsNotNone(cancel_task_resp)
        else:
            pprint('SKIPPING TEST FOR API - {0}'.format(
                self.clnt.apiversion))
            time.sleep(1)

    def test_api_filter_topology(self):
        ''' Verify filter_topology.
        '''
        # Set client apiversion if it is not already set
        if self.clnt.apiversion is None:
            self.api.get_cvp_info()
        # Verify the test container topology returns the test device info
        topology = self.api.filter_topology(node_id=self.container['key'])

        # Verify the test device is present in the returned data
        exp_device_key = self.device['key']
        topo_devices = [x['key'] for
                        x in topology['topology']['childNetElementList']]
        self.assertIn(exp_device_key, topo_devices)

        # Verify the test device data is consistent
        topo_dev_data = [x for x in topology['topology']['childNetElementList']
                         if x['key'] == exp_device_key][0]
        # The tempAction field can be either None or [] when empty,
        # so skip this in the comparison.
        topo_dev_data.pop('tempAction', None)
        known_dev_data = dict(self.device)
        known_dev_data.pop('tempAction', None)
        # The device containerName field appears to be null for filter
        # topology calls where the nodeID is a container ID.
        # Skip this in comparison
        topo_dev_data.pop('containerName', None)
        known_dev_data.pop('containerName', None)

        # Test expected parameter keys are in return data.
        # Test values for parameters with consistent return values
        # Ignore comparing values for keys with
        # known different return value formats
        diff_val_form_keys = ['dcaKey', 'modelName', 'isDANZEnabled',
                              'deviceInfo', 'ztpMode', 'isMLAGEnabled']
        for key in topo_dev_data:
            self.assertIn(key, known_dev_data)
            if self.clnt.apiversion == 1.0 or key not in diff_val_form_keys:
                self.assertEqual(topo_dev_data[key], known_dev_data[key])

    # def test_api_deploy_device(self):
    #     ''' Verify deploy_device
    #     '''
    #     device = self.api.get_inventory()[0]
    #     cur_confs = self.api.get_configlets_by_netelement_id(device['key'])
    #     device_configlet_keys = []
    #     device_configlet_names = []
    #     for confmap in cur_confs['configletMapper']:
    #         if cur_confs['configletMapper'][confmap]['type'] == 'netelement':
    #             device_configlet_keys.append(confmap)
    #
    #     for confkey in device_configlet_keys:
    #         for configlet in cur_confs['configletList']:
    #             if confkey == configlet['key']:
    #                 device_configlet_names.append(configlet['name'])
    #                 continue
    #     device_configlet_objects = []
    #     for devconfname in device_configlet_names:
    #         result = self.api.get_configlet_by_name(devconfname)
    #         if result['name'] == devconfname:
    #             device_configlet_objects.append(result)
    #     orig_cont = self.api.get_parent_container_for_device(device['key'])
    #     undefined_devs = self.api.get_devices_in_container('Undefined')
    #
    #     task_id = self._get_next_task_id()
    #     pprint('NEXT TASK ID - %s\n' % task_id)
    #     pprint('PRE RESET')
    #     resp = self.api.reset_device('TESTAPP', device, create_task=True)
    #     pprint('POST RESET')
    #     pprint(resp)
    #     pprint('PRE RESET TASK')
    #     self._execute_long_running_task(task_id)
    #     pprint('POST RESET TASK')
    #
    #     new_undefined_devs = self.api.get_devices_in_container('Undefined')
    #     self.assertEqual(len(undefined_devs) + 1, len(new_undefined_devs))
    #     new_device_info = self.api.get_inventory()[0]
    #     new_cont = self.api.get_parent_container_for_device(
    #         new_device_info['key'])
    #     self.assertEqual(new_cont['name'], 'Undefined')
    #
    #     task_id = self._get_next_task_id()
    #     pprint('NEXT TASK ID - %s\n' % task_id)
    #     pprint('PRE DEPLOY')
    #     resp = self.api.deploy_device(new_device_info, orig_cont['name'],
    #                                   device_configlet_objects,
    #                                   image_bundle=None, create_task=True)
    #     pprint('POST DEPLOY')
    #     pprint(resp)
    #     pprint('PRE EXECUTE DEPLOY TASK')
    #     self._execute_long_running_task(task_id)
    #     pprint('POST EXECUTE DEPLOY TASK')
    #
    #     final_undef_devs = self.api.get_devices_in_container('Undefined')
    #     self.assertEqual(len(undefined_devs), len(final_undef_devs))
    #
    # def test_api_reset_device(self):
    #     ''' Verify reset_device
    #     '''
    #     device = self.api.get_inventory()[0]
    #     cur_confs = self.api.get_configlets_by_netelement_id(device['key'])
    #     device_configlet_keys = []
    #     device_configlet_names = []
    #     for confmap in cur_confs['configletMapper']:
    #         if cur_confs['configletMapper'][confmap]['type'] == 'netelement':
    #             device_configlet_keys.append(confmap)
    #
    #     for confkey in device_configlet_keys:
    #         for configlet in cur_confs['configletList']:
    #             if confkey == configlet['key']:
    #                 device_configlet_names.append(configlet['name'])
    #                 continue
    #     orig_cont = self.api.get_parent_container_for_device(device['key'])
    #     undefined_devs = self.api.get_devices_in_container('Undefined')
    #     task_id = self._get_next_task_id()
    #
    #     resp = self.api.reset_device('TESTAPP', device, create_task=True)
    #     pprint(resp)
    #     self._execute_long_running_task(task_id)
    #
    #     new_undefined_devs = self.api.get_devices_in_container('Undefined')
    #     self.assertEqual(len(undefined_devs) + 1, len(new_undefined_devs))
    #
    #     new_device_info = self.api.get_inventory()[0]
    #
    #     new_cont = self.api.get_parent_container_for_device(
    #         new_device_info['key'])
    #     self.assertEqual(new_cont['name'], 'Undefined')
    #
    #     task_id = self._get_next_task_id()
    #     resp = self.api.move_device_to_container('TESTAPP', new_device_info,
    #                                              orig_cont,
    #                                              create_task=False)
    #     pprint(resp)
    #     apply_confs_list = []
    #     for index, confkey in enumerate(device_configlet_keys):
    #         param = {'name': device_configlet_names[index], 'key': confkey}
    #         apply_confs_list.append(param)
    #     resp = self.api.apply_configlets_to_device('TESTAPP',
    #                                                new_device_info,
    #                                                apply_confs_list,
    #                                                create_task=True)
    #     pprint(resp)
    #     self._execute_long_running_task(task_id)
    #
    #     final_undef_devs = self.api.get_devices_in_container('Undefined')
    #     self.assertEqual(len(undefined_devs), len(final_undef_devs))


if __name__ == '__main__':
    unittest.main()

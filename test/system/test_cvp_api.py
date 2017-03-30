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
import sys
import time
import unittest
from requests.exceptions import Timeout

from cvprac.cvp_client import CvpClient
from cvprac.cvp_client_errors import CvpApiError

sys.path.append(os.path.join(os.path.dirname(__file__), '../lib'))
from systestlib import DutSystemTest

class TestCvpClient(DutSystemTest):
    ''' Test cases for the CvpClient class.
    '''
    # pylint: disable=too-many-public-methods
    def setUp(self):
        ''' Instantiate the CvpClient class and connect to the CVP node.
            Log messages to the /tmp/TestCvpClient.log
        '''
        super(TestCvpClient, self).setUp()
        self.clnt = CvpClient(filename='/tmp/TestCvpClient.log')
        self.assertIsNotNone(self.clnt)
        dut = self.duts[0]
        self.clnt.connect([dut['node']], dut['username'], dut['password'])
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
        # Get the next task ID
        task_id = self._get_next_task_id()

        # Update the lldp time in the first configlet in the list.
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
        while cnt > 0:
            time.sleep(1)
            result = self.api.get_task_by_id(task_id)
            if result is not None:
                break
            cnt -= 1
        err_msg = 'Timeout waiting for task id %s to be created' % task_id
        self.assertGreater(cnt, 0, msg=err_msg)

        return (task_id, org_config)

    def test_api_get_cvp_info(self):
        ''' Verify get_cvp_info
        '''
        result = self.api.get_cvp_info()
        self.assertIsNotNone(result)
        self.assertIn('version', result)

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
        status = result['workOrderUserDefinedStatus']
        self.assertEqual(status, 'Pending')

        # Restore the configlet to what it was before the task was created.
        configlet = self.dev_configlets[0]
        self.api.update_configlet(org_config, configlet['key'],
                                  configlet['name'])

        # Test cancel_task
        self.api.cancel_task(task_id)

        # Get the task logs
        result = self.api.get_logs_by_id(task_id)
        self.assertIsNotNone(result)

        # Check compliance
        self.test_api_check_compliance()

    def test_api_get_task_by_id_bad(self):
        ''' Verify get_task_by_id with bad task id
        '''
        result = self.api.get_task_by_id(10000000)
        self.assertIsNone(result)

    def test_api_get_task_by_id_fmt_bad(self):
        ''' Verify get_task_by_id with bad task id
        '''
        with self.assertRaises(CvpApiError):
            self.api.get_task_by_id('BOGUS')

    def test_api_get_tasks_by_s_bad(self):
        ''' Verify get_tasks_by_status
        '''
        result = self.api.get_tasks_by_status('BOGUS')
        self.assertIsNotNone(result)

    def test_api_get_configlet_by_name(self):
        ''' Verify get_configlet_by_name
        '''
        configlet = self.dev_configlets[0]
        result = self.api.get_configlet_by_name(configlet['name'])
        self.assertIsNotNone(result)
        self.assertEqual(result['key'], configlet['key'])

    def test_api_get_configlet_history(self):
        ''' Verify get_configlet_history
        '''
        key = self.dev_configlets[0]['key']
        result = self.api.get_configlet_history(key)
        self.assertIsNotNone(result)

    def test_api_get_device_by_name(self):
        ''' Verify get_device_by_name
        '''
        result = self.api.get_device_by_name(self.device['fqdn'])
        self.assertIsNotNone(result)
        self.assertEqual(result, self.device)

    def test_api_get_device_by_name_bad(self):
        ''' Verify get_device_by_name with bad fqdn
        '''
        result = self.api.get_device_by_name('bogus_host_name')
        self.assertIsNotNone(result)
        self.assertEqual(result, {})

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

    def test_api_execute_task(self):
        ''' Verify execute_task
        '''
        # Create task and execute it
        (task_id, _) = self._create_task()
        self._execute_task(task_id)

        # Check compliance
        self.test_api_check_compliance()

    def test_api_get_containers(self):
        ''' Verify get containers
        '''
        result = self.api.get_containers()
        self.assertIsNotNone(result)
        total = result['total']
        self.assertEqual(len(result['data']), total)

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

    def test_api_configlets_to_device(self):
        ''' Verify apply_configlets_to_device and remove_configlets_from_device
        '''
        # Create a new configlet
        name = 'test_configlet'
        config = 'alias srie show running-config interface ethernet 1'

        # Add the configlet
        key = self._create_configlet(name, config)

        # Get the next task ID
        task_id = self._get_next_task_id()

        # Apply the configlet to the device
        label = 'cvprac test'
        param = {'name': name, 'key': key}
        self.api.apply_configlets_to_device(label, self.device, [param])

        # Validate task was created to apply the configlet to device
        result = self.api.get_task_by_id(task_id)
        self.assertIsNotNone(result)
        self.assertEqual(result['workOrderId'], task_id)
        self.assertIn(label, result['description'])

        # Execute Task
        self._execute_task(task_id)

        # Get the next task ID
        task_id = self._get_next_task_id()

        # Remove configlet from device
        self.api.remove_configlets_from_device(label, self.device, [param])

        # Validate task was created to remove the configlet to device
        result = self.api.get_task_by_id(task_id)
        self.assertIsNotNone(result)
        self.assertEqual(result['workOrderId'], task_id)
        self.assertIn(label, result['description'])

        # Execute Task
        self._execute_task(task_id)

        # Delete the configlet
        self.api.delete_configlet(name, key)

        # Check compliance
        self.test_api_check_compliance()

    def test_api_check_compliance(self):
        ''' Verify check_compliance
        '''
        key = self.device['key']
        ntype = self.device['type']
        result = self.api.check_compliance(key, ntype)
        self.assertEqual(result['complianceCode'], '0000')
        self.assertEqual(result['complianceIndication'], 'NONE')

    def test_api_request_timeout(self):
        ''' Verify api timeout
        '''
        self.assertEqual(self.api.request_timeout, 30)
        self.api.request_timeout = 0.0001
        with self.assertRaises(Timeout):
            self.api.get_cvp_info()
        self.api.request_timeout = 30.0

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

    def test_api_get_image_bundle_by_name(self):
        ''' Verify get image bundle by name
        '''
        bundles = self.api.get_image_bundles()
        if bundles['total'] > 0:
            bundle_name = bundles['data'][0]['name']
            bundle = self.api.get_image_bundle_by_name(bundle_name)
            self.assertEqual(bundle['name'], bundle_name)

    def test_api_get_image_bundle_by_name_doesnt_exist(self):
        ''' Verify get image bundle by name returns none if image bundle doesn't exist
        '''
        result = self.api.get_image_bundle_by_name('nonexistantimagebundle')
        self.assertIsNone(result)

    def test_api_apply_image_to_device(self):
        ''' Verify task gets created when applying an image bundle to a device.
            This test only runs if at least one image bundle and one device
            exist in the CVP instance being used for testing.
        '''
        bundles = self.api.get_image_bundles()
        devices = self.api.get_inventory()
        # Verify at least one image bundle and device exist
        if bundles['total'] > 0 and len(devices) > 0:
            # Get device and image bundle
            b = self.api.get_image_bundle_by_name(bundles['data'][0]['name'])
            d = self.api.get_device_by_name(devices[0]['fqdn'])

            # Apply image and verify at least one task id was created
            result = self.api.apply_image_to_device(b, d)
            self.assertIsNotNone(result)
            self.assertEqual(result['data']['status'], 'success')
            taskids = result['data']['taskIds']
            self.assertIsNotNone(taskids)

            # Verify task was created and in pending state
            task = self.api.get_task_by_id(taskids[0])
            self.assertIsNotNone(task)
            self.assertEqual(task['workOrderUserDefinedStatus'], 'Pending')

            # Cancel task and verify it is cancelled
            self.api.cancel_task(taskids[0])
            task = self.api.get_task_by_id(taskids[0])
            self.assertIsNotNone(task)
            self.assertEqual(task['workOrderUserDefinedStatus'], 'Cancelled')

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


if __name__ == '__main__':
    unittest.main()

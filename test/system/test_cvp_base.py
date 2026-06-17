# pylint: disable=wrong-import-position

''' Base class for TestCvpClient and TestCvpClientCC class.
'''
from pprint import pprint
import os
import sys
import re
import time
import uuid
import urllib3

sys.path.append(os.path.join(os.path.dirname(__file__), '../lib'))
from systestlib import DutSystemTest
from cvprac.cvp_client import CvpClient


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class TestCvpClientBase(DutSystemTest):
    ''' Base class for TestCvpClient and TestCvpClientCC class.
    '''
    # pylint: disable=too-many-public-methods
    # pylint: disable=invalid-name
    _preflight_done = False
    _suite_container_baseline = {}
    _suite_device_container = None
    _test_container_prefixes = ('CVPRACTEST', 'CVPRAC_')
    _test_container_names = {'Rack2+_DC11', 'imagecontainer'}

    @classmethod
    def setUpClass(cls):
        ''' Instantiate the CvpClient class and connect to the CVP node.
            Log messages to the /tmp/TestCvpClient.log
        '''
        super(TestCvpClientBase, cls).setUpClass()
        cls.clnt = CvpClient(filename='/tmp/TestCvpClient.log')
        assert cls.clnt is not None
        assert cls.clnt.last_used_node is None
        dut = cls.duts[0]
        cert = dut.get("cert", False)
        username = dut.get("username", "")
        password = dut.get("password", "")
        api_token = dut.get("api_token", None)
        is_cvaas = dut.get("is_cvaas", False)
        connect_timeout = dut.get("connect_timeout", 10)
        request_timeout = dut.get("request_timeout", 30)

        cls.clnt.connect([dut['node']], username, password,
                         connect_timeout, request_timeout,
                         cert=cert, is_cvaas=is_cvaas, api_token=api_token)

        # Store user provided request_timeout for use during
        # test_api_request_timeout testcase
        cls.request_timeout = request_timeout
        cls.api = cls.clnt.api
        assert cls.api is not None
        cls._refresh_device_state()
        if not TestCvpClientBase._preflight_done:
            cls._preflight_cleanup()
            TestCvpClientBase._preflight_done = True
        cls._refresh_device_state()

    @classmethod
    def _refresh_device_state(cls):
        ''' Refresh the device, parent container and assigned configlets. '''
        dut = cls.duts[0]
        err_msg = 'CVP node must contain at least one device'
        result = cls.api.get_inventory()
        assert result is not None
        if len(result) < 1:
            raise AssertionError(err_msg)
        assert len(result) >= 1
        device = [res for res in result if res['hostname'] ==
                  dut.get("device", "")]
        cls.device = device[0]
        # Get the container for the device on the list and
        # use that container as the parent container.
        result = cls.api.search_topology(cls.device['fqdn'])
        assert result is not None
        dev_container = result['netElementContainerList']
        assert len(dev_container) >= 1
        info = dev_container[0]
        result = cls.api.search_topology(info['containerName'])
        assert result is not None
        cls.container = result['containerList'][0]

        # Get the configlets assigned to the device.  There must be at least 1.
        err_msg = 'CVP node device must have at least one configlet assigned'
        key = info['netElementKey']
        result = cls.api.get_configlets_by_device_id(key)
        if len(result) < 1:
            raise AssertionError(err_msg)
        cls.dev_configlets = result

    @classmethod
    def _preflight_cleanup(cls):
        ''' Clean up pending suite state before any system tests run. '''
        cls._cancel_open_tasks()
        cls._cleanup_change_controls()
        cls._cleanup_named_test_containers()
        cls._refresh_device_state()
        cls._wait_for_device_compliance()
        TestCvpClientBase._suite_container_baseline = cls._get_container_map()
        TestCvpClientBase._suite_device_container = cls.api.get_parent_container_for_device(
            cls.device['key'])

    @classmethod
    def tearDownClass(cls):
        ''' Destroy the CvpClient class.
        '''
        super(TestCvpClientBase, cls).tearDownClass()
        cls.api = None
        cls.clnt = None

    def cancel_task(self, task_id):
        """ Cancel task
        """
        pprint('CANCELING TASK...')
        self.api.cancel_task(task_id)

    def setUp(self):
        '''
            Set the task_id, cc_id and cc_name. It executes before each test case
        '''
        self._refresh_device_state()
        self.task_id = None
        self.task_ids = []
        self.cc_id = str(uuid.uuid4())
        self.cc_name = f'test_api_{time.time()}'
        self.configlet_restores = {}
        self._verify_cleanup_compliance = False
        self._cleanup_requires_restore_execution = False

    def tearDown(self):
        '''
            Delete the change control, restore configlets, cancel tracked tasks
            and remove created containers.
        '''
        cleanup_error = None
        self._prepare_cleanup()
        try:
            chg_ctrl_get_one = self.api.change_control_get_one(self.cc_id)
            if chg_ctrl_get_one:
                self.delete_change_control(self.cc_id)
        except Exception as error: # pylint: disable=broad-except
            cleanup_error = error
        for cleanup_step in (
                self._restore_configlets,
                self._restore_device_container,
                self._cancel_tracked_tasks,
                self._cancel_open_tasks,
                self._cleanup_extra_containers,
                self._refresh_after_cleanup):
            try:
                cleanup_step()
            except Exception as error: # pylint: disable=broad-except
                if cleanup_error is None:
                    cleanup_error = error
        if cleanup_error is not None:
            raise cleanup_error

    def _get_next_task_id(self):
        ''' Return the next task id.

            Returns:
                task_id (str): Task ID
        '''
        # Get all the tasks and the task id of the next task created is
        # the length + 1.
        results = self.api.get_tasks()
        self.assertIsNotNone(results)
        latest_task = str(int(results['data'][0]['workOrderId']) + 1)
        return latest_task

    def _create_task(self):
        ''' Create a task by making a simple change to a configlet assigned
            to the device.

            Returns:
                (task_id, config)
                task_id (str): Task ID
                config (str): Previous configlets contents
        ''' # pylint: disable=duplicate-code
        self._refresh_device_state()
        task_id = self._get_next_task_id()
        configlet = self._get_single_device_configlet()
        config = configlet['config']
        org_config = config
        self._track_configlet_restore(configlet)

        match = re.match(r'lldp timer (\d+)', config)
        if match is not None:
            value = int(match.group(1)) + 1
            repl = f'lldp timer {value}'
            config = re.sub(match.group(0), repl, config)
        else:
            value = 13
            config = f'lldp timer {value}\n' + config
        configlet['config'] = config

        # Updating the configlet will cause a task to be created to apply
        # the change to the device.
        task_snapshot = self._get_task_snapshot()
        self.api.update_configlet(config, configlet['key'], configlet['name'])
        task_ids = self._discover_task_ids(task_snapshot, fallback_task_id=task_id)
        if task_ids:
            self._track_task_ids(task_ids)
            task_id = task_ids[0]
        else:
            self._track_task_ids([task_id])

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
        err_msg = f'Timeout waiting for task id {task_id} to be created'
        self.assertGreater(cnt, 0, msg=err_msg)
        self.task_id = task_id
        return task_id, org_config

    def delete_change_control(self, cc_id):
        """ Delete change control
        """
        pprint('DELETING CHANGE CONTROL...')
        delete_chg_ctrl = self.api.change_control_delete(
            cc_id)
        assert delete_chg_ctrl is not None
        assert delete_chg_ctrl['key']['id'] == cc_id
        return delete_chg_ctrl

    @classmethod
    def _get_container_map(cls):
        ''' Return current containers keyed by container key. '''
        return {
            container['key']: container for container in cls.api.get_containers()['data']
        }

    @classmethod
    def _is_test_container_name(cls, name):
        ''' Return True if the container name is used by system tests. '''
        return (
            name in cls._test_container_names or
            any(name.startswith(prefix) for prefix in cls._test_container_prefixes)
        )

    @classmethod
    def _extract_task_ids(cls, response):
        ''' Extract task IDs from a CVP response. '''
        if not isinstance(response, dict):
            return []
        data = response.get('data', {})
        if isinstance(data, dict):
            task_ids = data.get('taskIds', [])
            return [str(task_id) for task_id in task_ids]
        return []

    @classmethod
    def _task_is_terminal(cls, task):
        ''' Return True when the task no longer needs cleanup. '''
        return (
            task.get('currentTaskName') == 'Cancelled' or
            task.get('workOrderUserDefinedStatus') in ('Cancelled', 'Completed', 'Failed')
        )

    @classmethod
    def _cancel_open_tasks(cls):
        ''' Cancel any non-terminal tasks before the suite starts. '''
        tasks = cls.api.get_tasks()
        for task in tasks.get('data', []):
            task_id = task.get('workOrderId')
            if task_id and not cls._task_is_terminal(task):
                try:
                    cls.api.cancel_task(task_id)
                except Exception: # pylint: disable=broad-except
                    pass

    @classmethod
    def _cleanup_change_controls(cls):
        ''' Stop and delete pending change controls before the suite starts. '''
        if cls.clnt.apiversion is None:
            cls.api.get_cvp_info()
        if cls.clnt.apiversion < 6.0:
            return
        response = cls.api.change_control_get_all()
        for change in response.get('data', []):
            cc_id = change.get('result', {}).get('value', {}).get('key', {}).get('id')
            if not cc_id:
                continue
            try:
                cls.api.change_control_stop(cc_id, notes='cvprac system test preflight cleanup')
            except Exception: # pylint: disable=broad-except
                pass
            try:
                cls.api.change_control_delete(cc_id)
            except Exception: # pylint: disable=broad-except
                pass

    @classmethod
    def _cleanup_named_test_containers(cls):
        ''' Remove stale test containers left by previous runs. '''
        containers = cls._get_container_map()
        extra_keys = [
            key for key, container in containers.items()
            if cls._is_test_container_name(container['name'])
        ]
        cls._delete_containers(extra_keys)

    @classmethod
    def _container_depth(cls, container, containers):
        ''' Return the depth of a container in the current topology. '''
        depth = 0
        parent_id = container.get('parentId')
        while parent_id and parent_id in containers:
            depth += 1
            parent_id = containers[parent_id].get('parentId')
        return depth

    @classmethod
    def _move_device_out_of_container(cls, container, containers):
        ''' Move the shared test device out of a container before deleting it. '''
        device_parent = cls.api.get_parent_container_for_device(cls.device['key'])
        if not isinstance(device_parent, dict) or device_parent.get('key') != container['key']:
            return
        parent = containers.get(container.get('parentId'))
        if parent is None:
            return
        device = cls.api.get_device_by_name(cls.device['fqdn'])
        response = cls.api.move_device_to_container('cvprac cleanup', device, parent)
        for task_id in cls._extract_task_ids(response):
            try:
                cls.api.cancel_task(task_id)
            except Exception: # pylint: disable=broad-except
                pass
        cls._refresh_device_state()

    @classmethod
    def _delete_containers(cls, container_keys):
        ''' Delete containers, removing children before parents. '''
        pending = set(container_keys)
        while pending:
            containers = cls._get_container_map()
            known = [containers[key] for key in pending if key in containers]
            if not known:
                return
            progress = False
            for container in sorted(
                    known,
                    key=lambda item: cls._container_depth(item, containers),
                    reverse=True):
                parent = containers.get(container.get('parentId'))
                if parent is None:
                    pending.discard(container['key'])
                    continue
                cls._move_device_out_of_container(container, containers)
                try:
                    cls.api.delete_container(
                        container['name'], container['key'], parent['name'], parent['key'])
                    pending.discard(container['key'])
                    progress = True
                except Exception: # pylint: disable=broad-except
                    pass
            if not progress:
                return

    @classmethod
    def _wait_for_device_compliance(cls):
        ''' Wait for the shared test device to return to compliance. '''
        orig_timeout = cls.api.request_timeout
        if cls.clnt.apiversion is None:
            cls.api.get_cvp_info()
        if cls.clnt.apiversion >= 4.0:
            cls.api.request_timeout = orig_timeout * 3
        try:
            for _ in range(0, 12):
                result = cls.api.check_compliance(cls.device['key'], cls.device['type'])
                if (result is not None and
                        result.get('complianceCode') == '0000' and
                        result.get('complianceIndication') == 'NONE'):
                    return
                time.sleep(10)
        finally:
            cls.api.request_timeout = orig_timeout
        raise AssertionError('CVP device did not return to compliance during cleanup')

    def _track_task_ids(self, task_ids):
        ''' Track task IDs for teardown cleanup. '''
        for task_id in task_ids:
            task_id = str(task_id)
            if task_id not in self.task_ids:
                self.task_ids.append(task_id)
                self._verify_cleanup_compliance = True

    def _get_single_device_configlet(self):
        ''' Return a configlet assigned only to the test device when possible. '''
        for configlet in self.dev_configlets:
            if configlet['netElementCount'] == 1:
                return configlet
        return self.dev_configlets[0]

    def _track_configlet_restore(self, configlet):
        ''' Save the original configlet contents once per test. '''
        if configlet['key'] not in self.configlet_restores:
            self.configlet_restores[configlet['key']] = {
                'key': configlet['key'],
                'name': configlet['name'],
                'config': configlet['config']
            }
            self._verify_cleanup_compliance = True

    def _log_cleanup(self, message):
        ''' Log teardown cleanup progress to the shared system-test log. '''
        self.clnt.log.info('system test cleanup: %s', message)

    def _prepare_cleanup(self):
        ''' Capture teardown context before mutating cleanup state. '''
        if not self._verify_cleanup_compliance:
            self._log_cleanup('mode=read-only tracked_tasks=0 restore_configlets=0')
            return
        tracked_states = self._get_tracked_task_states()
        self._cleanup_requires_restore_execution = any(
            task is not None and task.get('workOrderUserDefinedStatus') == 'Completed'
            for task in tracked_states.values())
        if self._cleanup_requires_restore_execution:
            cleanup_mode = 'applied-change rollback'
        else:
            cleanup_mode = 'pending-only'
        self._log_cleanup(
            f'mode={cleanup_mode} tracked_tasks={self.task_ids} '
            f'restore_configlets={list(self.configlet_restores.keys())}')

    def _get_tracked_task_states(self):
        ''' Return a mapping of tracked task IDs to their current task info. '''
        states = {}
        for task_id in self.task_ids:
            states[str(task_id)] = self.api.get_task_by_id(task_id)
        return states

    def _get_task_snapshot(self):
        ''' Return current tasks keyed by task ID. '''
        snapshot = {}
        tasks = self.api.get_tasks()
        for task in tasks.get('data', []):
            task_id = task.get('workOrderId')
            if task_id is not None:
                snapshot[str(task_id)] = task
        return snapshot

    def _discover_task_ids(self, before_tasks, fallback_task_id=None):
        ''' Detect task IDs created by a configlet update. '''
        cnt = 30
        if self.clnt.apiversion is None:
            self.api.get_cvp_info()
        if self.clnt.apiversion >= 2.0:
            cnt += 30
        while cnt > 0:
            after_tasks = self._get_task_snapshot()
            task_ids = [
                task_id for task_id in after_tasks
                if task_id not in before_tasks
            ]
            if task_ids:
                return task_ids
            if fallback_task_id is not None:
                fallback = after_tasks.get(str(fallback_task_id))
                if fallback is not None:
                    return [str(fallback_task_id)]
            time.sleep(1)
            cnt -= 1
        if fallback_task_id is not None:
            fallback = self.api.get_task_by_id(fallback_task_id)
            if fallback is not None:
                return [str(fallback_task_id)]
        return []

    def _wait_for_task_completion(self, task_id, timeout=600, poll_interval=10):
        ''' Wait for a task to reach a terminal state and return the task. '''
        cnt = max(1, int(timeout / poll_interval))
        while cnt > 0:
            task = self.api.get_task_by_id(task_id)
            if task is not None:
                status = task.get('workOrderUserDefinedStatus')
                if status in ('Completed', 'Cancelled', 'Failed'):
                    return task
            time.sleep(poll_interval)
            cnt -= 1
        raise AssertionError(f'Timeout waiting for cleanup task id {task_id} to complete')

    def _execute_restore_tasks(self, task_ids, configlet_name):
        ''' Execute restore tasks so applied config changes are rolled back. '''
        for task_id in task_ids:
            task = self.api.get_task_by_id(task_id)
            if task is None:
                raise AssertionError(
                    f'Cleanup restore task {task_id} for configlet {configlet_name} was not found')
            status = task.get('workOrderUserDefinedStatus')
            if status == 'Completed':
                continue
            if status in ('Cancelled', 'Failed'):
                raise AssertionError(
                    f'Cleanup restore task {task_id} for configlet {configlet_name} '
                    f'is already {status}')
            self._log_cleanup(
                f'executing restore task {task_id} for configlet {configlet_name}')
            self.api.execute_task(task_id)
            task = self._wait_for_task_completion(task_id)
            status = task.get('workOrderUserDefinedStatus')
            if status != 'Completed':
                raise AssertionError(
                    f'Cleanup restore task {task_id} for configlet {configlet_name} '
                    f'ended in {status}')

    def _restore_configlets(self):
        ''' Restore any configlets modified by the shared task helper. '''
        for restore in self.configlet_restores.values():
            current = self.api.get_configlet_by_name(restore['name'])
            if current is None or current.get('config') == restore['config']:
                continue
            self._log_cleanup(f'restoring configlet {restore["name"]}')
            task_snapshot = self._get_task_snapshot()
            fallback_task_id = None
            if self._cleanup_requires_restore_execution:
                fallback_task_id = self._get_next_task_id()
            response = self.api.update_configlet(
                restore['config'], restore['key'], restore['name'])
            restore_task_ids = self._extract_task_ids(response)
            if not restore_task_ids:
                restore_task_ids = self._discover_task_ids(
                    task_snapshot, fallback_task_id=fallback_task_id)
            if restore_task_ids:
                self._track_task_ids(restore_task_ids)
            elif self._cleanup_requires_restore_execution:
                raise AssertionError(
                    f'Cleanup could not identify restore task for configlet {restore["name"]}')
            if self._cleanup_requires_restore_execution and restore_task_ids:
                self._execute_restore_tasks(restore_task_ids, restore['name'])

    def _restore_device_container(self):
        ''' Move the shared test device back to the suite baseline container. '''
        expected = TestCvpClientBase._suite_device_container
        if not isinstance(expected, dict):
            return
        current = self.api.get_parent_container_for_device(self.device['key'])
        if not isinstance(current, dict) or current.get('key') == expected.get('key'):
            return
        device = self.api.get_device_by_name(self.device['fqdn'])
        response = self.api.move_device_to_container('cvprac cleanup', device, expected)
        self._track_task_ids(self._extract_task_ids(response))

    def _cancel_tracked_tasks(self):
        ''' Cancel all tracked tasks that are still open. '''
        for task_id in reversed(self.task_ids):
            task = self.api.get_task_by_id(task_id)
            if task is not None and not self._task_is_terminal(task):
                self.cancel_task(task_id)

    def _cleanup_extra_containers(self):
        ''' Delete containers created after the suite baseline was captured. '''
        baseline_keys = set(TestCvpClientBase._suite_container_baseline.keys())
        current_keys = set(self._get_container_map().keys())
        extra_keys = current_keys - baseline_keys
        self._delete_containers(extra_keys)

    def _refresh_after_cleanup(self):
        ''' Refresh shared state and verify compliance after teardown cleanup. '''
        self._refresh_device_state()
        if self._verify_cleanup_compliance:
            self._wait_for_device_compliance()

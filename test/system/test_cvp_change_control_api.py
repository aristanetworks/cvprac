import os
import sys
import time
import unittest
import uuid
from pprint import pprint

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from cvprac.cvp_client_errors import CvpRequestError

sys.path.append(os.path.join(os.path.dirname(__file__), '../lib'))
from test_cvp_api import TestCvpClient

class TestCvpClientCC(TestCvpClient):
    ''' Test cases for the CvpClientCC class.
    '''
    cc_id = None

    def get_version(self):
        self.clnt.apiversion = 2.0
        if self.clnt.apiversion is None:
            self.api.get_cvp_info()
        if self.clnt.apiversion > 3.0:
            pprint('RUN TEST FOR V3 CHANGE CONTROL APIs')
            return True
        else:
            pprint('SKIPPING TEST FOR API - {0}'.format(
                self.clnt.apiversion))
            return False

    def test_api_change_control_create_for_tasks(self):
        ''' Verify change_control_create_for_tasks
        '''
        if self.get_version():
            TestCvpClientCC.cc_id = str(uuid.uuid4())
            chg_ctrl_name = 'test_api_%d' % time.time()
            (task_id, _) = self._create_task()
            chg_ctrl = self.api.change_control_create_for_tasks(
                    TestCvpClientCC.cc_id, chg_ctrl_name, [task_id])
            assert chg_ctrl['value']['change']['name'] == chg_ctrl_name

    def test_api_change_control_approve(self):
        ''' Verify change_control_approve
        '''
        if self.get_version():
            # Approve the change control
            approve_note = "Approving CC via cvprac"
            approve_chg_ctrl = self.api.change_control_approve(
                TestCvpClientCC.cc_id, notes=approve_note)
            assert approve_chg_ctrl is not None
            assert approve_chg_ctrl['value']['approve']['value'] is True
            assert approve_chg_ctrl['value']['approve']['notes'] == approve_note
            assert approve_chg_ctrl['value']['key']['id'] == TestCvpClientCC.cc_id

    def test_api_change_control_start(self):
        ''' Verify change_control_start
        '''
        if self.get_version():
            # Start the change control
            start_note = "Start the CC via cvprac"
            start_chg_ctrl = self.api.change_control_start(
                TestCvpClientCC.cc_id, notes=start_note)
            assert start_chg_ctrl is not None
            assert start_chg_ctrl['value']['start']['value'] is True
            assert start_chg_ctrl['value']['start']['notes'] == start_note
            assert start_chg_ctrl['value']['key']['id'] == TestCvpClientCC.cc_id

    def test_api_change_control_stop(self):
        ''' Verify change_control_stop
        '''
        if self.get_version():
            # Stop the chnage control
            stop_note = "stop the CC via cvprac"
            stop_chg_ctrl = self.api.change_control_stop(
                TestCvpClientCC.cc_id, notes=stop_note)
            assert stop_chg_ctrl is not None
            assert stop_chg_ctrl['value']['start']['value'] is False
            assert stop_chg_ctrl['value']['start']['notes'] == stop_note
            assert stop_chg_ctrl['value']['key']['id'] == TestCvpClientCC.cc_id

    def test_api_change_control_create_for_empty_tasks_list(self):
        ''' Verify change_control_create_for_tasks for empty task list
        '''
        if self.get_version():
            # Set client apiversion if it is not already set
            pprint('RUN TEST FOR V3 CHANGE CONTROL APIs')
            chg_ctrl_name = 'test_api_%d' % time.time()
            cc_id = str(uuid.uuid4())
            with self.assertRaises(CvpRequestError):
                chg_ctrl = self.api.change_control_create_for_tasks(
                         cc_id, chg_ctrl_name, [], series=False)

    def test_api_change_control_create_for_none_task_id_in_list(self):
        ''' Verify change_control_create_for_tasks for none task id in list
        '''
        # Set client apiversion if it is not already set
        if self.get_version():
            cc_id = str(uuid.uuid4())
            chg_ctrl_name = 'test_api_%d' % time.time()
            with self.assertRaises(CvpRequestError):
                chg_ctrl = self.api.change_control_create_for_tasks(
                    cc_id, chg_ctrl_name, [None], series=False)

    def test_api_change_control_create_for_none_task_ids_not_list(self):
        ''' Verify change_control_create_for_tasks for none task ids list
        '''
        # Set client apiversion if it is not already set
        if self.get_version():
            cc_id = str(uuid.uuid4())
            chg_ctrl_name = 'test_api_%d' % time.time()
            with self.assertRaises(TypeError):
                chg_ctrl = self.api.change_control_create_for_tasks(
                    cc_id, chg_ctrl_name, None, series=False)

    def test_api_change_control_create_for_random_task_id(self):
        ''' Verify change_control_create_for_tasks for random task id
        '''
        # Set client apiversion if it is not already set
        if self.get_version():
            random_task_id = '3333'
            cc_id = str(uuid.uuid4())
            chg_ctrl_name = 'test_api_%d' % time.time()
            # Create the change control with random task id without
            # creating the task
            chg_ctrl = self.api.change_control_create_for_tasks(
                cc_id, chg_ctrl_name, [random_task_id], series=False)

            # Approve the change control
            approve_note = "Approving CC via cvprac"
            approve_chg_ctrl = self.api.change_control_approve(
                cc_id, notes=approve_note)
            assert approve_chg_ctrl is not None
            assert approve_chg_ctrl['value']['approve']['value'] is True


if __name__ == '__main__':
    unittest.main()

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

CHANGE_CONTROL_ID_INVALID = '19175756-a8c8-4b'
RANDOM_TASK_ID = '3333'
RANDOM_CCID = '23456dvbjjhjnm'
APPROVE_NOTE = "Approving CC via cvprac"
START_NOTE = "Start the CC via cvprac"
STOP_NOTE = "Stop the CC via cvprac"
TASK_ID = None


class TestCvpClientCC(TestCvpClient):
    """ Test cases for the CvpClientCC class.
    """

    @classmethod
    def setUpClass(cls):
        """ Initialize variables
        """
        super(TestCvpClientCC, cls).setUpClass()
        cls.cc_id = str(uuid.uuid4())
        cls.cc_name = 'test_api_%d' % time.time()

    @classmethod
    def tearDownClass(cls):
        """ Reset variables value to None
        """
        super(TestCvpClientCC, cls).tearDownClass()
        cls.cc_id = None
        cls.cc_name = None

    def get_version(self):
        if self.clnt.apiversion is None:
            self.api.get_cvp_info()
        if self.clnt.apiversion > 3.0:
            pprint('RUN TEST FOR V3 CHANGE CONTROL APIs')
            return True
        else:
            pprint('SKIPPING TEST FOR API - {0}'.format(
                self.clnt.apiversion))
            return False

    def get_cc_status(self, cc_id):
        params = 'key.id={}'.format(cc_id)
        cc_url = '/api/resources/changecontrol/v1/ChangeControl?' + params
        response = self.clnt.get(cc_url, timeout=30)
        return response

    def test_api_change_control_create_for_tasks(self):
        """ Verify change_control_create_for_tasks
        """
        if self.get_version():
            pprint('CREATING CHANGE CONTROL...')
            global task_id
            (task_id, _) = self._create_task()
            chg_ctrl = self.api.change_control_create_for_tasks(
                self.cc_id, self.cc_name, [task_id])

            assert chg_ctrl['value']['key']['id'] == self.cc_id
            assert chg_ctrl['value']['change']['name'] == self.cc_name
            time.sleep(1)

            # Verify CC
            response = self.get_cc_status(self.cc_id)

            assert response is not None
            assert chg_ctrl['value']['key']['id'] == response['value']['key']['id']
            assert chg_ctrl['value']['change']['name'] == response['value']['change']['name']
            time.sleep(2)

    def test_api_change_control_approve(self):
        """ Verify change_control_approve
        """
        if self.get_version():
            pprint('APPROVING CHANGE CONTROL...')
            # Approve the change control
            approve_chg_ctrl = self.api.change_control_approve(
                self.cc_id, notes=APPROVE_NOTE)
            assert approve_chg_ctrl is not None
            assert approve_chg_ctrl['value']['approve']['value'] is True
            assert approve_chg_ctrl['value']['approve']['notes'] == APPROVE_NOTE
            assert approve_chg_ctrl['value']['key']['id'] == self.cc_id
            time.sleep(1)

            # Verify approved CC
            response = self.get_cc_status(self.cc_id)

            assert response is not None
            assert approve_chg_ctrl['value']['key']['id'] == response['value']['key']['id']
            assert approve_chg_ctrl['value']['approve']['notes'] == response['value']['approve']['notes']
            assert approve_chg_ctrl['value']['approve']['value'] == response['value']['approve']['value']

    def test_api_change_control_approval_get_one(self):
        """ Verify change_control_approval_get_one
         """
        if self.get_version():
            pprint('APPROVAL GET ONE...')
            approval_get_one = self.api.change_control_approval_get_one(self.cc_id)
            assert approval_get_one is not None
            assert approval_get_one['value']['approve']['value'] is True
            assert approval_get_one['value']['approve']['notes'] == APPROVE_NOTE
            assert approval_get_one['value']['key']['id'] == self.cc_id
            time.sleep(1)

            #verify with actual api output

            response = self.get_cc_status(self.cc_id)

            assert response is not None
            assert approval_get_one['value']['key']['id'] == response['value']['key']['id']
            assert approval_get_one['value']['approve']['notes'] == response['value']['approve']['notes']
            assert approval_get_one['value']['approve']['value'] == response['value']['approve']['value']

    def test_api_change_control_approval_get_one_without_approve(self):
        """ Verify change_control_approval_get_one_without_approve
         """
        if self.get_version():
            pprint('APPROVAL GET ONE WITHOUT APPROVE...')
            approval_get_one = self.api.change_control_approval_get_one(self.cc_id)
            assert approval_get_one is None

    def test_api_change_control_start(self):
        """ Verify change_control_start
        """
        if self.get_version():
            pprint('STARTING CHANGE CONTROL...')
            # Start the change control
            start_chg_ctrl = self.api.change_control_start(
                self.cc_id, notes=START_NOTE)
            assert start_chg_ctrl is not None
            assert start_chg_ctrl['value']['start']['value'] is True
            assert start_chg_ctrl['value']['start']['notes'] == START_NOTE
            assert start_chg_ctrl['value']['key']['id'] == self.cc_id

            # Verify start CC
            response = self.get_cc_status(self.cc_id)

            assert response is not None
            assert start_chg_ctrl['value']['key']['id'] == response['value']['key']['id']
            assert start_chg_ctrl['value']['start']['value'] == response['value']['start']['value']
            assert start_chg_ctrl['value']['start']['notes'] == response['value']['start']['notes']

    def test_api_change_control_stop(self):
        """ Verify change_control_stop
        """
        if self.get_version():
            pprint('STOPPING CHANGE CONTROL...')
            # Stop the change control
            stop_chg_ctrl = self.api.change_control_stop(
                self.cc_id, notes=STOP_NOTE)
            assert stop_chg_ctrl is not None
            assert stop_chg_ctrl['value']['start']['value'] is False
            assert stop_chg_ctrl['value']['start']['notes'] == STOP_NOTE
            assert stop_chg_ctrl['value']['key']['id'] == self.cc_id

            # Verify stop CC
            response = self.get_cc_status(self.cc_id)

            assert response is not None
            assert stop_chg_ctrl['value']['key']['id'] == response['value']['key']['id']
            assert stop_chg_ctrl['value']['start']['value'] == response['value']['start']['value']
            assert stop_chg_ctrl['value']['start']['notes'] == response['value']['start']['notes']

    def test_api_change_control_create_for_empty_tasks_list(self):
        """ Verify change_control_create_for_tasks for empty task list
        """
        if self.get_version():
            # Set client apiversion if it is not already set
            pprint('RUN TEST FOR V3 CHANGE CONTROL APIs')
            # cc_id = str(uuid.uuid4())
            with self.assertRaises(CvpRequestError):
                chg_ctrl = self.api.change_control_create_for_tasks(
                    self.cc_id, self.cc_name, [], series=False)

    def test_api_change_control_create_for_none_task_id_in_list(self):
        """ Verify change_control_create_for_tasks for none task id in list
        """
        # Set client apiversion if it is not already set
        if self.get_version():
            pprint('CREATE CHANGE CONTROL FOR LIST OF NONE TASK IDs...')
            with self.assertRaises(CvpRequestError):
                chg_ctrl = self.api.change_control_create_for_tasks(
                    self.cc_id, self.cc_name, [None], series=False)

    def test_api_change_control_create_for_none_task_ids_not_list(self):
        """ Verify change_control_create_for_tasks for none task ids list
        """
        # Set client apiversion if it is not already set
        if self.get_version():
            pprint('CREATE CHANGE CONTROL FOR NONE TASK IDs...')
            with self.assertRaises(TypeError):
                chg_ctrl = self.api.change_control_create_for_tasks(
                    self.cc_id, self.cc_name, None, series=False)

    def test_api_change_control_create_for_random_task_id(self):
        """ Verify change_control_create_for_tasks for random task id
        """
        # Set client apiversion if it is not already set
        if self.get_version():
            pprint('CREATING CHANGE CONTROL FOR RANDOM TASK IDs...')
            change_control_id = str(uuid.uuid4())
            # Create the change control with random task id without
            # creating the task, it takes a global task
            chg_ctrl = self.api.change_control_create_for_tasks(
                change_control_id, self.cc_name, [RANDOM_TASK_ID], series=False)

            # Approve the change control
            approve_chg_ctrl = self.api.change_control_approve(
                change_control_id, notes=APPROVE_NOTE)
            assert approve_chg_ctrl is not None
            assert approve_chg_ctrl['value']['approve']['value'] is True

            # Verify CC
            response = self.get_cc_status(change_control_id)

            assert response is not None
            assert chg_ctrl['value']['key']['id'] == response['value']['key']['id']
            assert chg_ctrl['value']['change']['name'] == response['value']['change']['name']

            # Delete CC
            pprint('DELETING CHANGE CONTROL FOR RANDOM TASK IDs...')
            delete_chg_ctrl = self.api.change_control_delete(
                change_control_id)
            assert delete_chg_ctrl is not None
            assert delete_chg_ctrl['key']['id'] == change_control_id

    def test_api_change_control_approve_invalid_tasks(self):
        if self.get_version():
            pprint('APPROVING CHANGE CONTROL FOR INVALID TASKS...')
            # Approve the change control
            approve_chg_ctrl = self.api.change_control_approve(
                CHANGE_CONTROL_ID_INVALID, notes=APPROVE_NOTE)
            assert approve_chg_ctrl is None

    def test_api_change_control_start_invalid_tasks(self):
        if self.get_version():
            pprint('STARTING CHANGE CONTROL FOR INVALID TASKS...')
            # Start the change control
            dut = self.duts[0]
            node = dut['node'] + ":443"
            err_msg = 'POST: https://' + node + '/api/resources/changecontrol/v1/ChangeControlConfig ' \
                                                ': Request Error: Bad Request - {"code":9, "message":"not approved"}'
            with self.assertRaisesRegex(CvpRequestError, err_msg):
                self.api.change_control_start(
                    CHANGE_CONTROL_ID_INVALID, notes=START_NOTE)

    def test_api_change_control_delete(self):
        if self.get_version():
            pprint('DELETING CHANGE CONTROL...')
            delete_chg_ctrl = self.api.change_control_delete(
                self.cc_id)
            assert delete_chg_ctrl is not None
            assert delete_chg_ctrl['key']['id'] == self.cc_id

            # Verify CC delete
            with self.assertRaises(CvpRequestError):
                response = self.get_cc_status(self.cc_id)

    def test_api_change_control_delete_invalid_cc(self):
        if self.get_version():
            pprint('DELETING CHANGE CONTROL...')
            with self.assertRaises(CvpRequestError):
                self.api.change_control_delete(
                    CHANGE_CONTROL_ID_INVALID)

    def test_api_change_control_get_one(self):
        """ Verify change_control_get_one
         """
        if self.get_version():
            print('task iddddddd in gte', task_id)
            pprint("CHANGE CONTROL GET ONE...")
            chg_ctrl_get_one = self.api.change_control_get_one(self.cc_id)
            assert chg_ctrl_get_one['value']['key']['id'] == self.cc_id
            assert chg_ctrl_get_one['value']['change']['name'] == self.cc_name
            assert chg_ctrl_get_one['value']['change']['stages']['values']['stage0']['action']['args']['values'][
                       'TaskID'] == task_id

            # verify with actual api output
            response = self.get_cc_status(self.cc_id)
            assert chg_ctrl_get_one['value']['key']['id'] == response['value']['key']['id']
            assert chg_ctrl_get_one['value']['change']['name'] == response['value']['change']['name']
            assert chg_ctrl_get_one['value']['change']['stages']['values']['stage0']['action']['args']['values'][
                       'TaskID'] == response['value']['change']['stages']['values']['stage0']['action']['args']['values'][
                       'TaskID']

    def test_api_change_control_get_one_without_ccid(self):
        """ Verify change_control_get_one_without_ccid
         """
        if self.get_version():
            pprint("CHANGE CONTROL GET ONE WITHOUT CC_ID...")
            err_msg = "change_control_get_one() missing 1 required positional argument: 'cc_id'"
            with self.assertRaises(TypeError) as ex:
                chg_ctrl_get_one = self.api.change_control_get_one()
                self.assertEqual(err_msg, ex.exception)

    def test_api_change_control_get_one_with_none_ccid(self):
        """ Verify change_control_get_one_with_none_ccid
         """
        if self.get_version():
            pprint("CHANGE CONTROL GET WITH NONE CC_ID...")
            chg_ctrl_get_one = self.api.change_control_get_one(None)
            assert chg_ctrl_get_one is None

    def test_api_change_control_get_one_with_random_ccid(self):
        """ Verify change_control_get_one_with_random_ccid
         """
        if self.get_version():
            pprint("CHANGE CONTROL GET WITH RANDOM CC_ID...")
            chg_ctrl_get_one = self.api.change_control_get_one(RANDOM_CCID)
            assert chg_ctrl_get_one is None

    def test_api_change_control_get_all(self):
        """ Verify change_control_get_all
         """
        ID = []
        if self.get_version():
            pprint("CHANGE CONTROL GET ALL...")
            chg_ctrl_get_all = self.api.change_control_get_all()
            for i in range(len(chg_ctrl_get_all['data'])):
                ID.append(chg_ctrl_get_all['data'][i]['result']['value']['key']['id'])
            assert self.cc_id in ID

    def test_api_change_control_get_all_without_create_chg_ctrl(self):
        """ Verify change_control_get_all_without_create_chg_ctrl
         """
        ID = []
        if self.get_version():
            pprint("CHANGE CONTROL GET ALL WITHOUT CHANGE CONTROL CREATION...")
            chg_ctrl_get_all = self.api.change_control_get_all()
            for i in range(len(chg_ctrl_get_all['data'])):
                ID.append(chg_ctrl_get_all['data'][i]['result']['value']['key']['id'])
            assert self.cc_id not in ID

    def test_api_change_control_approval_get_all(self):
        """ Verify change_control_approval_get_all
         """
        ID = []
        if self.get_version():
            pprint("CHANGE CONTROL APPROVAL GET ALL...")
            chg_ctrl_approval_get_all = self.api.change_control_approval_get_all()
            for i in range(len(chg_ctrl_approval_get_all['data'])):
                ID.append(chg_ctrl_approval_get_all['data'][i]['result']['value']['key']['id'])
                if chg_ctrl_approval_get_all['data'][i]['result']['value']['key']['id'] == self.cc_id:
                    check_index = i
            assert self.cc_id in ID
            assert chg_ctrl_approval_get_all['data'][check_index]['result']['value']['approve']['value'] is True

    def test_api_change_control_approval_get_all_without_approve(self):
        """ Verify change_control_approval_get_all_without_approve
         """
        ID = []
        if self.get_version():
            pprint("CHANGE CONTROL APPROVAL GET ALL WITHOUT APPROVE...")
            chg_ctrl_approval_get_all = self.api.change_control_approval_get_all()
            for i in range(len(chg_ctrl_approval_get_all['data'])):
                ID.append(chg_ctrl_approval_get_all['data'][i]['result']['value']['key']['id'])
            assert self.cc_id not in ID


def suite():
    suite = unittest.TestSuite()
    suite.addTest(TestCvpClientCC('test_api_change_control_get_all_without_create_chg_ctrl'))
    suite.addTest(TestCvpClientCC('test_api_change_control_create_for_tasks'))
    suite.addTest(TestCvpClientCC('test_api_change_control_get_one'))
    suite.addTest(TestCvpClientCC('test_api_change_control_get_one_without_ccid'))
    suite.addTest(TestCvpClientCC('test_api_change_control_get_one_with_none_ccid'))
    suite.addTest(TestCvpClientCC('test_api_change_control_get_one_with_random_ccid'))
    suite.addTest(TestCvpClientCC('test_api_change_control_get_all'))
    suite.addTest(TestCvpClientCC('test_api_change_control_approval_get_one_without_approve'))
    suite.addTest(TestCvpClientCC('test_api_change_control_approval_get_all_without_approve'))
    suite.addTest(TestCvpClientCC('test_api_change_control_create_for_empty_tasks_list'))
    suite.addTest(TestCvpClientCC('test_api_change_control_create_for_none_task_id_in_list'))
    suite.addTest(TestCvpClientCC('test_api_change_control_create_for_none_task_ids_not_list'))
    suite.addTest(TestCvpClientCC('test_api_change_control_create_for_random_task_id'))
    suite.addTest(TestCvpClientCC('test_api_change_control_approve_invalid_tasks'))
    suite.addTest(TestCvpClientCC('test_api_change_control_approve'))
    suite.addTest(TestCvpClientCC('test_api_change_control_approval_get_one'))
    suite.addTest(TestCvpClientCC('test_api_change_control_approval_get_all'))
    suite.addTest(TestCvpClientCC('test_api_change_control_start'))
    suite.addTest(TestCvpClientCC('test_api_change_control_start_invalid_tasks'))
    suite.addTest(TestCvpClientCC('test_api_change_control_stop'))
    suite.addTest(TestCvpClientCC('test_api_change_control_delete_invalid_cc'))
    suite.addTest(TestCvpClientCC('test_api_change_control_delete'))
    return suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())

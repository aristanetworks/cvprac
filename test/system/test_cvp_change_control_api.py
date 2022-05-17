'''
    Tests for change control apis
'''
from pprint import pprint
import time
import unittest
from test_cvp_base import TestCvpClientBase
import urllib3
from cvprac.cvp_client_errors import CvpRequestError
urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning)


CHANGE_CONTROL_ID_INVALID = 'InvalidCVPRACSystestCCID'
INVALID_TASK_ID = 'InvalidCVPRACSystestTASKID'
INVALID_CCID = 'InvalidCVPRACSystestCCID'
APPROVE_NOTE = "Approving CC via cvprac cc system tests"
START_NOTE = "Start the CC via cvprac cc system tests"
STOP_NOTE = "Stop the CC via cvprac cc system tests"
TASK_ID = None


class TestCvpClientCC(TestCvpClientBase):
    """ Test cases for the CvpClientCC class.
    """
    @classmethod
    def setUpClass(cls):
        """ Initialize variables
        """
        super(TestCvpClientCC, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        """ Reset variables value to None
        """
        super(TestCvpClientCC,
              cls).tearDownClass()

    def get_version(self):
        """ Get api version
        """
        if self.clnt.apiversion is None:
            self.api.get_cvp_info()
        if self.clnt.apiversion >= 6.0:
            pprint('RUN TEST FOR V6 (2021.2.0+) CHANGE CONTROL RESOURCE APIs')
            return True
        pprint(f'SKIPPING TEST FOR API - {self.clnt.apiversion}')
        return False

    def get_cc_status(self, cc_id):
        """ Get change control status
        """
        params = f'key.id={cc_id}'
        cc_url = f'/api/resources/changecontrol/v1/ChangeControl?{params}'
        response = self.clnt.get(
            cc_url, timeout=30)
        return response

    def get_device_list(self):
        """ Get device list from inventory
        """
        inventory = self.api.get_inventory()
        device_list = []
        if len(inventory) >= 1:
            # for i in range(0, len(inventory)):
            #     device_list.append(
            #         inventory[i]['serialNumber'])
            device_list = [inventory[i]['serialNumber'] for i in range(len(inventory))]
        else:
            raise Exception("No device found")
        return device_list

    def create_snapshot(self):
        """ Create snapshot for change control with custom stages
        """
        pprint('CREATING SNAPSHOT...')
        device_list = self.get_device_list()
        template_details = {
            "commands": [
                "show version"
            ],
            "deviceList": [
                device_list[0]
            ],
            "frequency": "350",
            "name": "show version"
        }
        response = self.clnt.post(
            '/snapshot/templates/schedule?', data=template_details)
        if response['status'] == "success":
            template_id = response['templateKey']
        else:
            raise Exception(
                "Snapshot not created")
        return template_id

    def delete_snapshot(self, snaps):
        """ Delete snapshot
        """
        pprint('DELETING SNAPSHOT...')
        response = self.clnt.delete(
            '/snapshot/templates?', data=snaps)
        return response

    def create_task(self):
        """ Create new task
        """
        pprint('CREATING TASKS...')
        # global task_id
        (task_id, _) = self._create_task()
        self.task_id = task_id
        return task_id

    def create_change_control_for_task(self, task_id):
        """ Create change control for tasks
        """
        pprint('CREATING CHANGE CONTROL...')
        chg_ctrl = self.api.change_control_create_for_tasks(
            self.cc_id, self.cc_name, [task_id])
        assert chg_ctrl is not None
        assert chg_ctrl['value']['key']['id'] == self.cc_id
        assert chg_ctrl['value']['change']['name'] == self.cc_name
        return chg_ctrl

    def approve_change_control(self):
        """ Approve change control
        """
        pprint('APPROVING CHANGE CONTROL...')
        # Approve the change control
        approve_chg_ctrl = self.api.change_control_approve(
            self.cc_id, notes=APPROVE_NOTE)
        assert approve_chg_ctrl is not None
        assert approve_chg_ctrl['value']['approve']['value'] is True
        assert approve_chg_ctrl['value']['approve']['notes'] == APPROVE_NOTE
        assert approve_chg_ctrl['value']['key']['id'] == self.cc_id
        return approve_chg_ctrl

    def start_change_control(self, cc_id):
        """ Start change control
        """
        pprint('STARTING CHANGE CONTROL...')
        # Start the change control
        start_chg_ctrl = self.api.change_control_start(
            cc_id, notes=START_NOTE)
        assert start_chg_ctrl is not None
        assert start_chg_ctrl['value']['start']['value'] is True
        assert start_chg_ctrl['value']['start']['notes'] == START_NOTE
        assert start_chg_ctrl['value']['key']['id'] == cc_id
        return start_chg_ctrl

    def stop_change_control(self):
        """ Stop change control
        """
        pprint('STOPPING CHANGE CONTROL...')
        # Stop the change control
        stop_chg_ctrl = self.api.change_control_stop(
            self.cc_id, notes=STOP_NOTE)
        assert stop_chg_ctrl is not None
        assert stop_chg_ctrl['value']['start']['value'] is False
        assert stop_chg_ctrl['value']['start']['notes'] == STOP_NOTE
        assert stop_chg_ctrl['value']['key']['id'] == self.cc_id
        return stop_chg_ctrl

    def delete_change_control(self, cc_id):
        """ Delete change control
        """
        pprint('DELETING CHANGE CONTROL...')
        delete_chg_ctrl = self.api.change_control_delete(
            cc_id)
        assert delete_chg_ctrl is not None
        assert delete_chg_ctrl['key']['id'] == self.cc_id
        return delete_chg_ctrl

    def change_control_get_one(self, cc_id):
        """ Change control get one
        """
        chg_ctrl_get_one = self.api.change_control_get_one(
            cc_id)
        return chg_ctrl_get_one

    def cancel_task(self, task_id):
        """ Cancel task
        """
        pprint('CANCELING TASK...')
        data = {'data': [task_id]}
        self.clnt.post(
            '/task/cancelTask.do', data=data)

    def test_api_change_control_create_for_task(self):
        """ Verify change_control_create_for_tasks
        """
        pprint(
            "test_api_change_control_create_for_tasks")
        if self.get_version():
            # Create Task
            task_id = self.create_task()

            # Create change control;
            chg_ctrl = self.create_change_control_for_task(
                task_id)
            time.sleep(1)

            # Verify CC
            response = self.get_cc_status(
                self.cc_id)

            assert response is not None
            assert chg_ctrl['value']['key']['id'] == response['value']['key']['id']
            assert chg_ctrl['value']['change']['name'] == response['value']['change']['name']
            time.sleep(2)

            approve_chg_ctrl = self.approve_change_control()

            # Start change control
            start_chg_ctrl = self.start_change_control(
                self.cc_id)

            # Verify start CC
            response = self.get_cc_status(
                self.cc_id)

            # Verify create CC
            assert response is not None
            assert chg_ctrl['value']['key']['id'] == response['value']['key']['id']
            assert chg_ctrl['value']['change']['name'] == response['value']['change']['name']
            time.sleep(2)

            # Verify approve CC
            assert approve_chg_ctrl['value']['key']['id'] == response['value']['key']['id']
            assert approve_chg_ctrl['value']['approve'][
                'notes'] == response['value']['approve']['notes']
            assert approve_chg_ctrl['value']['approve'][
                'value'] == response['value']['approve']['value']

            # Verify Start CC
            assert start_chg_ctrl['value']['key']['id'] == response['value']['key']['id']
            assert start_chg_ctrl['value']['start']['value'] == response['value']['start']['value']
            assert start_chg_ctrl['value']['start']['notes'] == response['value']['start']['notes']

            # Stop change control
            stop_chg_ctrl = self.stop_change_control()

            # Verify stop CC
            response = self.get_cc_status(
                self.cc_id)

            assert response is not None
            assert stop_chg_ctrl['value']['key']['id'] == response['value']['key']['id']
            assert stop_chg_ctrl['value']['start']['value'] == response['value']['start']['value']
            assert stop_chg_ctrl['value']['start']['notes'] == response['value']['start']['notes']

            # Delete change control
            pprint('DELETING CHANGE CONTROL...')
            self.delete_change_control(self.cc_id)

            # Verify Delete CC
            with self.assertRaises(CvpRequestError):
                self.get_cc_status(self.cc_id)

    def test_api_change_control_approval_get_one(self):
        """ Verify change_control_approval_get_one
         """
        pprint(
            "test_api_change_control_approval_get_one")
        if self.get_version():
            # Create task
            task_id = self.create_task()

            # Create change control
            self.create_change_control_for_task(
                task_id)

            # Approve change control
            self.approve_change_control()

            pprint('APPROVAL GET ONE...')
            approval_get_one = self.api.change_control_approval_get_one(
                self.cc_id)
            assert approval_get_one is not None
            assert approval_get_one['value']['approve']['value'] is True
            assert approval_get_one['value']['approve']['notes'] == APPROVE_NOTE
            assert approval_get_one['value']['key']['id'] == self.cc_id
            time.sleep(1)

            # verify with actual api output

            response = self.get_cc_status(
                self.cc_id)

            assert response is not None
            assert approval_get_one['value']['key']['id'] == response['value']['key']['id']
            assert approval_get_one['value']['approve'][
                'notes'] == response['value']['approve']['notes']
            assert approval_get_one['value']['approve'][
                'value'] == response['value']['approve']['value']

            # Delete change control
            self.delete_change_control(self.cc_id)

            # Cancel Task
            self.cancel_task(task_id)

    def test_api_change_control_approval_get_one_without_approve(self):
        """ Verify change_control_approval_get_one_without_approve
         """
        pprint(
            "test_api_change_control_approval_get_one_without_approve")
        if self.get_version():
            # Create task
            task_id = self.create_task()

            # Create CC
            self.create_change_control_for_task(
                task_id)

            pprint(
                'APPROVAL GET ONE WITHOUT APPROVE...')
            approval_get_one = self.api.change_control_approval_get_one(
                self.cc_id)
            assert approval_get_one is None

            # Delete CC
            self.delete_change_control(self.cc_id)

            # Cancel Task
            self.cancel_task(task_id)

    def test_api_change_control_create_for_empty_tasks_list(self):
        """ Verify change_control_create_for_tasks for empty task list
        """
        pprint(
            "test_api_change_control_create_for_empty_tasks_list")
        if self.get_version():
            # Set client apiversion if it is not already set
            pprint(
                'RUN TEST FOR V3 CHANGE CONTROL APIs')
            with self.assertRaises(CvpRequestError):
                self.create_change_control_for_task(
                    [])

    def test_api_change_control_create_for_none_task_id_in_list(self):
        """ Verify change_control_create_for_tasks for none task id in list
        """
        # Set client apiversion if it is not already set
        pprint(
            "test_api_change_control_create_for_none_task_id_in_list")
        if self.get_version():
            pprint(
                'CREATE CHANGE CONTROL FOR LIST OF NONE TASK IDs...')
            with self.assertRaises(CvpRequestError):
                self.create_change_control_for_task([
                                                     None])

    def test_api_change_control_create_for_none_task_ids_not_list(self):
        """ Verify change_control_create_for_tasks for none task ids list
        """
        # Set client apiversion if it is not already set
        pprint(
            "test_api_change_control_create_for_none_task_ids_not_list")
        if self.get_version():
            pprint(
                'CREATE CHANGE CONTROL FOR NONE TASK IDs...')
            with self.assertRaises(CvpRequestError):
                self.create_change_control_for_task(
                    None)

    def test_api_change_control_create_for_invalid_task_id(self):
        """ Verify change_control_create_for_tasks for invalid task id
        """
        pprint(
            "test_api_change_control_create_for_invalid_task_id")
        # Set client apiversion if it is not already set
        if self.get_version():
            pprint(
                'CREATING CHANGE CONTROL FOR INVALID TASK IDs...')

            # Create change control for random task
            chg_ctrl = self.create_change_control_for_task(
                INVALID_TASK_ID)

            # Approve the change control
            self.approve_change_control()

            # Verify CC
            response = self.get_cc_status(
                self.cc_id)

            assert response is not None
            assert chg_ctrl['value']['key']['id'] == response['value']['key']['id']
            assert chg_ctrl['value']['change']['name'] == response['value']['change']['name']

            # Delete CC
            self.delete_change_control(self.cc_id)

    def test_api_change_control_approve_invalid_tasks(self):
        """ Verify test_api_change_control_approve_invalid_tasks
                """
        pprint(
            "test_api_change_control_approve_invalid_tasks")
        if self.get_version():
            pprint(
                'APPROVING CHANGE CONTROL FOR INVALID TASKS...')
            # Approve the change control
            approve_chg_ctrl = self.api.change_control_approve(
                CHANGE_CONTROL_ID_INVALID, notes=APPROVE_NOTE)
            assert approve_chg_ctrl is None

    def test_api_change_control_start_invalid_tasks(self):
        """ Verify test_api_change_control_start_invalid_tasks
        """
        pprint("test_api_change_control_start_invalid_tasks")
        if self.get_version():
            pprint('STARTING CHANGE CONTROL FOR INVALID TASKS...')
            # Start the change control
            dut = self.duts[0]
            node = dut['node'] + ":443"
            # CVP 2022.1.0 format The forward slashes in the error string are likely a bug
            pprint('SETTING DEFAULT ERROR MESSAGE FORMAT FOR CVP 2022.1.0')
            err_msg = 'POST: https://' + node + '/api/resources/changecontrol/v1/' \
                                                'ChangeControlConfig : Request Error:' \
                                                ' Not Found - {"code":5, "message":"change' \
                                                ' control with ID' \
                                                ' \\\\"InvalidCVPRACSystestCCID\\\\"' \
                                                ' does not exist"}'
            if self.clnt.apiversion < 8.0:
                # CVP 2021.X.X format
                pprint('USING ERROR MESSAGE FORMAT FOR CVP 2021.X.X')
                err_msg = "POST: https://" + node + "/api/resources/changecontrol/v1/" \
                                                    "ChangeControlConfig : Request Error: " \
                                                    "Bad Request -" \
                                                    " {\"code\":9,[ ]?\"message\":\"not approved\"}"
            with self.assertRaisesRegex(CvpRequestError, err_msg):
                self.start_change_control(CHANGE_CONTROL_ID_INVALID)

    def test_api_change_control_delete_invalid_cc(self):
        """ Verify test_api_change_control_delete_invalid_cc
                 """
        pprint(
            "test_api_change_control_delete_invalid_cc")
        if self.get_version():
            pprint('DELETING CHANGE CONTROL...')
            with self.assertRaises(CvpRequestError):
                self.delete_change_control(
                    CHANGE_CONTROL_ID_INVALID)

    def test_api_change_control_get_one(self):
        """ Verify change_control_get_one
         """
        pprint("test_api_change_control_get_one")
        if self.get_version():
            # Create task
            task_id = self.create_task()

            # Create CC
            self.create_change_control_for_task(
                task_id)

            pprint("CHANGE CONTROL GET ONE...")
            # chg_ctrl_get_one = self.api.change_control_get_one(self.cc_id)
            chg_ctrl_get_one = self.change_control_get_one(
                self.cc_id)
            assert chg_ctrl_get_one is not None
            assert chg_ctrl_get_one['value']['key']['id'] == self.cc_id
            assert chg_ctrl_get_one['value']['change']['name'] == self.cc_name
            assert chg_ctrl_get_one['value']['change']['stages']['values']['stage0'] \
                ['action']['args']['values']['TaskID'] == task_id
            # verify with actual api output
            response = self.get_cc_status(
                self.cc_id)
            assert chg_ctrl_get_one['value']['key']['id'] == response['value']['key']['id']
            assert chg_ctrl_get_one['value']['change']['name'] == response['value']['change'][
                'name']
            assert chg_ctrl_get_one['value']['change']['stages']['values']['stage0']['action'] \
                ['args']['values']['TaskID'] == response['value']['change']['stages']['values'] \
                ['stage0']['action']['args']['values']['TaskID']

            # Delete CC
            self.delete_change_control(self.cc_id)

            # Cancel Task
            self.cancel_task(task_id)

    def test_api_change_control_get_one_without_ccid(self):
        """ Verify change_control_get_one_without_ccid
         """
        pprint(
            "test_api_change_control_get_one_without_ccid")
        if self.get_version():
            pprint(
                "CHANGE CONTROL GET ONE WITHOUT CC_ID...")
            err_msg = "change_control_get_one() missing 1 required positional argument: 'cc_id'"
            with self.assertRaises(TypeError) as ex:
                self.change_control_get_one()
                self.assertEqual(
                    err_msg, ex.exception)

    def test_api_change_control_get_one_with_none_ccid(self):
        """ Verify change_control_get_one_with_none_ccid
         """
        pprint(
            "test_api_change_control_get_one_with_none_ccid")
        if self.get_version():
            pprint(
                "CHANGE CONTROL GET WITH NONE CC_ID...")
            chg_ctrl_get_one = self.change_control_get_one(
                None)
            assert chg_ctrl_get_one is None

    def test_api_change_control_get_one_with_invalid_ccid(self):
        """ Verify change_control_get_one_with_invalid_ccid
         """
        pprint(
            "test_api_change_control_get_one_with_invalid_ccid")
        if self.get_version():
            pprint(
                "CHANGE CONTROL GET WITH INVALID CC_ID...")
            chg_ctrl_get_one = self.change_control_get_one(
                INVALID_CCID)
            assert chg_ctrl_get_one is None

    def test_api_change_control_get_all(self):
        """ Verify change_control_get_all
         """
        pprint("test_api_change_control_get_all")
        ids = []
        if self.get_version():
            pprint("CHANGE CONTROL GET ALL...")
            # Create task
            task_id = self.create_task()

            # Create CC
            self.create_change_control_for_task(
                task_id)

            chg_ctrl_get_all = self.api.change_control_get_all()
            for i in range(len(chg_ctrl_get_all['data'])):
                ids.append(chg_ctrl_get_all['data'][i]
                           ['result']['value']['key']['id'])
            assert self.cc_id in ids

            # Delete CC
            self.delete_change_control(self.cc_id)

            # Cancel Task
            self.cancel_task(task_id)

    def test_api_change_control_get_all_without_create_chg_ctrl(self):
        """ Verify change_control_get_all_without_create_chg_ctrl
         """
        pprint("test_api_change_control_get_all_without_create_chg_ctrl")
        ids = []
        if self.get_version():
            pprint("CHANGE CONTROL GET ALL WITHOUT CHANGE CONTROL CREATION...")
            resp = self.api.change_control_get_all()
            if 'data' in resp:
                for i in range(len(resp['data'])):
                    ids.append(resp['data'][i]['result']['value']['key']['id'])
            assert self.cc_id not in ids

    def test_api_change_control_approval_get_all(self):
        """ Verify change_control_approval_get_all
         """
        pprint("test_api_change_control_approval_get_all")
        ids = []
        if self.get_version():
            # Create task
            task_id = self.create_task()

            # Create CC
            self.create_change_control_for_task(
                task_id)

            # Approve CC
            self.approve_change_control()

            pprint(
                "CHANGE CONTROL APPROVAL GET ALL...")
            chg_ctrl_approval_get_all = self.api.change_control_approval_get_all()
            for i in range(len(chg_ctrl_approval_get_all['data'])):
                ids.append(
                    chg_ctrl_approval_get_all['data'][i]['result']['value']['key']['id'])
                if chg_ctrl_approval_get_all['data'][i]['result']['value']['key']['id'] \
                        == self.cc_id:
                    check_index = i
            assert self.cc_id in ids
            assert chg_ctrl_approval_get_all['data'][check_index][
                'result']['value']['approve']['value'] is True

            # Delete CC
            self.delete_change_control(self.cc_id)

            # Cancel Task
            self.cancel_task(task_id)

    def test_api_change_control_approval_get_all_without_approve(self):
        """ Verify change_control_approval_get_all_without_approve
         """
        pprint("test_api_change_control_approval_get_all_without_approve")
        if self.get_version():
            # Create task
            task_id = self.create_task()

            # Create CC
            self.create_change_control_for_task(
                task_id)

            ids = []
            pprint("CHANGE CONTROL APPROVAL GET ALL WITHOUT APPROVE...")
            resp = self.api.change_control_approval_get_all()
            if 'data' in resp:
                for i in range(len(resp['data'])):
                    ids.append(resp['data'][i]['result']['value']['key']['id'])
            assert self.cc_id not in ids

            # Delete CC
            self.delete_change_control(self.cc_id)
            # Cancel Task
            self.cancel_task(task_id)

    def test_api_change_control_create_with_custom_stages(self):
        """ Verify test_api_change_control_create_with_custom_stages
        """
        pprint(
            "test_api_change_control_create_with_custom_stages")
        devices = self.get_device_list()
        if len(devices) > 1:
            device_id_1 = devices[0]
            device_id_2 = devices[1]
        elif len(devices) == 1:
            device_id_1 = devices[0]
            device_id_2 = devices[0]

        template_id = [
            self.create_snapshot(), self.create_snapshot()]
        time.sleep(1)
        custom_cc = {'key': {
            'id': self.cc_id
        },
            'change': {
            'name': self.cc_name,
            'notes': 'cvprac CC',
            'rootStageId': 'root',
            'stages': {'values': {'root': {'name': 'root',
                                           'rows': {'values': [{'values': ['1-2']},
                                                               {'values': ['3']}]
                                                    }
                                           },
                                  '1-2': {'name': 'stages 1-2',
                                          'rows': {'values': [{'values': ['1ab']},
                                                              {'values': ['2']}]}},
                                  '1ab': {'name': 'stage 1ab',
                                          'rows': {'values': [{'values': ['1a', '1b']}]
                                                   }
                                          },
                                  '2': {'name': 'stage 2ab',
                                        'rows': {'values': [{'values': ['2a', '2b']}]
                                                 }
                                        },
                                  '1a': {'action': {'args': {'values': {'DeviceID': device_id_1,
                                                                    'TemplateID': template_id[0]}},
                                                    'name': 'snapshot',
                                                    'timeout': 3000},
                                         'name': 'stage 1a'},
                                  '1b': {'action': {'args': {'values': {'DeviceID': device_id_1,
                                                                    'TemplateID': template_id[0]}},
                                                    'name': 'snapshot',
                                                    'timeout': 3000},
                                         'name': 'stage 1b'},
                                  '2a': {'action': {'args': {'values': {'DeviceID': device_id_1,
                                                                    'TemplateID': template_id[0]}},
                                                    'name': 'snapshot',
                                                    'timeout': 3000},
                                         'name': 'stage 2a'},
                                  '2b': {'action': {'args': {'values': {'DeviceID': device_id_2,
                                                                    'TemplateID': template_id[1]}},
                                                    'name': 'snapshot',
                                                    'timeout': 3000},
                                         'name': 'stage 2a'},
                                  '3': {'action': {'args': {'values': {'DeviceID': device_id_2,
                                                                    'TemplateID': template_id[1]}},
                                                   'name': 'snapshot',
                                                   'timeout': 3000},
                                        'name': 'stage 3'},
                                  }}}}

        if self.get_version():
            pprint(
                "CHANGE CONTROL CREATE WITH CUSTOM STAGES...")
            chg_ctrl_create_with_custom_stages = self.api.change_control_create_with_custom_stages(
                custom_cc)
            assert chg_ctrl_create_with_custom_stages[
                'value']['key']['id'] == self.cc_id
            assert chg_ctrl_create_with_custom_stages[
                'value']['change']['name'] == self.cc_name
            assert chg_ctrl_create_with_custom_stages['value']['change']['stages'][
                'values']['1a']['action']['args']['values']['DeviceID'] == device_id_1
            assert chg_ctrl_create_with_custom_stages['value']['change']['stages'][
                'values']['1a']['action']['args']['values']['TemplateID'] == template_id[0]
            assert chg_ctrl_create_with_custom_stages['value']['change']['stages'][
                'values']['1b']['action']['args']['values']['DeviceID'] == device_id_1
            assert chg_ctrl_create_with_custom_stages['value']['change']['stages'][
                'values']['1b']['action']['args']['values']['TemplateID'] == template_id[0]
            assert chg_ctrl_create_with_custom_stages['value']['change']['stages'][
                'values']['2a']['action']['args']['values']['DeviceID'] == device_id_1
            assert chg_ctrl_create_with_custom_stages['value']['change']['stages'][
                'values']['2a']['action']['args']['values']['TemplateID'] == template_id[0]
            assert chg_ctrl_create_with_custom_stages['value']['change']['stages'][
                'values']['2b']['action']['args']['values']['DeviceID'] == device_id_2
            assert chg_ctrl_create_with_custom_stages['value']['change']['stages'][
                'values']['2b']['action']['args']['values']['TemplateID'] == template_id[1]
            assert chg_ctrl_create_with_custom_stages['value']['change']['stages'][
                'values']['3']['action']['args']['values']['DeviceID'] == device_id_2
            assert chg_ctrl_create_with_custom_stages['value']['change']['stages'][
                'values']['3']['action']['args']['values']['TemplateID'] == template_id[1]

            response = self.get_cc_status(
                self.cc_id)

            assert chg_ctrl_create_with_custom_stages['value'][
                'key']['id'] == response['value']['key']['id']
            assert chg_ctrl_create_with_custom_stages['value'][
                'change']['name'] == response['value']['change']['name']
            assert chg_ctrl_create_with_custom_stages['value']['change']['stages']['values'][
                '1a']['action']['args']['values']['DeviceID'] == response['value']['change'][
                'stages']['values']['1a']['action']['args']['values']['DeviceID']
            assert chg_ctrl_create_with_custom_stages['value']['change']['stages']['values'][
                '1a']['action']['args']['values']['TemplateID'] == response['value']['change'][
                'stages']['values']['1a']['action']['args']['values']['TemplateID']
            assert chg_ctrl_create_with_custom_stages['value']['change']['stages']['values'][
                '1b']['action']['args']['values']['DeviceID'] == response['value']['change'][
                'stages']['values']['1b']['action']['args']['values']['DeviceID']
            assert chg_ctrl_create_with_custom_stages['value']['change']['stages']['values'][
                '1b']['action']['args']['values']['TemplateID'] == response['value']['change'][
                'stages']['values']['1b']['action']['args']['values']['TemplateID']
            assert chg_ctrl_create_with_custom_stages['value']['change']['stages']['values'][
                '2a']['action']['args']['values']['DeviceID'] == response['value']['change'][
                'stages']['values']['2a']['action']['args']['values']['DeviceID']
            assert chg_ctrl_create_with_custom_stages['value']['change']['stages']['values'][
                '2a']['action']['args']['values']['TemplateID'] == response['value']['change'][
                'stages']['values']['2a']['action']['args']['values']['TemplateID']
            assert chg_ctrl_create_with_custom_stages['value']['change']['stages']['values'][
                '2b']['action']['args']['values']['DeviceID'] == response['value']['change'][
                'stages']['values']['2b']['action']['args']['values']['DeviceID']
            assert chg_ctrl_create_with_custom_stages['value']['change']['stages']['values'][
                '2b']['action']['args']['values']['TemplateID'] == response['value']['change'][
                'stages']['values']['2b']['action']['args']['values']['TemplateID']
            assert chg_ctrl_create_with_custom_stages['value']['change']['stages']['values'][
                '3']['action']['args']['values']['DeviceID'] == response['value']['change'][
                'stages']['values']['3']['action']['args']['values']['DeviceID']
            assert chg_ctrl_create_with_custom_stages['value']['change']['stages']['values'][
                '3']['action']['args']['values']['TemplateID'] == response['value']['change'][
                'stages']['values']['3']['action']['args']['values']['TemplateID']
            self.approve_change_control()
            self.start_change_control(self.cc_id)
            time.sleep(1)
            self.stop_change_control()
            self.delete_change_control(self.cc_id)
            delete_snap = self.delete_snapshot(
                template_id)
            assert delete_snap['result'] == 'Success'

    def test_api_change_control_create_with_custom_stages_without_custom_cc(self):
        """ Verify test_api_change_control_create_with_custom_stages
        """
        pprint(
            "test_api_change_control_create_with_custom_stages_without_custom_cc")
        if self.get_version():
            pprint(
                "CHANGE CONTROL CREATE WITH CUSTOM STAGES WITHOUT CUSTOM CC...")
            with self.assertRaises(CvpRequestError):
                self.api.change_control_create_with_custom_stages()

    def test_api_change_control_create_with_custom_stages_with_none_custom_cc(self):
        """ Verify test_api_change_control_create_with_custom_stages
        """
        pprint(
            "test_api_change_control_create_with_custom_stages_with_none_custom_cc")
        if self.get_version():
            pprint(
                "CHANGE CONTROL CREATE WITH CUSTOM STAGES WITH NONE CUSTOM CC...")
            with self.assertRaises(CvpRequestError):
                self.api.change_control_create_with_custom_stages(
                    None)


if __name__ == '__main__':
    unittest.main()

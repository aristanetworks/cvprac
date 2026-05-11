#!/usr/bin/env python3
#
# python3 mlag_issu <upgrade inventory file> <MLAG peer to upgrade: 'peer1' or 'peer2'>"
#
# # Example of upgrade inventory file (YAML)
# cvp_hosts:
#     - 192.168.0.191
#     - 192.168.0.192
#     - 192.168.0.193
# cvp_username: cvpadmin
# target_eos_version: 4.25.4M
# target_terminattr_version: 1.13.6
# mlag_couples:
#     - peer1: leaf101-1
#       peer2: leaf101-2
#     - peer1: leaf102-1
#       peer2: leaf102-2
#
# Note: upgrades are performed in parallel

import sys
import time
from getpass import getpass
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from datetime import datetime
from cvprac.cvp_client import CvpClient
from cvprac.cvp_client_errors import CvpLoginError, CvpApiError
from pprint import pprint
from operator import itemgetter
import yaml

class CvpDeviceUpgrader(object):
    def __init__(self, hosts, username, password):
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        self.cvp_hosts = hosts
        self.cvp_user = username
        self.cvp_password = password
        self.session = self._open_cvp_session()

    def _open_cvp_session(self):
        try:
            client = CvpClient()
            client.connect(
                nodes=self.cvp_hosts,
                username=self.cvp_user,
                password=self.cvp_password,
                request_timeout=300,
                connect_timeout=30
            )
            return(client)
        except CvpLoginError as e:
            print(f"Cannot connect to CVP API: {e}")
            exit()

    def create_mlag_issu_change_control(self, taskIDs, deviceIDs):
        cc_id = f"CC_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        cc_name = f"Change Control {cc_id}"

        stages = {
            'root': {
                'name': f"{cc_name} Root",
                'rows': {'values': [
                    {'values': [f"preU_{cc_id}"]},
                    {'values': [f"U_{cc_id}"]},
                    {'values': [f"postU_{cc_id}"]},
                ]},
            },
            f"preU_{cc_id}": {
                'name': 'pre_upgrade',
                'rows': {'values': [
                    {'values': [f"preU_{cc_id}_{i}" for i in range(len(deviceIDs))]},
                ]},
            },
            f"U_{cc_id}": {
                'name': 'upgrade',
                'rows': {'values': [
                    {'values': [f"U_{cc_id}_{i}" for i in range(len(taskIDs))]},
                ]},
            },
            f"postU_{cc_id}": {
                'name': 'post_upgrade',
                'rows': {'values': [
                    {'values': [f"postU_{cc_id}_{i}" for i in range(len(deviceIDs))]},
                ]},
            },
        }

        for i, device_id in enumerate(deviceIDs):
            stages[f"preU_{cc_id}_{i}"] = {
                'name': 'Check MLAG Health',
                'action': {
                    'name': 'mlaghealthcheck',
                    'timeout': 0,
                    'args': {'values': {'DeviceID': device_id}},
                },
            }
            stages[f"postU_{cc_id}_{i}"] = {
                'name': 'Check MLAG Health',
                'action': {
                    'name': 'mlaghealthcheck',
                    'timeout': 0,
                    'args': {'values': {'DeviceID': device_id}},
                },
            }

        for i, task_id in enumerate(taskIDs):
            stages[f"U_{cc_id}_{i}"] = {
                'name': 'Image Upgrade',
                'action': {
                    'name': 'task',
                    'timeout': 3000,
                    'args': {'values': {'TaskID': task_id}},
                },
            }

        custom_cc = {
            'key': {'id': cc_id},
            'change': {
                'name': cc_name,
                'notes': 'MLAG ISSU Change Control',
                'rootStageId': 'root',
                'stages': {'values': stages},
            },
        }
        try:
            res = self.session.api.change_control_create_with_custom_stages(custom_cc)
        except Exception as e:
            print(str(e))
            return None
        print(f"Change control {cc_id} created")
        return cc_id

    def get_mlag_issu_change_control_logs(self, ccID, startTime):
        end_time = int(time.time() * 1000)
        cc_logs_data = {'category': 'ChangeControl',
            'objectKey': ccID,
            'dataSize': 15000,
            'startTime': startTime,
            'endTime': end_time
        }
        logs = self.session.post('/cvpservice/audit/getLogs.do',
            data=cc_logs_data,
            timeout=self.session.api.request_timeout
        )
        for log in sorted(logs['data'], key=itemgetter('dateTimeInLongFormat')):
            if log['subObjectName'] and 'Command(s)' not in log['activity']:
                log_date = datetime.fromtimestamp(log['dateTimeInLongFormat']/1000)
                print(f"{log_date} {log['subObjectName']}: {log['activity']}")
        return(end_time + 1)

    def run_mlag_issu_change_control(self, ccID):
        print(f"Automatic approval of change control {ccID}")
        self.session.api.change_control_approve(ccID, datetime.utcnow().isoformat() + 'Z')
        time.sleep(2)
        print(f"Starting the execution of change control {ccID}")
        start_time = int(time.time() * 1000)
        self.session.api.change_control_start(ccID)
        time.sleep(2)
        cc = self.session.api.change_control_get_one(ccID)
        cc_status = cc['value']['status']
        cc_error = cc['value'].get('error', '')
        start_time = self.get_mlag_issu_change_control_logs(ccID, start_time)
        while cc_status == 'CHANGE_CONTROL_STATUS_RUNNING':
            time.sleep(30)
            cc = self.session.api.change_control_get_one(ccID)
            cc_status = cc['value']['status']
            cc_error = cc['value'].get('error', '')
            start_time = self.get_mlag_issu_change_control_logs(ccID, start_time)
        print(f"Change control {ccID} final status: {cc_status}")
        if cc_error:
            print(f"Change control {ccID} had the following errors: {cc_error}")
        else:
            print(f"Change control {ccID} completed without errors")

def main():
    if len(sys.argv) != 3:
        print(f"Usage: python3 {sys.argv[0]} <input file path> <MLAG peer to upgrade: peer1/peer2>")
        exit()
    try:
        with open(sys.argv[1], 'r') as yf:
            params = yaml.safe_load(yf)
    except Exception as e:
        print(e)
        exit()
    cvp_password = getpass(prompt=f"CVP password for user {params['cvp_username']}: ")
    cvpdu = CvpDeviceUpgrader(
        hosts=params['cvp_hosts'],
        username=params['cvp_username'],
        password=cvp_password
    )
    image_bundle = None
    for bundle in cvpdu.session.api.get_image_bundles()['data']:
        eos_match = False
        terminattr_match = False
        for img in bundle['imageIds']:
            if params['target_eos_version'] in img:
                eos_match = True
            elif params['target_terminattr_version'] in img:
                terminattr_match = True
        if eos_match and terminattr_match:
            image_bundle = bundle
            break
    if image_bundle is None:
        print(f"Cannot find an image bundle with EOS {params['target_eos_version']} and TerminAttr {params['target_terminattr_version']}")
        exit()
    hostnames = [couple[sys.argv[2]] for couple in params['mlag_couples']]
    devices_to_upgrade = list()
    inventory = cvpdu.session.api.get_inventory()
    for hostname in hostnames:
        provisioned = False
        for dev in inventory:
            if dev['hostname'] == hostname:
                provisioned = True
                devices_to_upgrade.append(dev)
                break
        if not provisioned:
            print(f"Device with hostname {hostname} is not provisioned in CVP")
    if not devices_to_upgrade:
        print('none of the mentioned devices is provisioned in CVP')
        exit()
    print(f"Devices to upgrade: {', '.join([dev['hostname'] for dev in devices_to_upgrade])}")
    task_ids = list()
    for device in devices_to_upgrade:
        response = cvpdu.session.api.apply_image_to_device(image_bundle, device)['data']
        if response['status'] == 'success':
            task_ids.extend(response['taskIds'])
    device_ids = [device['serialNumber'] for device in devices_to_upgrade]
    cc_id = cvpdu.create_mlag_issu_change_control(task_ids, device_ids)
    if cc_id is None:
        print('Failed to create the MLAG ISSU change control')
        exit()
    time.sleep(2)
    cvpdu.run_mlag_issu_change_control(cc_id)

if __name__ == '__main__':
    main()

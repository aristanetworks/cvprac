# Copyright (c) 2022 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.

# This script can be run as a cronjob to periodically reconcile all devices
# that are out of configuration compliance in environments where the running-config
# is still modified via the CLI often.
from cvprac.cvp_client import CvpClient
import ssl
from datetime import datetime
ssl._create_default_https_context = ssl._create_unverified_context
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()
clnt = CvpClient()
clnt.set_log_level(log_level='WARNING')

# Reading the service account token from a file
with open("token.tok") as f:
    token = f.read().strip('\n')

clnt = CvpClient()
clnt.connect(nodes=['cvp1'], username='',password='',api_token=token)

inventory = clnt.api.get_inventory()

compliance = {"0001": "Config is out of sync",
        "0003": "Config & image out of sync",
        "0004": "Config, Image and Device time are in sync",
        "0005": "Device is not reachable",
        "0008": "Config, Image and Extensions are out of sync",
        "0009": "Config and Extensions are out of sync",
        "0012": "Config, Image, Extension and Device time are out of sync",
        "0013": "Config, Image and Device time are out of sync",
        "0014": "Config, Extensions and Device time are out of sync",
        "0016": "Config and Device time are out of sync"
    }

non_compliants = []
taskIds = []
for device in inventory:
    if device['complianceCode'] in compliance.keys():
        # create a list of non-compliant devices for reporting purposes
        non_compliants.append(device['hostname'])
        dev_mac = device['systemMacAddress']
        # check if device already has reconciled config and save the key if it does
        try:
            configlets = clnt.api.get_configlets_by_device_id(dev_mac)
            for configlet in configlets:
                if configlet['reconciled'] == True:
                    configlet_key = configlet['key']
                    break
                else:
                    configlet_key = ""
            rc = clnt.api.get_device_configuration(dev_mac)
            name = 'RECONCILE_' + device['serialNumber']
            update = clnt.api.update_reconcile_configlet(dev_mac, rc, configlet_key, name, True)
            # if the device had no reconciled config, it means we need to append the reconciled
            # configlet to the list of applied configlets on the device
            if configlet_key == "":
                addcfg = clnt.api.apply_configlets_to_device("auto-reconciling",device,[update['data']])
                clnt.api.cancel_task(addcfg['data']['taskIds'][0])            
        except Exception as e:
            continue
print(f"The non compliant devices were: {str(non_compliants)}")

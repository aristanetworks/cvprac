# Copyright (c) 2021 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.

from cvprac.cvp_client import CvpClient
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()

# Create connection to CloudVision
clnt = CvpClient()
clnt.connect(nodes=['cvp1'], username="username",password="password")

configletNames = ['tp-avd_tp-avd-leaf1','vlan144','api_models']

device_name = "tp-avd-leaf1"
device = clnt.api.get_device_by_name(device_name)

configlets = []

for name in configletNames:
    configlets.append(clnt.api.get_configlet_by_name(name))

# Apply configlets in the order specified in the list
clnt.api.apply_configlets_to_device("", device, configlets, reorder_configlets=True)

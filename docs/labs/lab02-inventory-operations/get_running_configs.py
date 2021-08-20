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

# Get the full inventory
inventory = clnt.api.get_inventory()

# Create a list of MAC addresses
device_macs = []
for i in inventory:
    device_macs.append(i['systemMacAddress'])

# Create a dictionary with MAC to running-config mapping
running_configs = {}
for i in device_macs:
    running_configs[i] = clnt.api.get_device_configuration(i)

# Write the running-configs of each device using the hostname as the filename
for i in inventory:
    with open(i['fqdn']+'.cfg', 'w') as f:
        f.write(running_configs[i['systemMacAddress']])
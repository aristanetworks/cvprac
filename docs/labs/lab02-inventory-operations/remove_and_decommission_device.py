# Copyright (c) 2022 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.

from cvprac.cvp_client import CvpClient
import ssl
import uuid
import time
ssl._create_default_https_context = ssl._create_unverified_context
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()

# Create connection to CloudVision
clnt = CvpClient()
clnt.connect(nodes=['cvp1'], username="username", password="password")

device_id = input("Serial number of the device to be decommissioned: ")
request_id = str(uuid.uuid4())
clnt.api.device_decommissioning(device_id, request_id)

# This API call will fully decommission the device, ie remove it from both
# Network Provisioning and Device Inventory (telemetry). It send an eAPI request
# to EOS to shutdown the TerminAttr daemon, waits for streaming to stop and then removes
# the device from provisioning and finally decommissions it. This operation can take a few minutes.
# Supported from CVP 2021.3.0+ and CVaaS.
decomm_status = "DECOMMISSIONING_STATUS_SUCCESS"
decomm_result = ""
while decomm_result != decomm_status:
    decomm_result = clnt.api.device_decommissioning_status_get_one(request_id)['value']['status']
    time.sleep(10)

print(decomm_result)

# Copyright (c) 2021 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.

from cvprac.cvp_client import CvpClient

# Reading the service account token from a file
with open("token.tok") as f:
    token = f.read().strip('\n')

# Create connection to CloudVision
clnt = CvpClient()
clnt.connect(nodes=['cvp1'], username='',password='',api_token=token)

tags_common = [{"key": "topology_hint_pod", "value": "tp-avd-pod1"},
               {"key": "topology_hint_datacenter", "value": "tp-avd-dc1"}]
tags_leaf1 = [{"key": "topology_hint_rack", "value": "tp-avd-leafs1"}]
tags_leaf2 = [{"key": "topology_hint_rack", "value": "tp-avd-leafs2"}]
tags_spines = [{"key": "topology_hint_rack", "value": "tp-avd-spines"}]

# Create workspace
display_name = 'TestTagCVPRAC'
workspace_id = "TestTagCVPRAC"
clnt.api.workspace_config(workspace_id,display_name)

### Create tags
element_type = "ELEMENT_TYPE_DEVICE"

for tag in tags_common+tags_leaf1+tags_leaf2+tags_spines:
    tag_label = tag['key']
    tag_value = tag['value']
    clnt.api.tag_config(element_type, workspace_id, tag_label, tag_value)

### Assign tags
devices = {"leafs1":["BAD032986065E8DC14CBB6472EC314A6","0123F2E4462997EB155B7C50EC148767"],
		   "leafs2":["8520AF39790A4EC959550166DC5DEADE", "6323DA7D2B542B5D09630F87351BEA41"],
		   "spines":["CD0EADBEEA126915EA78E0FB4DC776CA", "2568DB4A33177968A78C4FD5A8232159"]}

for tag in tags_common+tags_leaf1:
    tag_label = tag['key']
    tag_value = tag['value']
    interface_id = ''
    for leaf in devices['leafs1']:
        device_id = leaf
        clnt.api.tag_assignment_config(element_type, workspace_id, tag_label, tag_value, device_id, interface_id)
for tag in tags_common+tags_leaf2:
    tag_label = tag['key']
    tag_value = tag['value']
    interface_id = ''
    for leaf in devices['leafs2']:
        device_id = leaf
        clnt.api.tag_assignment_config(element_type, workspace_id, tag_label, tag_value, device_id, interface_id)
for tag in tags_common+tags_spines:
    tag_label = tag['key']
    tag_value = tag['value']
    interface_id = ''
    for spine in devices['spines']:
        device_id = spine
        clnt.api.tag_assignment_config(element_type, workspace_id, tag_label, tag_value, device_id, interface_id)

### Start build
request = 'REQUEST_START_BUILD'
request_id = 'b1'
description='testing cvprac build'
clnt.api.workspace_config(workspace_id=workspace_id,display_name=display_name,description=description,request=request,request_id=request_id)

### Check workspace build status and proceed only after it finishes building
b = 0
while b == 0:
    build_id = request_id
    request = clnt.api.workspace_build_status(workspace_id,build_id)
    if request['value']['state'] == 'BUILD_STATE_SUCCESS':
        b = b+1
    else:
        continue

### Submit workspace
request = 'REQUEST_SUBMIT'
request_id = 's1'
clnt.api.workspace_config(workspace_id=workspace_id,display_name=display_name,description=description,request=request,request_id=request_id)

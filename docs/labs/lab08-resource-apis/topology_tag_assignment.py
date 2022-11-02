# Copyright (c) 2021 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.

# In this example we are going to assign topology tags using the tags.v2 workspace aware API
# More details on tag.v2 can be found at https://aristanetworks.github.io/cloudvision-apis/models/tag.v2/
# NOTE: Tag.v2 can be used for assigning both device and interface tags (studios, topology, etc) and it's not
# limited to topology tags only. 
# The following are some of the built-in tags that can be used to modify the Topology rendering:
# topology_hint_type: < core | edge | endpoint | management | leaf | spine  >
# topology_hint_rack: < rack name as string >
# topology_hint_pod: < pod name as string >
# topology_hint_datacenter: < datacenter name as string >
# topology_hint_building: < building name as string >
# topology_hint_floor: < floor name as string >
# topology_network_type: < datacenter | campus | cloud >

from cvprac.cvp_client import CvpClient
import uuid
from datetime import datetime

# Reading the service account token from a file
with open("token.tok") as f:
    token = f.read().strip('\n')

# Create connection to CloudVision
clnt = CvpClient()
clnt.connect(nodes=['cvp1'], username='',password='',api_token=token)

tags_common = [{"key": "topology_hint_pod", "value": "tp-avd-pod1"},
               {"key": "topology_hint_datacenter", "value": "tp-avd-dc1"}]
tags_leaf1 = [{"key": "topology_hint_rack", "value": "tp-avd-leafs1"},
              {"key": "topology_hint_type", "value": "leaf"}]
tags_leaf2 = [{"key": "topology_hint_rack", "value": "tp-avd-leafs2"},
              {"key": "topology_hint_type", "value": "leaf"}]
tags_spines = [{"key": "topology_hint_rack", "value": "tp-avd-spines"},
               {"key": "topology_hint_type", "value": "spine"}]

# Create workspace
display_name = f"Change_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
workspace_id = str(uuid.uuid4())
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
clnt.api.workspace_config(workspace_id=workspace_id, display_name=display_name, 
                                     description=description, request=request, request_id=request_id)

### Check workspace build status and proceed only after it finishes building
b = 0
while b == 0:
    build_id = request_id
    # Requesting for the build status too fast might fail if the build start didn't finish creating
    # the build with the request_id/build_id
    while True:
        try:
            request = clnt.api.workspace_build_status(workspace_id, build_id)
            break
        except Exception as e:
            continue
    if request['value']['state'] == 'BUILD_STATE_SUCCESS':
        b = b+1
    else:
        continue

### Submit workspace
request = 'REQUEST_SUBMIT'
request_id = 's1'
clnt.api.workspace_config(workspace_id=workspace_id,display_name=display_name,description=description,request=request,request_id=request_id)

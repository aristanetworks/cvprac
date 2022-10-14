# Copyright (c) 2021 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.

# This script is an example on provisioning registered devices in CloudVision that is based on
# Arista Test Drive (ATD) and similar to what the ansible playbooks do in
# https://github.com/arista-netdevops-community/atd-avd.
# It does the following:
# - creates and uploads configlets,
# - creates the container hierarchy in Network Provisiong
# - moves the devices to their target containers
# - assigns the configlets to the devices
# - creates a change control from the genereated tasks
# - approves and executes the change control

import uuid
import time
import ssl
from datetime import datetime
from cvprac.cvp_client import CvpClient
ssl._create_default_https_context = ssl._create_unverified_context

# Create connection to CloudVision
clnt = CvpClient()
clnt.connect(['cvp1'],'username', 'password')

# Create container topology
container_name = "DC1_LEAFS"
container_topology = [{"containerName": "ATD_FABRIC", "parentContainerName": 'Tenant'},
                      {"containerName": "ATD_LEAFS", "parentContainerName": 'ATD_FABRIC'},
                      {"containerName": "pod1", "parentContainerName": 'ATD_LEAFS'},
                      {"containerName": "pod2", "parentContainerName": 'ATD_LEAFS'},
                      {"containerName": "ATD_SERVERS", "parentContainerName": 'ATD_FABRIC'},
                      {"containerName": "ATD_SPINES", "parentContainerName": 'ATD_FABRIC'},
                      {"containerName": "ATD_TENANT_NETWORKS", "parentContainerName": 'ATD_FABRIC'}]
for container in container_topology:
    try:
        container_name = container['containerName']
        # Get parent container information
        parent = clnt.api.get_container_by_name(container['parentContainerName'])
        print(f'Creating container {container_name}\n')
        clnt.api.add_container(container_name,parent["name"],parent["key"])
    except Exception as e:
        if "Data already exists in Database" in str(e):
            print ("Container already exists, continuing...")

# Create device mappers
devices = [{'deviceName': "leaf1",
            'configlets': ["BaseIPv4_Leaf1", "AVD_leaf1"],
            "parentContainerName": "pod1"},
           {'deviceName': "leaf2",
            'configlets': ["BaseIPv4_Leaf2", "AVD_leaf2"],
            "parentContainerName": "pod1"},
           {'deviceName': "leaf3",
            'configlets': ["BaseIPv4_Leaf3", "AVD_leaf3"],
            "parentContainerName": "pod2"},
           {'deviceName': "leaf4",
            'configlets': ["BaseIPv4_Leaf4", "AVD_leaf4"],
            "parentContainerName": "pod2"},
           {'deviceName': "spine1",
            'configlets': ["BaseIPv4_Spine1", "AVD_spine1"],
            "parentContainerName": "ATD_SPINES"},
           {'deviceName': "spine2",
            'configlets': ["BaseIPv4_Spine2", "AVD_spine2"],
            "parentContainerName": "ATD_SPINES"}]

task_list = []
for device in devices:
    # Load the AVD configlets from file
    with open("./configlets/AVD_" + device['deviceName'] + ".cfg", "r") as file:
        configlet_file = file.read()
    avd_configlet_name = device['configlets'][1]
    base_configlet_name = device['configlets'][0] # preloaded configlet in an ATD environment
    container_name = device['parentContainerName']
    base_configlet = clnt.api.get_configlet_by_name(base_configlet_name)
    configlets = [base_configlet]
    # Update the AVD configlets if they exist, otherwise upload them from the configlets folder
    print (f"Creating configlet {avd_configlet_name} for {device['deviceName']}\n")
    try:
        configlet = clnt.api.get_configlet_by_name(avd_configlet_name)
        clnt.api.update_configlet(configlet_file, configlet['key'], avd_configlet_name)
        configlets.append(configlet)
    except:
        clnt.api.add_configlet(avd_configlet_name, configlet_file)
        configlet = clnt.api.get_configlet_by_name(avd_configlet_name)
        configlets.append(configlet)
    # Get device data
    device_data = clnt.api.get_device_by_name(device['deviceName'] + ".atd.lab")
    # Get the parent container data for the device
    container = clnt.api.get_container_by_name(container_name)
    device_name = device['deviceName']
    print(f"Moving device {device_name} to container {container_name}\n")
    # The move action will create the task first, however if the devices are already in the target
    # container, for instance if the script was run multiple times than the move action will
    # not generate a task anymore, therefore it's better to create the task list from the
    # Update Config action which will reuse the Move Device action's task if one exists,
    # otherwise will create a new one.
    move = clnt.api.move_device_to_container("python", device_data, container)
    apply_configlets = clnt.api.apply_configlets_to_device("", device_data, configlets)
    task_list = task_list + apply_configlets['data']['taskIds']

print(f"Generated task IDs are: {task_list}\n")

# Generate unique ID for the change control
cc_id = str(uuid.uuid4())
cc_name = f"Change_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

print("Creating Change control with the list of tasks")
clnt.api.change_control_create_for_tasks(cc_id, cc_name, task_list, series=False)

print("Approving Change Control")
# adding a few seconds sleep to avoid small time diff between the local system and CVP
time.sleep(2)
approve_note = "Approving CC via cvprac"
clnt.api.change_control_approve(cc_id, notes=approve_note)

# Start the change control
print("Executing Change Control...")
start_note = "Start the CC via cvprac"
clnt.api.change_control_start(cc_id, notes=start_note)

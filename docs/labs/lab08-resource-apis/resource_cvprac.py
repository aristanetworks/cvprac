# Copyright (c) 2021 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.

from cvprac.cvp_client import CvpClient
from pprint import pprint as pp
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()

# Reading the service account token from a file
with open("token.tok") as f:
    token = f.read().strip('\n')

clnt = CvpClient()
clnt.connect(nodes=['cvp1'], username='',password='',api_token=token)

def get_events_all(client):
    ''' Get All events '''
    event_url = '/api/resources/event/v1/Event/all'
    response = client.get(event_url)
    return response['data']

def get_event(client, key, ts):
    event_url = '/api/resources/event/v1/Event?'
    url = event_url + 'key.key=' + key + "&key.timestamp=" + ts
    response = client.get(url)
    return response

def get_events_t1_t2(client, t1, t2):
    event_url = '/api/resources/event/v1/Event/all?'
    url = event_url + 'time.start=' + t1 + "&time.end=" + t2
    response = client.get(url)
    return response['data']

def get_events_by_severity(client, severity):
    payload = {"partialEqFilter": [{"severity": severity }]}
    event_url = '/api/resources/event/v1/Event/all'
    response = client.post(event_url, data=payload)
    if 'data' in response.keys():
        return response['data']
    else:
        return response

def get_events_by_type(client, etype):
    payload = {"partialEqFilter": [{"eventType": etype }]}
    event_url = '/api/resources/event/v1/Event/all'
    response = client.post(event_url, data=payload)
    if 'data' in response.keys():
        return response['data']
    else:
        return response

def get_active_devices(client):
    ''' Get active devices '''
    dev_url = '/api/resources/inventory/v1/Device/all'
    devices_data = client.get(dev_url)
    devices = []
    for device in devices_data['data']:
        try:
            if device['result']['value']['streamingStatus'] == "STREAMING_STATUS_ACTIVE":
                devices.append(device['result']['value']['hostname'])
        # pass on archived datasets
        except KeyError as e:
            continue
    return devices

def get_all_device_tags(client):
    tag_url = '/api/resources/tag/v1/DeviceTag/all'
    tag_data = client.get(tag_url)
    tags = []
    for tag in tag_data['data']:
        tags.append({tag['result']['value']['key']['label']:tag['result']['value']['key']['value']})
    return tags

def get_all_interface_tags(client):
    tag_url = '/api/resources/tag/v1/InterfaceTagAssignmentConfig/all'
    tags = client.get(tag_url)
    return tags['data']

def filter_interface_tag(client, dId=None, ifId=None, label=None, value=None):
    tag_url = '/api/resources/tag/v1/InterfaceTagAssignmentConfig/all'
    payload = {
                "partialEqFilter": [
                    {"key": {"deviceId": dId, "interfaceId": ifId, "label": label, "value": value}}
                ]
            }
    response = client.post(tag_url, data=payload)
    return response

def create_itag(client, label, value):
    tag_url = '/api/resources/tag/v1/InterfaceTagConfig'
    payload = {"key":{"label":label,"value":value}}
    response = client.post(tag_url, data=payload)
    return response

def assign_itag(client, dId, ifId, label, value):
    tag_url = '/api/resources/tag/v1/InterfaceTagAssignmentConfig'
    payload = {"key":{"label":label, "value":value, "deviceId": dId, "interfaceId": ifId}}
    response = client.post(tag_url, data=payload)
    return response

def create_dtag(client, label, value):
    tag_url = '/api/resources/tag/v1/DeviceTagConfig'
    payload = {"key":{"label":label,"value":value}}
    response = client.post(tag_url, data=payload)
    return response

def assign_dtag(client, dId, label, value):
    tag_url = '/api/resources/tag/v1/DeviceTagAssignmentConfig'
    payload = {"key":{"label":label, "value":value, "deviceId": dId}}
    response = client.post(tag_url, data=payload)
    return response

### Uncomment the below functions/print statement to test

# ### Get all active events
# print ('=== All active events ===')
# cvpevents = get_events_all(clnt)
# for event in cvpevents:
#     print(event)

# ### Get a specific event
# key = "6098ae39e4c8a9d7"
# ts ="2021-04-06T21:53:00Z"
# get_event(clnt, key, ts)

# ### Get events between two dates
# t1 = "2021-04-06T09:00:00Z"
# t2 = "2021-04-06T14:00:00Z"
# events = get_events_t1_t2(clnt, t1, t2)
# print(f"=== Events between {t1} and {t2} ===")
# pp(events)

# ### Get all INFO severity events ###
# # EVENT_SEVERITY_UNSPECIFIED = 0
# # EVENT_SEVERITY_INFO =	1
# # EVENT_SEVERITY_WARNING = 2
# # EVENT_SEVERITY_ERROR = 3
# # EVENT_SEVERITY_CRITICAL =	4
# ####################################

# severity = 1 ## Severity INFO
# info = get_events_by_severity(clnt, severity)
# print('=== Get all INFO severity events ===')
# pp(info)

# ### Get specific event types

# etype = "LOW_DEVICE_DISK_SPACE"
# event = get_events_by_type(clnt, etype)
# print('=== Get all Low Disk Space events ===')
# pp(event)

# ### Get the inventory
# print ('=== Inventory ===')
# print(get_active_devices(clnt))

# ### Get all devie tags
# print('=== Device Tags ===' )
# for tag in get_all_device_tags(clnt):
#     print (tag)

# ### Get all interface tag assignments
# print(get_all_interface_tags(clnt))

# ### Get all interfaces that have a tag with a specific value on a device
# print(filter_interface_tag(clnt, dId="JPE14070534", value="speed40Gbps"))

# ### Get all tags for an interface of a device
# print(filter_interface_tag(clnt, dId="JPE14070534", ifId="Ethernet1"))

# ### Get all interfaces that have a specific tag assigned
# print(filter_interface_tag(clnt, dId="JPE14070534", label="lldp_hostname"))

# ### Create an interface tag
# create_itag(clnt, "lldp_chassis", "50:08:00:0d:00:48")

# ### Assign an interface tag
# assign_itag(clnt, "JPE14070534", "Ethernet4", "lldp_chassis", "50:08:00:0d:00:38")

# ### Create a device tag
# create_dtag(clnt, "topology_hint_pod", "ire-pod11")

# ### Assign an interface tag
# assign_dtag(clnt, "JPE14070534", "topology_hint_pod", "ire-pod11" )

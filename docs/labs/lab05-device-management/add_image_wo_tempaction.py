# Copyright (c) 2021 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.

from cvprac.cvp_client import CvpClient
import json
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()

# Create connection to CloudVision
clnt = CvpClient()
clnt.connect(['cvp1'],'username', 'password')

image_name = "vEOS-4.26.0.1F"
image = clnt.api.get_image_bundle_by_name(image_name)

device_name = "tp-avd-leaf2"
device  = clnt.api.get_device_by_name(device_name)

def apply_image_to_element_no_temp(image, element, name, id_type, create_task=True):
    ''' Apply an image bundle to a device or container
        A copy of the appl_image_to_element() function without creating a tempAction.
        Useful in situations where we need to call saveTopology on a per tempAction basis,
        which is only possible if the addTempAction function is not used and the data
        that we would've passed in the addTempAction call is passed in the
        saveTopology call.
        Args:
            image (dict): The image info.
            element (dict): Info about the element to apply an image to. Dict
                can contain device info or container info.
            name (str): Name of the element the image is being applied to.
            id_type (str): - Id type of the element the image is being applied to
                            - can be 'netelement' or 'container'
            create_task (bool): Determines whether or not to execute a save
                and create the tasks (if any)
        Returns:
            response (list): A list that contains the tempAction data
                Ex: [{'NetworkRollbackTask': False,
                      'taskJson': '[{
                        "info": "Apply image: vEOS-4.26.0.1F to netelement tp-avd-leaf2",
                        "infoPreview": "Apply image: vEOS-4.26.0.1F to netelement tp-avd-leaf2",
                        "note": "",
                        "action": "associate", "nodeType":
                        "imagebundle",
                        "nodeId": "imagebundle_1622072231719691917",
                        "toId": "50:08:00:b1:5b:0b",
                        "toIdType": "netelement",
                        "fromId": "",
                        "nodeName": "vEOS-4.26.0.1F",
                        "fromName": "", "
                        toName": "tp-avd-leaf2",
                        "childTasks": [],
                        "parentTask": ""}]'}]
    '''

    print('Attempt to apply %s to %s %s' % (image['name'],
                                                        id_type, name))
    info = 'Apply image: %s to %s %s' % (image['name'], id_type, name)
    node_id = ''
    if 'imageBundleKeys' in image:
        if image['imageBundleKeys']:
            node_id = image['imageBundleKeys'][0]
        print('Provided image is an image object.'
                        ' Using first value from imageBundleKeys - %s'
                        % node_id)
    if 'id' in image:
        node_id = image['id']
        print('Provided image is an image bundle object.'
                        ' Found v1 API id field - %s' % node_id)
    elif 'key' in image:
        node_id = image['key']
        print('Provided image is an image bundle object.'
                        ' Found v2 API key field - %s' % node_id)
    data = [
      {
      "NetworkRollbackTask": False,
      "taskJson": json.dumps([{'info': info,
                        'infoPreview': info,
                        'note': '',
                        'action': 'associate',
                        'nodeType': 'imagebundle',
                        'nodeId': node_id,
                        'toId': element['key'],
                        'toIdType': id_type,
                        'fromId': '',
                        'nodeName': image['name'],
                        'fromName': '',
                        'toName': name,
                        'childTasks': [],
                        'parentTask': ''}])
      }
    ]
    return data

create_task = False
tempAction = apply_image_to_element_no_temp(image, device, device['fqdn'], 'netelement', create_task)

clnt.api._save_topology_v2(tempAction)
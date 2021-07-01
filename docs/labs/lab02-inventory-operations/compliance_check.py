# Copyright (c) 2021 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.

from cvprac.cvp_client import CvpClient
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()

### Compliance Code description
compliance = {"0000":"Configuration is in sync",
              "0001": "Config is out of sync",
              "0002": "Image is out of sync",
              "0003": "Config & image out of sync",
              "0004": "Config, Image and Device time are in sync",
              "0005": "Device is not reachable",
              "0006": "The current EOS version on this device is not supported by CVP. Upgrade the device to manage.",
              "0007": "Extensions are out of sync",
              "0008": "Config, Image and Extensions are out of sync",
              "0009": "Config and Extensions are out of sync",
              "0010": "Image and Extensions are out of sync",
              "0011": "Unauthorized User",
              "0012": "Config, Image, Extension and Device time are out of sync",
              "0013": "Config, Image and Device time are out of sync",
              "0014": "Config, Extensions and Device time are out of sync",
              "0015": "Image, Extensions and Device time are out of sync",
              "0016": "Config and Device time are out of sync",
              "0017": "Image and Device time are out of sync",
              "0018": "Extensions and Device time are out of sync",
              "0019": "Device time is out of sync"
}

# Create connection to CloudVision using Service account token
with open("token.tok") as f:
    token = f.read().strip('\n')

clnt = CvpClient()
clnt.connect(nodes=['cvp1'], username='',password='',api_token=token)

def check_devices_under_container(client, container):
    ''' container is the container ID '''

    nodeId = container['key']
    nodeName = container['name']
    api = '/ztp/getAllNetElementList.do?'
    queryParams = "nodeId={}&queryParam=&nodeName={}&startIndex=0&endIndex=0&contextQueryParam=&ignoreAdd=false&useCache=true".format(nodeId, nodeName)
    return client.get(api + queryParams)


container = clnt.api.get_container_by_name('TP_LEAFS')

devices = (check_devices_under_container(clnt,container))

for device in devices['netElementList']:
    code = device['complianceCode']
    print(device['fqdn'], ' ', code,' ', compliance[code])

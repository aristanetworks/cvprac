# Copyright (c) 2021 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.

from cvprac.cvp_client import CvpClient
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()

# Create connection to CloudVision
with open("token.tok") as f:
    token = f.read().strip('\n')

clnt = CvpClient()
clnt.connect(nodes=['cvp1'], username='',password='',api_token=token)

container = clnt.api.get_container_by_name('TP_LEAFS') # container object

app_name = "my app" # can be any string

device = {"key":"00:1c:73:c5:4c:87", "fqdn":"co633.ire.aristanetworks.com"}

move_device_to_container(app_name, device, container)

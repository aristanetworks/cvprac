# Copyright (c) 2021 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.

from cvprac.cvp_client import CvpClient
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()

# Create connection to CloudVision using Service account token
with open("token.tok") as f:
    token = f.read().strip('\n')

clnt = CvpClient()
clnt.connect(nodes=['cvp1'], username='', password='', api_token=token)

devices = ["50:08:00:a7:ca:c3","50:08:00:b1:5b:0b","50:08:00:60:c6:76",
           "50:08:00:25:9d:36","50:08:00:8b:ee:b1","50:08:00:8c:22:49"]

clnt.api.delete_devices(devices)

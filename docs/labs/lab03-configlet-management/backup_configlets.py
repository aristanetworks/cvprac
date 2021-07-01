# Copyright (c) 2021 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.
#
# Get configlets and save them to individual files
from cvprac.cvp_client import CvpClient
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()

# Create connection to CloudVision
clnt = CvpClient()
clnt.connect(['cvp1'],'username', 'password')

configlets = clnt.api.get_configlets(start=0,end=0)

for configlet in configlets['data']:
    with open(configlet['name'],'w') as f:
        f.write(configlet['config'])

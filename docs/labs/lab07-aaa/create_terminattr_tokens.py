# Copyright (c) 2021 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.
#
# Example script to generate the TerminAttr token via REST API from CVaaS and CV on-prem
# and save them to a file

from cvprac.cvp_client import CvpClient
from pprint import pprint as pp
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()

# Reading the service account token from a file
with open("cvaas.tok") as f:
    token = f.read().strip('\n')

clnt = CvpClient()
clnt.connect(nodes=['www.arista.io'], username='',password='',is_cvaas=True, api_token=token)

terminattr_token = clnt.api.create_enroll_token('720h')
with open('cv-onboarding-token', 'w') as f:
    f.write(terminattr_token[0]['enrollmentToken']['token'])

primary = CvpClient()
primary.connect(nodes=['cvp1'], username='username',password='password')

terminattr_token = primary.api.create_enroll_token('720h')

with open('token', 'w') as f:
    f.write(terminattr_token['data'])

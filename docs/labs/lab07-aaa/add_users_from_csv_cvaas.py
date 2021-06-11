# Copyright (c) 2021 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.

from cvprac.cvp_client import CvpClient
from cvprac.cvp_client_errors import CvpApiError
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()
from cvprac.cvp_client import CvpClient
import csv

# Create connection to CloudVision using Service Account token
with open("cvaas.tok") as f:
    token = f.read().strip('\n')

clnt = CvpClient()
clnt.connect(nodes=['www.arista.io'], username='', password='', is_cvaas=True, api_token=token)


with open("aaa_users.csv") as csvfile:
    for i in csv.DictReader(csvfile):
        data = dict(i)
        try:
            clnt.api.add_user(data['username'], "", data['role'], data['status'], data['first_name'], data['last_name'], data['email'], data['user_type'])
        except CvpApiError as e:
            print(e)
        print ("Adding user {} to CVaaS".format(data['username']))

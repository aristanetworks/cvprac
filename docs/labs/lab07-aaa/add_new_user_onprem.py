# Copyright (c) 2021 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.

from cvprac.cvp_client import CvpClient
from cvprac.cvp_client_errors import CvpApiError
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()
from getpass import getpass

# Create connection to CloudVision
clnt = CvpClient()
clnt.connect(['cvp1'],'username', 'password')

username = "cvpuser2"
password = getpass()
role = "network-admin"
status = "Enabled"
first_name = "Cloud"
last_name = "Vision"
email = "cvp@arista.com"
utype = "TACACS"

try:
    clnt.api.add_user(username,password,role,status,first_name,last_name,email,utype)
except CvpApiError as e:
    print(e)

# Copyright (c) 2021 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.

from cvprac.cvp_client import CvpClient
from cvprac.cvp_client_errors import CvpApiError
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()

# Create connection to CloudVision using user/password (on-prem only)
clnt = CvpClient()
clnt.connect(['cvp1'],'username', 'password')

username = "cvprac2"
duration = "31536000s" # 1 year validity
description = "test cvprac"
svc_token = clnt.api.svc_account_token_set(username, duration, description)

# Write the token to file in <username>.tok format
with open(svc_token[0]['value']['user'] + ".tok", "w") as f:
    f.write(svc_token[0]['value']['token'])

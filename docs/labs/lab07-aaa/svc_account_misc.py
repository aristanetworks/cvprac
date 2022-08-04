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

# Get all service accounts states

accounts = clnt.api.svc_account_get_all()

# Get specific service account state

account = clnt.api.svc_account_get_one("cvprac2")

# Get all service account token states

tokens = clnt.api.svc_account_token_get_all()

# Get specific token state

token = clnt.api.svc_account_token_get_one("9bfb39ff892c81d6ac9f25ff95d0389719595feb")

# Delete a service account token

clnt.api.svc_account_token_delete("9bfb39ff892c81d6ac9f25ff95d0389719595feb")

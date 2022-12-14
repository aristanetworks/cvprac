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

svc_accounts = clnt.api.svc_account_get_all()
created_by = 'john.smith'

# Delete service accounts created by user john.smith
for account in svc_accounts:
    if account['value']['created_by'] == created_by:
        clnt.api.svc_account_delete(account['value']['key']['name'])

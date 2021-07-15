# Copyright (c) 2021 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.

from cvprac.cvp_client import CvpClient
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()
from datetime import datetime

# Note API token auth method is not yet supported with Change Controls
clnt = CvpClient()
clnt.connect(['cvp1'],'username', 'password')

ccid = 'cvprac0904211418'
name = "cvprac CC test"
tlist = ['1021','1020','1019','1018']

### Create Change control with the list of tasks
clnt.api.create_change_control_v3(ccid, name, tlist)

### Approve CC
clnt.api.approve_change_control('cvprac0904211418', timestamp=datetime.utcnow().isoformat() + 'Z')

### Execute CC
clnt.api.execute_change_controls(['cvprac0904211418'])

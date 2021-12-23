# Copyright (c) 2021 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.
#
# NOTE: The following example is using the new Change Control Resource APIs supported in 2021.2.0 or newer and in CVaaS.
# For CVaaS service-account token based auth has to be used.

from cvprac.cvp_client import CvpClient
import ssl
import uuid
from datetime import datetime
ssl._create_default_https_context = ssl._create_unverified_context
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()

# Create connection to CloudVision
clnt = CvpClient()
clnt.connect(['cvp1'],'username', 'password')

# Generate change control id and change control name
cc_id = str(uuid.uuid4())
name = f"Change_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# Select the tasks and create a CC where all tasks will be run in parallel
tasks = ["1249","1250","1251","1252"]
clnt.api.change_control_create_for_tasks(cc_id, name, tasks, series=False)

# Approve the change control
approve_note = "Approving CC via cvprac"
clnt.api.change_control_approve(cc_id, notes=approve_note)

# # Schedule the change control
# # Executing scheduled CCs might only work post 2021.3.0+
# schedule_note = "Scheduling CC via cvprac"
# schedule_time = "2021-12-23T03:17:00Z"
# clnt.api.change_control_schedule(cc_id,schedule_time,notes=schedule_note)

# Start the change control
start_note = "Start the CC via cvprac"
clnt.api.change_control_start(cc_id, notes=start_note)
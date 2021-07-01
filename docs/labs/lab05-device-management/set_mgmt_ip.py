# Copyright (c) 2021 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.

from cvprac.cvp_client import CvpClient
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()

# Create connection to CloudVision
clnt = CvpClient()
clnt.connect(['cvp1'],'username', 'password')


data = {"data":[{"info":"Device IP Address Changed",
                "infoPreview":"<b> Device IP Address Changed to 10.83.13.214</b>",
                "action":"associate",
                "nodeType":"ipaddress",
                "nodeId":"",
                "toId":"50:08:00:a7:ca:c3",          # MAC of the device
                "fromId":"",
                "nodeName":"",
                "fromName":"",
                "toName":"tp-avd-leaf1",             # hostname
                "toIdType":"netelement",
                "nodeIpAddress":"10.83.13.219",      # the temporary management IP Address
                "nodeTargetIpAddress":"10.83.13.214" # the final management IP address
                }
            ]
        }
clnt.api._add_temp_action(data)

clnt.api._save_topology_v2([])

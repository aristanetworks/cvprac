# Copyright (c) 2020 Arista Networks, Inc.
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

container_id = clnt.api.get_container_by_name("TP_LEAFS")['key']
builder_name = 'SYS_TelemetryBuilderV3'
configletBuilderID = clnt.api.get_configlet_by_name(builder_name)['key']

payload = {"previewValues":[{
                            "fieldId":"vrf",
                            "value":"red"}],
            "configletBuilderId":configletBuilderID,
            "netElementIds":[],
            "pageType":"container",
            "containerId":container_id,
            "containerToId":"",
            "mode":"assign"}

preview = clnt.post('/configlet/configletBuilderPreview.do', data=payload)

generated_names_list = []
generated_keys_list = []

for i in preview['data']:
  generated_names_list.append(i['configlet']['name'])
  generated_keys_list.append(i['configlet']['key'])

clnt.get("/configlet/searchConfiglets.do?objectId={}&objectType=container&type=ignoreDraft&queryparam={}&startIndex=0&endIndex=22&sortByColumn=&sortOrder=".format(container_id, builder_name.lower()))

tempData = {"data":[{
    "info":"Configlet Assign: to container TP_LEAFS",
    "infoPreview":"<b>Configlet Assign:</b> to container  TP_LEAFS",
    "action":"associate",
    "nodeType":"configlet",
    "nodeId":"",
    "toId":container_id,
    "fromId":"","nodeName":"","fromName":"",
    "toName":"TP_LEAFS",
    "toIdType":"container",
    "configletList":generated_keys_list,
    "configletNamesList":generated_names_list,
    "ignoreConfigletList":[],
    "ignoreConfigletNamesList":[],
    "configletBuilderList":[configletBuilderID],
    "configletBuilderNamesList":[builder_name],
    "ignoreConfigletBuilderList":[],
    "ignoreConfigletBuilderNamesList":[]
    }
    ]
    }

clnt.api._add_temp_action(tempData)
clnt.api._save_topology_v2([])

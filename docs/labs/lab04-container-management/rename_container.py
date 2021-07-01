from cvprac.cvp_client import CvpClient
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()

# Create connection to CloudVision
clnt = CvpClient()
clnt.connect(['cvp1'],'username', 'password')
oldName = "test"
newName = "test121"

container_id = clnt.api.get_container_by_name(oldName)['key']

data = {"data":[{"info": "Container {} renamed from {}".format(newName, oldName),
                "infoPreview": "Container {} renamed from {}".format(newName, oldName),
                "action": "update",
                "nodeType": "container",
                "nodeId": container_id,
                "toId":"",
                "fromId":"",
                "nodeName": newName,
                "fromName": "",
                "toName": "",
                "toIdType": "container",
                "oldNodeName": oldName
                }
            ]
        }

clnt.api._add_temp_action(data)
clnt.api._save_topology_v2([])

from cvprac.cvp_client import CvpClient
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()

clnt = CvpClient()
clnt.connect(nodes=['cvp1'], username="username",password="password")

ts = "2021-11-19T15:04:05.0Z" # rfc3339 time
uri = "/api/v3/services/compliancecheck.Compliance/GetConfig"

# Fetch the inventory
inventory = clnt.api.get_inventory()

# Iterate through all devices and get the running-config at the specified time for each device
for device in inventory:
    sn = device['serialNumber']
    data = {"request":{
        "device_id": sn,
        "timestamp": ts,
        "type":"RUNNING_CONFIG"
        }
    }
    try:
        resultRunningConfig = clnt.post(uri, data=data)[0]['config']
        with open(device['hostname']+'.cfg','w') as f:
            f.write(resultRunningConfig)
    except Exception as e:
        print("Not able to get configuration for device {} - exception {}".format(device['fqdn'], e))

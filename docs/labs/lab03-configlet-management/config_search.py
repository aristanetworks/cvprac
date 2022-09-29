# Copyright (c) 2022 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.

from cvprac.cvp_client import CvpClient
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()

# Create connection to CloudVision
clnt = CvpClient()
clnt.connect(nodes=['cvp1'], username="username",password="password")

def main():

   print('Retrieving configlets ...')

   inventory = clnt.api.get_inventory()
   data = clnt.api.get_configlets_and_mappers()['data']
   print(data)

   print('Number of configlets:', len(data['configlets']))

   searchAgain = True
   while searchAgain:
        try:
            search = input( "\nEnter Config Line: " )
            print(f"\n\n\'{search}\' has been found in following configlets:\n\n")
            print(f"{'Hostname':<30}{'Serial number':<50}{'MAC address':<30}{'Configlets':<40}")
            print("=" * 150)
            for i in inventory:
                device = i['hostname']
                device_sn = i['serialNumber']
                device_mac = i['systemMacAddress']
                configlet_list = []
                for c in data['configlets']:
                    for g in data['generatedConfigletMappers']:
                        if device_mac == g['netElementId'] and c['key'] == g['configletBuilderId'] and search in c['config']:
                            configlet_list.append(c['name'])
                    for k in data['configletMappers']:
                        if device_mac == k['objectId'] and c['key'] == k['configletId'] and search in c['config']:
                            configlet_list.append(c['name'])
                configlet_list_final = ",".join(configlet_list)
                if len(configlet_list) > 0:                
                    print(f"{device:<30}{device_sn:<50}{device_mac:<30}{configlet_list_final:<30}")

        except KeyboardInterrupt:
            print('\nExiting... \n')
            return

if __name__ == '__main__':
   main()


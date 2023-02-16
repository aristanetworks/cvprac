# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.

from cvprac.cvp_client import CvpClient
import ssl
import argparse
ssl._create_default_https_context = ssl._create_unverified_context
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()

# Create connection to CloudVision
clnt = CvpClient()
clnt.connect(nodes=['cvp1'], username="username", password="password")

parser = argparse.ArgumentParser(
    description='Get the list of devices and containers a configlet is attached to')
parser.add_argument('-c', '--configlet', required=True, help='The name of the configlet')
args = parser.parse_args()

configlet_name = args.configlet
devices = clnt.api.get_applied_devices(configlet_name)

containers = clnt.api.get_applied_containers(configlet_name)
print(f"Total number of devices {configlet_name} is attached to: {devices['total']}\n")
print(f"Total number of containers {configlet_name} is attached to: {containers['total']}\n")
col1 = "Device FQDN/hostname"
col2 = "IP Address"
print(f"{col1:<40}{col2:<40}")
print("="*80)
for device in devices['data']:
    print(f"{device['hostName']:<40}{device['ipAddress']}")

print("\nList of containers:\n")
for container in containers['data']:
    print(container['containerName'])

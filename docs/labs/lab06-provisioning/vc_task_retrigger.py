# Copyright (c) 2021 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.

# Example on how to re-trigger task creation if a config push task was previously
# cancelled and the device is still config out of sync

from cvprac.cvp_client import CvpClient
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()

# Create connection to CloudVision
clnt = CvpClient()

clnt.connect(nodes=['cvp1'], username="username",password="password")

# Trigger tasks after they were cancelled

devices = ["tp-avd-leaf1", "tp-avd-leaf2", "tp-avd-leaf3", "tp-avd-leaf4", "tp-avd-spine1", "tp-avd-spine2"]

compliance = {"0001": "Config is out of sync",
              "0003": "Config & image out of sync",
              "0004": "Config, Image and Device time are in sync",
              "0005": "Device is not reachable",
              "0008": "Config, Image and Extensions are out of sync",
              "0009": "Config and Extensions are out of sync",
              "0012": "Config, Image, Extension and Device time are out of sync",
              "0013": "Config, Image and Device time are out of sync",
              "0014": "Config, Extensions and Device time are out of sync",
              "0016": "Config and Device time are out of sync",
}

for dev in devices:
   # generate device object
   device = clnt.api.get_device_by_name(dev)
   # generate configlet list
   cl = clnt.api.get_configlets_by_device_id(device['systemMacAddress'])
   # generate a task if config is out of sync
   if device['complianceCode'] in compliance.keys():
      print(clnt.api.apply_configlets_to_device("", device, cl))

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

image_name = "vEOS-4.26.0.1F"
image = clnt.api.get_image_bundle_by_name(image_name)

device_name = "tp-avd-leaf2"
device  = clnt.api.get_device_by_name(device_name)

clnt.api.apply_image_to_device(image, device)

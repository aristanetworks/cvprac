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
clnt.connect(nodes=['cvp1'], username="username",password="password")

container_name = "TP_LEAFS"

configletName = 'cvprac_example2'

container = clnt.api.get_container_by_name(container_name)

configlet = clnt.api.get_configlet_by_name(configletName)

clnt.api.apply_configlets_to_container("", container, [configlet])

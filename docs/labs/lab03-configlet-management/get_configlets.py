# Copyright (c) 2021 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.
#
# Get list of configlets in parallel

from cvprac.cvp_client import CvpClient
import ssl
from concurrent.futures import ThreadPoolExecutor
ssl._create_default_https_context = ssl._create_unverified_context
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()

# Create connection to CloudVision
clnt = CvpClient()

clnt.connect(nodes=['cvp1'], username="username",password="password")

import time
from functools import wraps

def get_list_of_configlets(configlets):
    """
    Create a thread pool and download specified urls
    """

    futures_list = []
    results = []

    with ThreadPoolExecutor(max_workers=40) as executor:
        for configlet in configlets:
            futures = executor.submit(clnt.api.get_configlet_by_name, configlet)
            futures_list.append(futures)

        for future in futures_list:
            try:
                result = future.result(timeout=60)
                results.append(result)
            except Exception:
                results.append(None)
    return results

if __name__ == "__main__":
    # Example with pre-defined list
    configlets = ["tp-avd_tp-avd-leaf1","tp-avd_tp-avd-leaf2","tp-avd_tp-avd-leaf3","tp-avd_tp-avd-leaf4"]

    # Example with loading list of configlets from a file
    # with open("configlet_list.txt") as f:
    #     configlets = f.read().splitlines()

    results = get_list_of_configlets(configlets)
    for result in results:
        print(result)

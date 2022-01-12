# Copyright (c) 2021 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.
#
# Get configlets and save them to individual files using multi threading
from cvprac.cvp_client import CvpClient
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()
from concurrent.futures import ThreadPoolExecutor
from functools import wraps

# Create connection to CloudVision
clnt = CvpClient()
clnt.connect(['cvp1'],'username', 'password')

total = clnt.api.get_configlets(start=0,end=1)['total']

def get_list_of_configlets():
    """
    Create a thread pool and download specified urls
    """

    futures_list = []
    results = []

    with ThreadPoolExecutor(max_workers=40) as executor:
        for i in range(0,total+1,10):
            futures = executor.submit(clnt.api.get_configlets, start=i,end=i+10)
            futures_list.append(futures)

        for future in futures_list:
            try:
                result = future.result(timeout=60)
                results.append(result)
            except Exception:
                results.append(None)
                print(future.result())
    return results

if __name__ == "__main__":

    results = get_list_of_configlets()
    for future in results:
        for configlet in future['data']:
            with open(configlet['name'],'w') as f:
                f.write(configlet['config'])

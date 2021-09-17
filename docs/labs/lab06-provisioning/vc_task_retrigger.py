# Copyright (c) 2021 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.

# Example on how to re-trigger task creation if a config push task was previously
# cancelled and the device is still config out of sync
import argparse
import ssl
import sys
from pkg_resources import parse_version
from getpass import getpass
from cvprac.cvp_client import CvpClient
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()


if ((sys.version_info.major == 3) or
        (sys.version_info.major == 2 and sys.version_info.minor == 7 and
         sys.version_info.micro >= 5)):
    ssl._create_default_https_context = ssl._create_unverified_context


def main():
        
    compliance = {"0001": "Config is out of sync",
        "0003": "Config & image out of sync",
        "0004": "Config, Image and Device time are in sync",
        "0005": "Device is not reachable",
        "0008": "Config, Image and Extensions are out of sync",
        "0009": "Config and Extensions are out of sync",
        "0012": "Config, Image, Extension and Device time are out of sync",
        "0013": "Config, Image and Device time are out of sync",
        "0014": "Config, Extensions and Device time are out of sync",
        "0016": "Config and Device time are out of sync"
    }
    # Create connection to CloudVision
    clnt = CvpClient()

    parser = argparse.ArgumentParser(
        description='Script to recreate a task, if a previous config push was cancelled')
    parser.add_argument('-u', '--username', default='username')
    parser.add_argument('-p', '--password', default=None)
    parser.add_argument('-c', '--cvpserver', action='append')
    parser.add_argument('-f', '--filter', action='append', default=None)
    args = parser.parse_args()

    if args.password is None:
        args.password = getpass()

    for cvpserver in args.cvpserver:
        print("Connecting to %s" % cvpserver)
        try:
            clnt.connect(nodes=[cvpserver], username=args.username, password=args.password)
        except Exception as e:
            print("Unable to connect to CVP: %s" % str(e))

        # Get the current CVP version
        cvp_release = clnt.api.get_cvp_info()['version']
        if parse_version(cvp_release) < parse_version('2020.3.0'):
            # For older CVP, we manually trigger a compliance check
            try:
                clnt.api.check_compliance('root', 'container')
            except:
                # Bad practice, but the check compliance applied to a container can't actually work
                # since the complianceIndication  key doesn't exist on the container level
                pass
        else:
            # with continuous compliance checks, triggering the check is no longer required
            pass

        device_filters = []
        if args.filter is not None:
            for entry in args.filter:
                device_filters.extend(entry.split(','))

        # Get inventory
        print("Collecting inventory...")
        devices = clnt.api.get_inventory()
        print("%d devices in inventory" % len(devices) )

        for switch in devices:
            if (switch['status'] == 'Registered' and
                    switch['parentContainerId'] != 'undefined_container'):

                if len(device_filters) > 0:
                    # iterate over device filters, and update task for
                    # any devices not in compliance
                    
                    for filter_term in device_filters:
                        print("Checking device: %s" % switch['hostname'])
                        if filter_term in switch['hostname']:
                            # generate configlet list
                            cl = clnt.api.get_configlets_by_device_id(switch['systemMacAddress'])
                            # generate a task if config is out of sync
                            if switch['complianceCode'] in compliance.keys():
                                print(clnt.api.apply_configlets_to_device("", switch, cl))
                            else:
                                print("%s is compliant, nothing to do" % switch['hostname'])
                        else:
                            print("Skipping %s due to filter" % switch['hostname'])
                else:
                    print("Checking device: %s" % switch['hostname'])
                    cl = clnt.api.get_configlets_by_device_id(switch['systemMacAddress'])
                    # generate a task if config is out of sync
                    if switch['complianceCode'] in compliance.keys():
                        print(clnt.api.apply_configlets_to_device("", switch, cl))

            else:
                print("Skipping %s, device is unregistered for provisioning" % switch['hostname'])

    return 0


if __name__ == "__main__":
    main()

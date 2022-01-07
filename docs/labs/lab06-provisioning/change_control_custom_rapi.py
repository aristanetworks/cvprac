# Copyright (c) 2021 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.
#
# NOTE: The following example is using the new Change Control Resource APIs supported in 2021.2.0 or newer and in CVaaS.
# For CVaaS service-account token based auth has to be used.

from cvprac.cvp_client import CvpClient
import ssl
import uuid
from datetime import datetime
ssl._create_default_https_context = ssl._create_unverified_context
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()

# Create connection to CloudVision
clnt = CvpClient()
clnt.connect(['cvp1'],'username', 'password')


cc_id = str(uuid.uuid4())
name = f"Change_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# Create custom stage hierarchy
# The below example would result in the following hierarchy:
# root (series)
# |- stages 1-2 (series)
# |  |- stage 1ab (parallel)
# |  |    |- stage 1a
# |  |    |- stage 1b
# |  |- stage 2
# |- stage 3
data = {'key': {
            'id': cc_id
            },
        'change': {
            'name': cc_id,
            'notes': 'cvprac CC',
            'rootStageId': 'root',
            'stages': {'values': {'root': {'name': 'root',
                                           'rows': {'values': [{'values': ['1-2']},
                                                               {'values': ['3']}]
                                            }
                                        },
                                  '1-2': {'name': 'stages 1-2',
                                          'rows': {'values': [{'values': ['1ab']},
                                                              {'values': ['2']}]}},
                                  '1ab': {'name': 'stage 1ab',
                                          'rows': {'values': [{'values': ['1a','1b']}]
                                            }
                                        },
                                  '1a': {'action': {'args': {'values': {'TaskID': '1242'}},
                                                    'name': 'task',
                                                    'timeout': 3000},
                                         'name': 'stage 1a'},
                                  '1b': {'action': {'args': {'values': {'TaskID': '1243'}},
                                                    'name': 'task',
                                                    'timeout': 3000},
                                         'name': 'stage 1b'},
                                  '2': {'action': {'args': {'values': {'TaskID': '1240'}},
                                                   'name': 'task',
                                                   'timeout': 3000},
                                        'name': 'stage 2'},
                                  '3': {'action': {'args': {'values': {'TaskID': '1241'}},
                                                   'name': 'task',
                                                   'timeout': 3000},
                                        'name': 'stage 3'},
                }
            }
        }
 }
# Create change control from custom stage hierarchy data
clnt.api.change_control_create_with_custom_stages(data)

# Approve the change control
approval_note = "Approve CC via cvprac" # notes are optional
clnt.api.change_control_approve(cc_id, notes=approval_note)

# Start the change control
start_note = "Starting CC via cvprac" # notes are optional
clnt.api.change_control_start(cc_id, notes=start_note)

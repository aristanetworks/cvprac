#
# Copyright (c) 2017, Arista Networks, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#   Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
#
#   Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
#
#   Neither the name of Arista Networks nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# 'AS IS' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL ARISTA NETWORKS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
# IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

''' CVP Restful API Client System Tests

The DUT is a CVP node.
'''
import os
import unittest
import yaml

def get_fixtures_path():
    ''' Return the path to the fixtures directory.
    '''
    return os.path.join(os.path.dirname(__file__), '../fixtures')

def get_fixture(filename):
    ''' Return a path with the fixtures directory prepended to the filename.
    '''
    return os.path.join(get_fixtures_path(), filename)

class DutSystemTest(unittest.TestCase):
    ''' DutSystemTest class that provides information about the DUTs used.
    '''
    def __init__(self, *args, **kwargs):
        super(DutSystemTest, self).__init__(*args, **kwargs)

    def setUp(self):
        ''' Read in the list of CVP node names or IP addresses to use
            for testing.

            Format for duts list of dicts:
            { node: nodename, user: username, password: password }
        '''
        self.duts = {}
        filename = get_fixture('cvp_nodes.yaml')
        with open(filename, 'r') as stream:
            self.duts = yaml.load(stream)
            stream.close()

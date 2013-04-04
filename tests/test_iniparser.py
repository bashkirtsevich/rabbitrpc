# coding=utf-8
#
# $Id: $
#
# NAME:         test_iniparser.py
#
# AUTHOR:       Nick Whalen <nickw@mindstorm-networks.net>
# COPYRIGHT:    2013 by Nick Whalen
# LICENSE:
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# DESCRIPTION:
#   Tests IniParser
#


import os
import pytest
import mock
from rabbitrpc.iniparser import IniParser


class Test_as_dict(object):
    """
    Tests IniParser's as_dict method.

    """
    def setup_method(self, method):
        """
        Test Setup

        :param method:

        """
        self.target_dict = {
            'RabbitRPC': {
                'rpc_definition_paths': '/home/nickw/rabbitrpc/scratch/defs:/tmp'
            },
            'RabbitMQ': {
                'username': 'None',
                'exchange': '',
                'queue_name': 'rabbitrpc',
                'host': 'localhost',
                'virtual_host': '/',
                'password': 'None',
                'port': '5672'}
        }
        self.parser = IniParser()

        # Load ini fixture
        ini = '%s/fixtures/config.ini' % os.path.abspath(os.path.join(__file__, os.pardir))
        self.parser.read(ini)
        self.config_dict = self.parser.as_dict()

    #---

    def test_ParsesIniToDict(self):
        """
        Tests that the parser correctly converts to a dict

        """
        assert self.config_dict == self.target_dict
    #---
#---
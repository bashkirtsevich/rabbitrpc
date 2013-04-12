# coding=utf-8
#
# $Id: $
#
# NAME:         rpcclient.py
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
#   RabbitMQ-based RPC client
#

import cPickle
import imp
import logging
from rabbitrpc.rabbitmq import producer
import sys


class RPCClientError(Exception): pass
class ConnectionError(RPCClientError): pass
class ReplyTimeoutError(RPCClientError): pass


class RPCClient(object):
    """
    Implements the client side of RPC over RabbitMQ.

    """
    rabbit_producer = None
    definitions = None
    definitions_hash = None

    def __init__(self, rabbit_config):
        """
        Constructor

        """
        self.log = logging.getLogger ('rpcclient')
        self.rabbit_producer = producer.Producer(rabbit_config)
    #---

    def __del__(self):
        """
        Cleans up connections

        """
        self.rabbit_producer.stop()
    #---


    def start(self):
        """
        Starts the RPC client

        """
        self.rabbit_producer.start()
        self._fetch_definitions()
    #---

    def _fetch_definitions(self):
        """
        Fetches the call definitions from the server.

        """
        call = cPickle.dumps({
            'call_name': 'provide_definitions',
            'args': None,
            'internal': True,
            'module': None,
        })

        encoded__data = self.rabbit_producer.send(call)
        def_data = cPickle.loads(encoded__data)

        self.definitions = def_data['result']['definitions']
        self.definitions_hash = def_data['result']['hash']
    #---

    def _new_module(self, module_name):
        """
        Wraps the module registration and creation methods

        """
        module = imp.new_module(module_name)
        sys.modules[module_name] = module

    #---



    def _create_module(self, module_name):
        """
        Creates a new dynamic module based on the provided info

        :return: module

        """
        module = imp.new_module(module_name)
    #---

    def _register_module(self, module_name, module):
        """
        Registers a new dynamic module with Python


        """
        sys.modules[module_name] = module
    #---
#---

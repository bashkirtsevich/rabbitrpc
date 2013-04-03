# coding=utf-8
#
# $Id: $
#
# NAME:         rpcserver.py
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
#   RabbitMQ-based RPC server.
#

import cPickle
import inspect
import logging
from rabbitmq import consumer


class RPCServerError(Exception): pass


def RPCFunction(function):
    """
    Decorator to register a function as an RPC function.

    :param function:  Incoming function to register

    :rtype: func

    """
    # Reads the function's args and arranges them into a format that's easy to use on the other side
    argspec = inspect.getargspec(function)
    num_defaults = len(argspec.defaults)
    named_args = argspec.args[:num_defaults] + zip(argspec.args[num_defaults:],argspec.defaults)

    args = {'named': named_args, 'kwargs': argspec.keywords, 'varargs': argspec.varargs}

    function_wire_def = {
        function.__name__: dict(args=args, doc=inspect.cleandoc(function.__doc__), module=function.__module__)
    }

    RPCServer.registerFunction(function_wire_def)

    return function
#---


class RPCServer(object):
    """
    Implements the server side of RPC over RabbitMQ.

    """
    rabbit_config = {
        'host': 'localhost',
        'port': 5672,
        'virtual_host': '/',
        'queue_name': 'rabbitrpc',
        'username': None,
        'password': None,
        'exchange': '',
    }
    rabbit_consumer = None
    definitions = {}
    log = None


    @classmethod
    def registerFunction(cls, rpc_function_def):
        """
        Registers an RPC function with the server class.

        :param rpc_function_def: The method to register as an available RPC call
        :type rpc_function_def: dict

        """
        cls.definitions.update(rpc_function_def)
    #---


    def __init__(self, rabbit_config):
        """
        Constructor

        :param rabbit_config: Dictionary which contains the RabbitMQ config.  Partial config can be passed, and
          values will overwrite their matching defaults. Defaults shown below:
            {
                'host': 'localhost',
                'port': 5672,
                'virtual_host': '/',
                'queue_name': 'rabbitrpc',
                'username': None,
                'password': None,
                'exchange': '',
            }
        :type rabbit_config: dict

        """
        self.log = logging.getLogger('rpcserver')

        # TODO: Fix this after the consumer constructor is refactored
        self.rabbit_consumer = consumer.Consumer(self._rabbit_callback, self.rabbit_config['queue_name'],
                                                 self.rabbit_config['exchange'], self.rabbit_config)
    #---


    def _rabbit_callback(self, body):
        """
        Takes the information from the RabbitMQ message body and determines what should be done with it, then does
        it.

        :param body: The message body from the RabbitMQ consumer
        :type body: str

        :return: Whatever the method that was proxied returns, encoded
        """

        return
    #---
#---

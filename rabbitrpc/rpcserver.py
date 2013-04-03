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
    rpc_functions = {}
    rpc_functions_hash = None
    rpc_classes = {}
    rpc_classes_hash = None


    @classmethod
    def registerFunction(cls, rpc_function_def):
        """
        Registers an RPC function with the server class.

        :param rpc_function_def: The method to register as an available RPC call
        :type rpc_function_def: dict

        """
        cls.rpc_functions.update(rpc_function_def)
    #---


    def __init__(self, rpc_callback, queue_name = 'rabbitrpc', exchange='', connection_settings = None):
        """
        Constructor

        :param rpc_callback: The method to call when the server receives and incoming RPC request.
        :type rpc_callback: function
        :param queue_name: Queue to connect to on the RabbitMQ server
        :type queue_name: str
        :param connection_settings: RabbitMQ connection configuration parameters.  These are the same parameters that
            are passed to the ConnectionParameters class in pika, minus 'credentials', which is created for you,
            provided that you provide both 'username' and 'password' values in the dict.
            See: http://pika.readthedocs.org/en/0.9.8/connecting.html#connectionparameters
        :type connection_settings: dict

        """

    #---
#---

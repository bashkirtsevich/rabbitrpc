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


_PROXY_FUNCTION="""def %(call_name)s(%(args)s):
    \"\"\"
    %(doc)s
    \"\"\"
    return proxy_class._proxy_handler('%(call_name)s','%(module_name)s'%(proxy_args)s)"""


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
        self.log = logging.getLogger (__name__)
        self.rabbit_producer = producer.Producer(rabbit_config)
    #---

    def __del__(self):
        """
        Cleans up connections

        """
        self.stop()
    #---


    def start(self):
        """
        Starts the RPC client

        """
        self.rabbit_producer.start()
        self.refresh()
    #---

    def stop(self):
        """
        Cleans up after the client, including un-registering defined modules.

        """
        if self.rabbit_producer:
            self.rabbit_producer.stop()

        self._remove_rpc_modules()
    #---

    def refresh(self):
        """
        Fetches the latest set of definitions from the server and re-builds the call mocks.  USE THIS WITH CARE!  It
        _will_ overwrite existing references.

        """
        self._fetch_definitions()
        self._build_rpc_modules()
    #---

    def _proxy_handler(self, method_name, module, *varargs, **kwargs):
        """
        This handles calls to the proxy functions and does the work to send those calls on to the RPC server.

        :param method_name: The calling method's name
        :type method_name: str
        :param module: The calling method's module name
        :type module: str
        :param varargs: varargs from the calling method
        :type varargs: tuple
        :param kwargs: kwargs from the calling method
        :type kwargs: dict

        :return: Call results
        """
        # Set up the arguments in the proper format
        if varargs or kwargs:
            args = {
                'varargs': varargs if varargs else None,
                'kwargs': kwargs if kwargs else None,
            }
        else:
            args = None

        call = {
            'call_name': method_name,
            'args': args,
            'internal': False,
            'module': module,
        }

        encoded_data = self.rabbit_producer.send(cPickle.dumps(call))
        decoded_results = cPickle.loads(encoded_data)

        results = self._result_handler(decoded_results)
        return results
    #---

    def _result_handler(self, decoded_results):
        """
        Handles the results from a call.  Raises exceptions if it needs to.

        :param decoded_results: Decoded call results
        :type decoded_results: dict

        :return: The actual decoded_results of the call

        """
        if decoded_results['error']:
            print(decoded_results['error']['traceback'])
            raise decoded_results['result']

        return decoded_results['result']
    #---

    def _fetch_definitions(self):
        """
        Fetches the call definitions from the server.

        """
        call = {
            'call_name': 'provide_definitions',
            'args': None,
            'internal': True,
            'module': None,
        }

        encoded_data = self.rabbit_producer.send(cPickle.dumps(call))
        def_data = cPickle.loads(encoded_data)

        self.definitions = def_data['result']['definitions']
        self.definitions_hash = def_data['result']['hash']
    #---

    def _build_rpc_modules(self):
        """
        Builds the set of dynamic modules defined in the RPC server definitions.

        """
        for module, definitions in self.definitions.items():
            new_module = imp.new_module(module)

            self._build_module_functions(definitions, new_module)

            # Give the module a reference to this class or things just won't work
            new_module.proxy_class = self
            # Make functions 'real'
            sys.modules[module] = new_module
    #---

    def _build_module_functions(self, definitions, module):
        """
        Builds a modules methods and attaches them to it

        :param definitions: Function definitions for the given module
        :type definitions: dict
        :param module: The module object to operate on
        :type module: module

        """
        for call_name, definition in definitions.items():
            args = ''
            proxy_args = ''

            if definition['args'] is not None:
                args, proxy_args = self._convert_args_to_strings(definition['args']['defined'])

            function_vars = {
                'call_name': call_name,
                'doc': definition['doc'],
                'args': args,
                'proxy_args': proxy_args,
                'module_name': module.__name__,
            }

            new_function = _PROXY_FUNCTION % function_vars
            exec new_function in module.__dict__
    #---

    def _convert_args_to_strings(self, func_args):
        """
        Converts the call definition's args to strings that can be used in the module function's definition and
        its calls to the proxy method.

        :param func_args: The arguments for a call definition
        :type func_args: dict

        :return: tuple Text arguments for the module function definition[0] and the proxy method call[1].

        """
        kwargs = ''
        varargs = ''
        proxy_kwargs = ''
        proxy_args = ''
        args = ''

        def convert_kwargs(key):
            if type(func_args['kw'][key]) is str:
                translated_str = '%s = "%s"' % (key, func_args['kw'][key])
            else:
                translated_str = '%s = %s' % (key, func_args['kw'][key])

            return translated_str
        #---

        if func_args['var'] is not None:
            varargs = ', '.join(func_args['var'])

        if func_args['kw'] is not None:
            kwargs = ', '.join(map(convert_kwargs, func_args['kw']))
            proxy_kwargs = ', '.join(map(lambda key: '%s = %s' % (key, key), func_args['kw'].keys()))

        # Build the 'def' arg list
        if varargs:
            args += ', %s' % varargs
        if kwargs:
            args += ', %s' % kwargs

        # Build the 'proxy' call arg list
        if varargs:
            proxy_args += ', %s' % varargs
        if proxy_kwargs:
            proxy_args += ', %s' % proxy_kwargs

        return args.lstrip(', '), proxy_args
    #---

    def _remove_rpc_modules(self):
        """
        Cleanup method.  Removes all the modules the rpc client registered.

        """
        if not self.definitions:
            return

        for module in self.definitions.keys():
            if module in sys.modules:
                del sys.modules[module]
    #---
#---

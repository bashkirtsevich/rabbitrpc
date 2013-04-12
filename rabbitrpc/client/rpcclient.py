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
    proxy_class._proxy_handler(%(call_name)s%(proxy_args)s)"""


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

    def _proxy_handler(self, method_name, *varargs, **kwargs):
        """
        This handles calls to the proxy functions and does the work to send those calls on to the RPC server.

        :return:
        """
        print('Ello, proxy handler method here')
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

    def _build_rpc_modules(self):
        """
        Builds the set of dynamic modules defined in the RPC server definitions.

        """
        for module, definitions in self.definitions.items():
            new_module = self._new_module(module)

            # Build the module functions
            for call_name, definition in definitions.items():
                args = ''
                proxy_args = ''

                if definition['args'] is not None:
                    varargs, kwargs, kwargs_no_defaults = self._convert_args_to_strings(definition['args']['defined'])
                    if varargs:
                        args += ', %s' % varargs
                    if kwargs:
                        args += ', %s' %kwargs

                    if varargs:
                        proxy_args += ', %s' % varargs
                    if kwargs:
                        proxy_args += ', %s' %kwargs_no_defaults

                modified_def = {
                    'call_name': call_name,
                    'doc': definition['doc'],
                    'args': args.lstrip(', '),
                    'proxy_args': proxy_args,
                }

                new_function = _PROXY_FUNCTION % modified_def
                exec new_function in new_module.__dict__

            # Give the module a reference to this class or things just won't work
            new_module.proxy_class = self
            # Make functions 'real'
            sys.modules[module] = new_module
    #---

    def _convert_args_to_strings(self, args):
        varargs = ''
        kwargs = ''
        kwargs_names = ''

        def convert_kwargs(key):
            if type(args['kw'][key]) is str:
                translated_str = '%s = "%s"' % (key, args['kw'][key])
            else:
                translated_str = '%s = %s' % (key, args['kw'][key])

            return translated_str
        #---

        if args['var'] is not None:
            varargs = ', '.join(args['var'])

        if args['kw'] is not None:
            kwargs = ', '.join(map(convert_kwargs, args['kw']))
            kwargs_names = args['kw'].keys()

        return varargs,kwargs,kwargs_names
    #---

    def _new_module(self, module_name):
        """
        Creates and registers a new module.

        :param module_name: Name of the module to create/register
        :type module_name: str

        :rtype: module
        """
        module = imp.new_module(module_name)
        sys.modules[module_name] = module

        return module
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

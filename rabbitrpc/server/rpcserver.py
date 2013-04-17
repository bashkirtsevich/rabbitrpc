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
import logging
from rabbitrpc.rabbitmq import consumer
import sys
import traceback


class RPCServerError(Exception): pass
class CallError(RPCServerError): pass
class CallFormatError(RPCServerError): pass
class ModuleError(RPCServerError): pass


class RPCServer(object):
    """
    Implements the server side of RPC over RabbitMQ.

    """
    internal_definitions = {
        'provide_definitions' : {
            'args': None,
            },
        'current_hash' : {
            'args': None,
            },
    }
    rabbit_consumer = None
    definitions = {}
    definitions_hash = None
    _module_map = {}
    log = None
    rabbit_config = None


    @classmethod
    def register_definition(cls, definition, module_map):
        """
        Registers an RPC call(s) with the server class.

        :param definition: The method(s) to register as an available RPC call
        :type definition: dict
        :param module_map: Short name -> Long Name mapping
        :type module_map: dict

        """
        for module,call_def in definition.items():
            if module in cls.definitions:
                cls.definitions[module].update(call_def)
            else:
                cls.definitions.update({module: call_def})

        cls.definitions_hash = hash(cPickle.dumps(cls.definitions))

        cls._module_map.update(module_map)
    #---


    def __init__(self, rabbit_config):
        """
        Constructor

        :param rabbit_config: The configuration for the RabbitMQ server.  For details see this example:
            https://github.com/nwhalen/rabbitrpc/wiki/Data-Structure-Definitions#rabbitmq-configuration
        :type rabbit_config: dict

        """
        self.log = logging.getLogger(__name__)
        self.rabbit_config = rabbit_config
    #---


    def run(self):
        """
        Runs the RabbitMQ consumer

        """
        # TODO: Fix this after the consumer constructor is refactored
        self.rabbit_consumer = consumer.Consumer(self._rabbit_callback, self.rabbit_config['queue_name'],
                                                 self.rabbit_config['exchange'],
                                                 self.rabbit_config['connection_settings'])

        self.rabbit_consumer.run()
    #---


    def stop(self):
        """
        Stops the RabbitMQ consumer

        :return:
        """
        self.rabbit_consumer.stop()
    #---


    def provide_definitions(self):
        """
        Provides the function definitions and their hash.

        :rtype: dict

        """
        data = {
            'definitions': self.definitions,
            'hash': self.definitions_hash,
        }

        return data
    #---


    def current_hash(self):
        """
        Provides the current hash.

        :rtype: int

        """
        return self.definitions_hash
    #---


    def _run_call(self, call_request):
        """
        Runs the specified call with or without args, depending on 'args' data.

        :param call_request: The call request data
        :type call_request: dict

        :return: Whatever the call returns

        """
        call_module = call_request['module']
        call_name = call_request['call_name']

        if call_request['internal'] and not call_module:
            dynamic_method =  self.__getattribute__(call_name)
        else:
            full_module = self._module_map[call_request['module']]
            dynamic_method = sys.modules[full_module].__dict__[call_name]

        self.log.info('Serving RPC request (%s.%s)' %(call_module, call_name))

        if not call_request['args']:
            return dynamic_method()

        args = {'varargs': [], 'kwargs': {}}
        # Remove keys with 'None' values from incoming args and update the defaults
        args.update({key: value for key,value in call_request['args'].items() if value})

        return dynamic_method(*args['varargs'], **args['kwargs'])
    #---

    def _validate_request_structure(self, call_request):
        """
        Validates that the call request's data-structure is sane.

        :param call_request: The call request data
        :type call_request: dict

        """
        if 'call_name' not in call_request:
            raise CallFormatError('call_name parameter is missing')

        if 'args' not in call_request:
            raise CallFormatError('args parameter is missing')
        elif call_request['args'] is not None:
            if 'varargs' not in call_request['args']:
                raise CallFormatError('sub-parameter for args - varargs - is missing')
            elif 'kwargs' not in call_request['args']:
                raise CallFormatError('sub-parameter for args - kwargs - is missing')

        if 'internal' not in call_request:
            raise CallFormatError('internal parameter is missing')

        if 'module' not in call_request:
            raise CallFormatError('module parameter is missing')
    #---


    def _validate_call(self, call_request):
        """
        Checks the call request for sanity.

        :param call_request: The call request data
        :type call_request: dict

        """
        # Internal requests are special-cased
        if 'internal' in call_request and call_request['internal'] is True:
            # Sanity check, the call must be defined already, no calling run() or __init__()
            if call_request['call_name'] not in self.internal_definitions:
                raise CallError('%s is not defined' % call_request['call_name'])

        # Normal RPC methods
        else:
            short_module = call_request['module']

            if short_module not in self._module_map:
                raise ModuleError('Something went very wrong. %s\'s map is missing. I am so lost...' % short_module)

            long_module = self._module_map[short_module]

            if (short_module not in self.definitions) or (long_module not in sys.modules):
                raise ModuleError('%s is not a valid module on this server' % short_module)

            elif call_request['call_name'] not in self.definitions[short_module]:
                raise CallError('%s is not defined on module %s' % (call_request['call_name'], short_module))

            elif not call_request['call_name'] in sys.modules[long_module].__dict__:
                raise CallError('%s is not a valid call on this server' %call_request['call_name'])
    #---


    def _encode_result(self, result, call_request, exception_info = None):
        """
        Encodes a call result into a data structure with information about the call and any errors, then pickles
        the result and returns it.

        :param result: The result data, can be any valid python object
        :param call_request: The original call request data

        :return: The encoded call result
        :rtype: str

        """
        call_result = {
            'call': call_request,
            'result': result,
            'error': None,
        }

        # Error processing
        if isinstance(result, Exception):
            call_result['error'] = {}
            trace = traceback.format_exception(*exception_info)
            call_result['error']['traceback'] = ''.join(trace)
            self.log.info('RPC request (%s.%s) raised an exception:\n%s'
                          %(call_request['module'], call_request['call_name'], call_result['error']['traceback']))

        return cPickle.dumps(call_result)
    #---


    def _rabbit_callback(self, body):
        """
        Takes the information from the RabbitMQ message body and determines what should be done with it, then does
        it.

        :param body: The message body from the RabbitMQ consumer
        :type body: str

        :return: Whatever the method that was proxied returns, pickled

        """
        exception_info = None

        # De-serialize the call request
        try:
            call_request = cPickle.loads(body)
        except Exception:
            raise consumer.InvalidMessageError(body)

        try:
            self._validate_request_structure(call_request)
            self._validate_call(call_request)
            result = self._run_call(call_request)
        except Exception as result:
            exception_info = sys.exc_info()
            pass

        return self._encode_result(result, call_request, exception_info)
    #---
#---

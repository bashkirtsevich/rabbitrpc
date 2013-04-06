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
from rabbitrpc import iniparser
import logging
from rabbitrpc.rabbitmq import consumer
import sys
import traceback


class RPCServerError(Exception): pass
class CallError(RPCServerError): pass
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
    log = None


    @classmethod
    def register_definition(cls, definition):
        """
        Registers an RPC function with the server class.

        :param definition: The method to register as an available RPC call
        :type definition: dict

        """
        cls.definitions.update(definition)
        cls.definitions_hash = hash(cPickle.dumps(cls.definitions))
    #---


    def __init__(self, config_file):
        """
        Constructor

        :param config_file:
        """
        self.log = logging.getLogger('rpcserver')

        config_parser = iniparser.IniParser()
        config_parser.read(config_file)
        self.config = config_parser.as_dict()
    #---


    def run(self):
        """
        Runs the RabbitMQ consumer

        """
        # TODO: Fix this after the consumer constructor is refactored
        rabbit_config = self.config['RabbitMQ']
        queue_name = rabbit_config.pop('queue_name')
        exchange = rabbit_config.pop('exchange')
        rabbit_config['port'] = int(rabbit_config['port'])

        self.rabbit_consumer = consumer.Consumer(self._rabbit_callback, queue_name, exchange, rabbit_config)

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
            if not call_module in sys.modules:
                raise ModuleError('%s is not a valid module on this server' %call_module)
            if not call_name in sys.modules[call_module].__dict__:
                raise CallError('%s is not a valid call on this server' %call_name)
            
            dynamic_method = sys.modules[call_module].__dict__[call_name]

        if not call_request['args']:
            return dynamic_method()


        args = {'varargs': [], 'kwargs': {}}
        # Remove keys with 'None' values from incoming args and update the defaults
        args.update({key: value for key,value in call_request['args'].items() if value})

        return dynamic_method(*args['varargs'], **args['kwargs'])
    #---


    def _validate_call_request(self, call_request):
        """
        Checks the call request data for sanity.

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
            if call_request['call_name'] not in self.definitions:
                raise CallError('%s is not defined' % call_request['call_name'])
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

        # De-serialize the data
        try:
            call_request = cPickle.loads(body)
        except Exception:
            raise consumer.InvalidMessageError(body)

        try:
            self._validate_call_request(call_request)
            result = self._run_call(call_request)
        except Exception as result:
            exception_info = sys.exc_info()
            pass

        return self._encode_result(result, call_request, exception_info)
    #---
#---

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


class RPCServerError(Exception): pass
class CallError(RPCServerError): pass


class RPCServer(object):
    """
    Implements the server side of RPC over RabbitMQ.

    """
    rabbit_consumer = None
    definitions = {}
    picked_defs = None
    pickled_defs_hash = None
    internal_definitions = {
        'provide_definitions' : {
                'args': None,
        }
    }
    log = None


    @classmethod
    def register_definition(cls, definition):
        """
        Registers an RPC function with the server class.

        :param definition: The method to register as an available RPC call
        :type definition: dict

        """
        cls.definitions.update(definition)
        cls.picked_defs = cPickle.dumps(cls.definitions)
        cls.pickled_defs_hash = hash(cls.picked_defs)
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
        self.rabbit_consumer = consumer.Consumer(self._rabbit_callback, rabbit_config['queue_name'],
                                                 rabbit_config['exchange'], rabbit_config)
    #---


    def _run_call(self, call_request):
        """
        Runs the specified call with or without args, depending on 'args' data.

        :param method: The method to call
        :param method_args: The arguments to pass to the method
        :type method_args: dict

        :return:

        """
        if call_request['internal']:
            dynamic_method =  self.__getattribute__(call_request['call_name'])
        # FIXME
        else:
            dynamic_method = lambda : None

        if not call_request['args']:
            return dynamic_method()

        args = {'varargs': [], 'kwargs': {}}
        args.update(call_request['args'])

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


    def _rabbit_callback(self, body):
        """
        Takes the information from the RabbitMQ message body and determines what should be done with it, then does
        it.

        :param body: The message body from the RabbitMQ consumer
        :type body: str

        :return: Whatever the method that was proxied returns, pickled

        """
        # De-serialize the data
        call_request = cPickle.loads(body)
        
        self._validate_call_request(call_request)
        result = self._run_call(call_request)

        return cPickle.dumps(result)
    #---


    def provide_definitions(self):
        """
        Provides the function definitions and their hash.

        :rtype: dict

        """
        data = {
            'definitions': self.picked_defs,
            'hash': self.pickled_defs_hash,
        }

        return data
    #---
#---

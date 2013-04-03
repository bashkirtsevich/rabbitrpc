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
import pika
from pika.exceptions import AMQPConnectionError


class RPCServerError(Exception): pass
class ConnectionError(RPCServerError): pass
class CredentialsError(RPCServerError): pass


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
        function.__name__: dict(args=args, doc=inspect.cleandoc(function.__doc__))
    }

    RPCServer.registerFunction(function_wire_def)

    return function
#---


class RPCServer(object):
    """
    Implements the server side of RPC over RabbitMQ.

    """
    channel = None
    connection = None
    connection_settings = {
        'host': 'localhost',
        'port': 5672,
        'virtual_host': '/',
    }
    exchange = ''
    log = None
    queue = None
    rabbit = None
    rpc_callback = None

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
        self.log = logging.getLogger('rabbitrpc.rpcserver')
        self.rpc_callback = rpc_callback
        self.queue = queue_name
        self.exchange = exchange

        if connection_settings:
            self.connection_settings = connection_settings

        if 'username' and 'password' in self.connection_settings:
            self._createCredentials()

        # Remove the original auth values
        if 'username' in self.connection_settings:
            del self.connection_settings['username']
        if 'password' in self.connection_settings:
            del self.connection_settings['password']

        self._configureConnection()
    #---

    def stop(self):
        """
        Disconnects from the RabbitMQ server

        """
        self.channel.stop_consuming()
        self.channel.close()
    #---

    def run(self):
        """
        Starts the consumer.

        """
        self._connect()
        self.channel.start_consuming()
    #---

    def _consumerCallback(self, ch, method, props, body):
        """
        Accepts incoming message, routes them to the RPC callback, then replies to the message with whatever the RPC
        callback returned.

        This method expects pickled data and returns pickled data!

        :param ch: Channel
        :type ch: object
        :param method: Method from the consumer callback
        :type method: object
        :param props: Properties from the consumer callback
        :type props: object
        """
        try:
            decoded_body = cPickle.loads(body)
            rpc_response = self.rpc_callback(decoded_body)
        except Exception as error:
            self.log.error('ERROR: Unexpected exception raised while processing RPC request: %s' % error)
            # This tells the server we didn't process the message and to hold it for another consumer
            self.channel.basic_reject(delivery_tag=method.delivery_tag)
            return

        # If a response was requested, send it
        if hasattr(props, 'reply_to'):
            pickled_response = cPickle.dumps(rpc_response)

            pub_props = pika.BasicProperties(delivery_mode=2, correlation_id=props.correlation_id)

            self.channel.basic_publish(exchange=self.exchange, routing_key=props.reply_to, properties=pub_props,
                                       body=pickled_response)

        # Tell Rabbit we're done processing the message
        self.channel.basic_ack(delivery_tag=method.delivery_tag)
    #---

    def _connect(self):
        """
        Connects to the RabbitMQ server.

        """
        try:
            self.connection = pika.BlockingConnection(self.connection_params)
        except AMQPConnectionError as error:
            raise ConnectionError('Failed to connect to RabbitMQ server: %s' %error)

        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=self.queue, durable=True)

        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(self._consumerCallback, queue=self.queue)
    #---

    def _configureConnection(self):
        """
        Sets up the connection information.

        """
        self.connection_params = pika.ConnectionParameters(**self.connection_settings)
    #---

    def _createCredentials(self):
        """
        Creates a PlainCredentials class for use by ConnectionParameters.

        """
        creds = pika.PlainCredentials(self.connection_settings['username'], self.connection_settings['password'])
        self.connection_settings.update({'credentials': creds})
    #---
#---

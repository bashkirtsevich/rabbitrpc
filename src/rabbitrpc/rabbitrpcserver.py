# coding=utf-8
#
# $Id: $
#
# NAME:         rabbithelper.py
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
import pika
from pika.exceptions import AMQPConnectionError

from conf import rabbitmq as config


class RabbitRPCServerError(Exception): pass
class ConnectionError(RabbitRPCServerError): pass


class RabbitRPCServer(object):
    """
    Implements the server side of RPC over RabbitMQ.
    """
    queue = None
    exchange = None
    rabbit = None
    connection = None
    channel = None
    rpc_callback = None
    log = None

    def __init__(self, rpc_callback, queue_name, exchange = None):
        """
        Constructor

        :param rpc_callback: The method to call when the server receives and incoming RPC request.
        :type rpc_callback: function
        :param queue_name: Queue to connect to on the RabbitMQ server
        :type queue_name: str
        :param exchange: The Exchange to send messages to
        :type exchange: str
        """
        self.log = logging.getLogger('lib.rabbitrpcserver')
        self.rpc_callback = rpc_callback
        self.queue = queue_name
        if exchange:
            self.exchange = exchange
        else:
            self.exchange = config.DEFAULT_EXCHANGE

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
        connection_settings = {
            'host': config.HOST,
            'port': config.PORT,
            'virtual_host': config.VHOST,
            'credentials': pika.PlainCredentials(config.USERNAME, config.PASSWORD)
        }

        self.connection_params = pika.ConnectionParameters(**connection_settings)
    #---
#---

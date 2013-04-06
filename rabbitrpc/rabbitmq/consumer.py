# coding=utf-8
#
# $Id: $
#
# NAME:         consumer.py
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
#   Implements a AMQP consumer for RabbitMQ.
#


import logging
import pika
from pika.exceptions import AMQPConnectionError
import traceback


class ConsumerError(Exception): pass
class ConnectionError(ConsumerError): pass
class CredentialsError(ConsumerError): pass
class InvalidMessageError(ConsumerError): pass


class Consumer(object):
    """
    Implements a consumer for RabbitMQ (with callbacks)

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
    dead_letter_queue = None
    rabbit = None
    callback = None


    def __init__(self, callback, queue_name = 'rabbitrpc', exchange='', connection_settings = None):
        """
        Constructor

        :param callback: The method to call when the server receives and incoming RPC request.
        :type callback: function
        :param queue_name: Queue to connect to on the RabbitMQ server
        :type queue_name: str
        :param connection_settings: RabbitMQ connection configuration parameters.  These are the same parameters that
            are passed to the ConnectionParameters class in pika, minus 'credentials', which is created for you,
            provided that you provide both 'username' and 'password' values in the dict.
            See: http://pika.readthedocs.org/en/0.9.8/connecting.html#connectionparameters
        :type connection_settings: dict

        """
        self.log = logging.getLogger('rabbitmq.consumer')
        self.callback = callback
        self.queue = queue_name
        self.dead_letter_queue = '%s-dead-messages' % queue_name
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

        :param ch: Channel
        :type ch: object
        :param method: Method from the consumer callback
        :type method: object
        :param props: Properties from the consumer callback
        :type props: object
        """
        try:
            callback_response = self.callback(body)
        except InvalidMessageError as error:
            self.log.error('This consumer encountered an improperly formed message: %s' % body)
            self.channel.basic_reject(delivery_tag=method.delivery_tag, requeue=False)
            return
        except Exception as error:
            if method.redelivered:
                self.log.error('This message is causing persistent problems with the consumer, dropping it: \n%s\n\n'
                               '%s' % (body, traceback.format_exc()))
                self.channel.basic_reject(delivery_tag=method.delivery_tag, requeue=False)
            else:
                self.log.error('Unexpected exception raised while calling the consumer callback:\n\n%s\n' %
                               traceback.format_exc())
                self.log.debug('Message Data: %s\n' % body)
                self.channel.basic_reject(delivery_tag=method.delivery_tag)
            return

        # If a response was requested, send it
        if hasattr(props, 'reply_to'):
            pub_props = pika.BasicProperties(delivery_mode=2, correlation_id=props.correlation_id)

            self.channel.basic_publish(exchange=self.exchange, routing_key=props.reply_to, properties=pub_props,
                                       body=callback_response)

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
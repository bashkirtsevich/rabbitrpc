# coding=utf-8
#
# $Id: $
#
# NAME:         producer.py
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
#   Implements a RabbitMQ Producer
#

import logging
import pika
from pika.exceptions import AMQPConnectionError
import uuid

class ProducerError(Exception): pass
class ConnectionError(ProducerError): pass
class ReplyTimeoutError(ProducerError): pass

class Producer(object):
    """
    Implements the client side of RPC over RabbitMQ.

    """
    connection_params = None
    correlation_id = None
    reply_queue = None
    log = None
    config = {
        'queue_name': 'rabbitrpc',
        'reply_queue': None,
        'exchange': '',
        'reply_timeout': 5, # Floats are ok

        'connection_settings': {
            'host': 'localhost',
            'port': 5672,
            'virtual_host': '/',
            'username': 'guest',
            'password': 'guest',
        }
    }
    _rpc_reply = None
    _reply_timeout = None

    def __init__(self, rabbit_config = None):
        """
        Constructor

        :param rabbit_config: The RabbitMQ config. See
            https://github.com/nwhalen/rabbitrpc/wiki/Data-Structure-Defintions for details.
        :type rabbit_config: dict

        """
        self.log = logging.getLogger('rabbitmq.producer')
        if rabbit_config:
            self.config.update(rabbit_config)

        if 'username' and 'password' in self.config['connection_settings']:
            self._createCredentials()

        self._configureConnection()
    #---

    def start(self):
        """
        Connects to RabbitMQ and starts the producer.

        """
        self._connect()
    #---

    def stop(self):
        """
        Cleanly stops the producer.

        """
        if self.connection:
            self.connection.close()
    #---

    def send(self, body_data, expect_reply = True):
        """
        Sends an RPC call to the provided queue.

        This method pickles the data provided to it before sending it to the queue.

        :param body_data: The data to transmit
        :type body_data: str
        :param expect_reply: Uses a blocking connection and waits for replies if `True`.  Simply sends and forgets
            if `False`.
        :type expect_reply: bool

        :return: Un-pickled RPC response data, if expect_reply is `True`.
        """
        publish_params = {}

        if expect_reply:
            self._startReplyConsumer()
            self.correlation_id = str(uuid.uuid4())
            params = {'properties': pika.BasicProperties(reply_to=self.reply_queue,
                                                         correlation_id=self.correlation_id)}
            publish_params.update(params)

        self.channel.basic_publish(exchange=self.config['exchange'], routing_key=self.config['queue_name'],
                                   body=body_data, **publish_params)

        if expect_reply:
            self._replyWaitLoop()

            reply = self._rpc_reply
            self._rpc_reply = None
            return reply

        return
    #---

    def _startReplyConsumer(self):
        """
        Starts the RPC reply consumer.

        """
        self.channel.basic_consume(self._consumerCallback, queue=self.reply_queue, no_ack=True)
    #---

    def _replyWaitLoop(self):
        """
        Loops until a response is received or the wait timeout elapses.

        """
        timeout_id = self.connection.add_timeout(self.config['reply_timeout'], self._timeoutElapsed)

        while self._rpc_reply is None:
            self.connection.process_data_events()

        self.connection.remove_timeout(timeout_id)
    #---

    def _timeoutElapsed(self):
        """
        Merely a method to raise an exception if the timeout elapses.  It's here because it seems to be impossible
        to get a reference to a method inside _replyWaitLoop in the tests.

        :raises: ReplyTimeoutError
        """
        raise ReplyTimeoutError('Reply timeout of %is elapsed with no response' % self.config['reply_timeout'])
    #---

    def _consumerCallback(self, ch, method, props, body):
        """
        Accepts the response to a an RPC call.

        :param ch: Channel
        :type ch: object
        :param method: Method from the consumer callback
        :type method: object
        :param props: Properties from the consumer callback
        :type props: object

        """
        if props.correlation_id == self.correlation_id:
            self._rpc_reply = body
    #---

    def _connect(self):
        """
        Connects to the RabbitMQ server.  Also creates an exclusive reply queue to be used when a call needs to
        pass data back to the client.

        """
        queue_params = {}

        if self.config['reply_queue']:
            queue_params.update({'queue':self.config['reply_queue']})

        try:
            self.connection = pika.BlockingConnection(self.connection_params)
        except AMQPConnectionError as error:
            raise ConnectionError('Failed to connect to RabbitMQ server: %s' %error)

        self.channel = self.connection.channel()

        # Creates a unique reply queue for just this connection (thus the exclusive)
        result = self.channel.queue_declare(exclusive=True, **queue_params)
        self.reply_queue = result.method.queue
    #---

    def _configureConnection(self):
        """
        Sets up the connection information.

        """
        self.connection_params = pika.ConnectionParameters(**self.config['connection_settings'])
    #---

    def _createCredentials(self):
        """
        Creates a PlainCredentials class for use by ConnectionParameters.

        """
        creds = pika.PlainCredentials(self.config['connection_settings']['username'],
                                      self.config['connection_settings']['password'])
        self.config['connection_settings'].update({'credentials': creds})

        # Remove the original auth values
        del self.config['connection_settings']['username']
        del self.config['connection_settings']['password']
    #---
#---
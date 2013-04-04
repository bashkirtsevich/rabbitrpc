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
import logging
import pika
from pika.exceptions import AMQPConnectionError
import uuid


class RPCClientError(Exception): pass
class ConnectionError(RPCClientError): pass
class ReplyTimeoutError(RPCClientError): pass


class RPCClient(object):
    """
    Implements the client side of RPC over RabbitMQ.

    """
    queue = None
    exchange = None
    reply_queue = None
    correlation_id = None
    log = None
    connection_settings = {
        'host': 'localhost',
        'port': 5672,
        'virtual_host': '/',
    }
    _rpc_reply = None
    _reply_timeout = None

    def __init__(self, queue_name = 'rabbitrpc', reply_queue = None, exchange='', reply_timeout=5000,
                 connection_settings = None):
        """
        Constructor

        :param queue_name: The name of the RabbitMQ queue to connect to.
        :type queue_name: str
        :param reply_queue: The queue that RPC server should send replies to.  Defaults to queue_name if `None`.
        :type reply_queue: str
        :param exchange: The exchange to use for this client.
        :type exchange: str
        :param reply_timeout: Time, in millis, to wait for a reply to the RPC query.
        :type reply_timeout: int
        :param connection_settings: RabbitMQ connection configuration parameters.  These are the same parameters that
            are passed to the ConnectionParameters class in pika, minus 'credentials', which is created for you,
            provided that you provide both 'username' and 'password' values in the dict.
            See: http://pika.readthedocs.org/en/0.9.8/connecting.html#connectionparameters
        :type connection_settings: dict


        """
        self.log = logging.getLogger('rabbitrpclient')
        self.queue = queue_name
        self._reply_timeout = reply_timeout / 1000
        self.exchange = exchange
        self.reply_queue = reply_queue

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
        self._connect()
    #---

    def send(self, rpc_data, expect_reply = True):
        """
        Sends an RPC call to the provided queue.

        This method pickles the data provided to it before sending it to the queue.

        :param expect_reply: Uses a blocking connection and waits for replies if `True`.  Simply sends and forgets if `False`.
        :type expect_reply: bool

        :return: Un-pickled RPC response data, if expect_reply is `True`.
        """
        publish_params = {}
        pickled_rpc = cPickle.dumps(rpc_data)

        if expect_reply:
            self._startReplyConsumer()
            self.correlation_id = str(uuid.uuid4())
            params = {'properties': pika.BasicProperties(reply_to=self.reply_queue, correlation_id=self.correlation_id)}
            publish_params.update(params)

        self.channel.basic_publish(exchange=self.exchange, routing_key=self.queue, body=str(pickled_rpc),
                                   **publish_params)

        if expect_reply:
            self._replyWaitLoop()
            return self._rpc_reply

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
        self.connection.add_timeout(self._reply_timeout, self._timeoutElapsed)

        while self._rpc_reply is None:
            self.connection.process_data_events()
    #---

    def _timeoutElapsed(self):
        """
        Merely a method to raise an exception if the timeout elapses.  It's here because it seems to be impossible
        to get a reference to a method inside _replyWaitLoop in the tests.

        :raises: ReplyTimeoutError
        """
        raise ReplyTimeoutError('Reply timeout of %i s elapsed with no response' % self._reply_timeout)
    #---

    def _consumerCallback(self, ch, method, props, body):
        """
        Accepts the response to a an RPC call.

        This method expects pickled data!

        :param ch: Channel
        :type ch: object
        :param method: Method from the consumer callback
        :type method: object
        :param props: Properties from the consumer callback
        :type props: object

        """
        if props.correlation_id == self.correlation_id:
            self._rpc_reply = cPickle.loads(body)
    #---

    def _connect(self):
        """
        Connects to the RabbitMQ server.

        """
        queue_params = {}

        if self.reply_queue:
            queue_params.update({'queue':self.reply_queue})

        try:
            self.connection = pika.BlockingConnection(self.connection_params)
        except AMQPConnectionError as error:
            raise ConnectionError('Failed to connect to RabbitMQ server: %s' %error)

        self.channel = self.connection.channel()

        result = self.channel.queue_declare(exclusive=True, **queue_params)
        self.reply_queue = result.method.queue
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

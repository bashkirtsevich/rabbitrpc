# coding=utf-8
#
# $Id: $
#
# NAME:         test_rpcserver.py
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
#   Unit tests for rpcserver module
#

import cPickle
import copy
import pytest
import mock

from rabbitrpc.server import rpcserver


class Test_register_definition(object):
    """
    Tests RPCServer's `register_definition` method.

    """

    def setup_method(self, method):
        """
        Test setup

        """
        self.definition = {
            'provide_definitions' : {
            'args': None,
            },
        }
        self.hash = hash(cPickle.dumps(self.definition))

        self.local_rpcserver = reload(rpcserver)

    #---

    def test_AddsDefinitionToClassVariable(self):
        """
        Tests that register_definition adds the function definition to the appropriate class variable

        """
        self.local_rpcserver.RPCServer.register_definition(self.definition)

        assert self.local_rpcserver.RPCServer.definitions == self.definition
    #---

    def test_ReHashesDefinitions(self):
        """
        Tests that register_definition re-hashes the function definitions after adding a new definition

        """
        self.local_rpcserver.RPCServer.register_definition(self.definition)

        assert self.local_rpcserver.RPCServer.definitions_hash == self.hash
    #---
#---

class Test___init__(object):
    """
    Tests RPCServer's `__init__` method.

    """

    def setup_method(self, method):
        """
        Test setup

        """
        self.local_rpcserver = reload(rpcserver)
        self.config_file = 'bob.txt'

        self.config_parser = mock.MagicMock()
        self.local_rpcserver.iniparser.IniParser = mock.MagicMock(return_value=self.config_parser)
        self.local_rpcserver.logging.getLogger = mock.MagicMock()

        self.server = self.local_rpcserver.RPCServer(self.config_file)
    #---

    def test_StartsALogger(self):
        """
        Tests that __init__ starts a logger.

        """
        self.local_rpcserver.logging.getLogger.assert_called_once_with('rpcserver')
    #---

    def test_ReadsConfigFile(self):
        """
        Tests that __init__ reads the config file.

        """
        self.config_parser.read.assert_called_once_with(self.config_file)
    #---

    def test_ParsesConfigToDict(self):
        """
        Tests that __init__ parses the config file to a dict.

        """
        self.config_parser.as_dict.assert_called_once_with()
    #---
#---

class Test_run(object):
    """
    Tests RPCServer's `run` method.

    """

    def setup_method(self, method):
        """
        Test setup

        """
        self.config = {
            'RabbitMQ': {
                'queue_name': 'nothing',
                'exchange': 'Nope',
                'port': 191,
            }
        }
        self.neutered_config = {
            'port': 191,
        }
        self.local_rpcserver = reload(rpcserver)

        self.local_rpcserver.iniparser.IniParser = mock.MagicMock()
        self.local_rpcserver.logging.getLogger = mock.MagicMock()
        self.rabbit_consumer = mock.MagicMock()
        self.local_rpcserver.consumer.Consumer = mock.MagicMock(return_value=self.rabbit_consumer)

        self.server = self.local_rpcserver.RPCServer('')
        self.server.config = copy.deepcopy(self.config)
        self.server.run()
    #---

    def test_CreatesAConsumer(self):
        """
        Tests that run creates a consumer, also tests that the config gets neutered before being passed.

        """
        self.local_rpcserver.consumer.Consumer.assert_called_with(self.server._rabbit_callback,
                self.config['RabbitMQ']['queue_name'], self.config['RabbitMQ']['exchange'], self.neutered_config )
    #---

    def test_RunsTheConsumer(self):
        """
        Tests that run starts the consumer

        """
        self.rabbit_consumer.run.assert_called_once_with()
    #---
#---

class Test_stop(object):
    """
    Tests RPCServer's `stop` method.

    """

    def setup_method(self, method):
        """
        Test setup

        """
        self.local_rpcserver = reload(rpcserver)


        self.local_rpcserver.iniparser.IniParser = mock.MagicMock()
        self.local_rpcserver.logging.getLogger = mock.MagicMock()
        self.rabbit_consumer = mock.MagicMock()
        self.local_rpcserver.consumer.Consumer = mock.MagicMock(return_value=self.rabbit_consumer)

        self.server = self.local_rpcserver.RPCServer('')
        self.server.run()
        self.server.stop()
    #---

    def test_StopsTheConsumer(self):
        """
        Tests that stop calls 'stop' on the consumer.

        """
        self.rabbit_consumer.stop.assert_called_once_with()
    #---
#---

class Test_provide_definitions(object):
    """
    Tests RPCServer's `provide_definitions` method.

    """

    def setup_method(self, method):
        """
        Test setup

        """
        self.local_rpcserver = reload(rpcserver)
        self.definition = {
            'provide_definitions' : {
            'args': None,
            },
        }
        self.hash = hash(cPickle.dumps(self.definition))

        self.local_rpcserver.iniparser.IniParser = mock.MagicMock()
        self.local_rpcserver.logging.getLogger = mock.MagicMock()

        self.server = self.local_rpcserver.RPCServer('')
        self.server.definitions = self.definition
        self.server.definitions_hash = self.hash
    #---

    def test_SendsTheDefinitionsAndHash(self):
        """
        Tests that provide_definitions sends a dict containing the definitions and hash.

        """
        definitions = self.server.provide_definitions()
        expected = {'definitions': self.definition, 'hash': self.hash}

        assert definitions == expected
    #---
#---

class Test_current_hash(object):
    """
    Tests RPCServer's `current_hash` method.

    """

    def setup_method(self, method):
        """
        Test setup

        """
        self.local_rpcserver = reload(rpcserver)
        self.definition = {
            'provide_definitions' : {
            'args': None,
            },
        }
        self.hash = hash(cPickle.dumps(self.definition))

        self.local_rpcserver.iniparser.IniParser = mock.MagicMock()
        self.local_rpcserver.logging.getLogger = mock.MagicMock()

        self.server = self.local_rpcserver.RPCServer('')
        self.server.definitions_hash = self.hash
    #---

    def test_HashIsSent(self):
        """
        Tests that current_hash provides the hash

        """
        provided_hash = self.server.current_hash()

        assert provided_hash == self.hash
    #---
#---

class Test__run_call(object):
    """
    Tests RPCServer's `_run_call` method.

    """

    def setup_method(self, method):
        """
        Test setup

        """
    #---

    def test_(self):
        """
        Tests that

        """
    #---
#---

class Test__validate_call_request(object):
    """
    Tests RPCServer's `_validate_call_request` method.

    """

    def setup_method(self, method):
        """
        Test setup

        """
    #---

    def test_(self):
        """
        Tests that

        """
    #---
#---

class Test__encode_result(object):
    """
    Tests RPCServer's `_encode_result` method.

    """

    def setup_method(self, method):
        """
        Test setup

        """
    #---

    def test_(self):
        """
        Tests that

        """
    #---
#---

class Test__rabbit_callback(object):
    """
    Tests RPCServer's `_rabbit_callback` method.

    """

    def setup_method(self, method):
        """
        Test setup

        """
    #---

    def test_(self):
        """
        Tests that

        """
    #---
#---
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
import sys
import traceback

from rabbitrpc.server import rpcserver


MQ_CONFIG = {
    'queue_name': 'rabbitrpc',
    'exchange': '',

    'connection_settings': {
        'host': 'localhost',
        'port': 5672,
        'virtual_host': '/',
        'username': 'guest',
        'password': 'guest',
    }
}

class Test_register_definition(object):
    """
    Tests RPCServer's `register_definition` method.

    """

    def setup_method(self, method):
        """
        Test setup

        """
        self.definition = {
            'some_module': {
                'provide_definitions' : {
                    'args': None,
                },
            }
        }
        self.module_map = dict(some_module='some_module')
        self.hash = hash(cPickle.dumps(self.definition))

        self.local_rpcserver = reload(rpcserver)
        self.local_rpcserver.RPCServer.definitions = self.definition
    #---

    def test_AddsFullDefinitionToBlankClassVariable(self):
        """
        Tests that register_definition adds the function definition to the appropriate class variable

        """
        self.local_rpcserver.RPCServer.register_definition(self.definition, self.module_map)

        assert self.local_rpcserver.RPCServer.definitions == self.definition
    #---

    def test_DoesNotOverwriteModules(self):
        """
        Tests that register_definition will not overwrite a module in the definitions.  It will instead simply add the
        call definition to that module.

        """
        new_def = {
            'some_module': {
                'pants' : {
                    'args': None,
                },
            }
        }
        expected = copy.deepcopy(self.definition)
        expected['some_module'].update(new_def['some_module'])

        self.local_rpcserver.RPCServer.register_definition(new_def, self.module_map)

        assert self.local_rpcserver.RPCServer.definitions == expected
    #---

    def test_AddsNewModuleIfDNE(self):
        """
        Tests that register_definition will add a new module entry if one does not exist already.

        """
        new_def = {
            'new_module': {
                'some_pants' : {
                    'args': None,
                },
            }
        }
        expected = copy.deepcopy(new_def)
        expected.update(self.definition)

        self.local_rpcserver.RPCServer.register_definition(new_def, self.module_map)

        assert self.local_rpcserver.RPCServer.definitions == expected
    #---

    def test_ReHashesDefinitions(self):
        """
        Tests that register_definition re-hashes the function definitions after adding a new definition

        """
        self.local_rpcserver.RPCServer.register_definition(self.definition, self.module_map)

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

        self.local_rpcserver.logging.getLogger = mock.MagicMock()

        self.server = self.local_rpcserver.RPCServer(MQ_CONFIG)
    #---

    def test_StartsALogger(self):
        """
        Tests that __init__ starts a logger.

        """
        assert self.local_rpcserver.logging.getLogger.called == True
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
        self.local_rpcserver = reload(rpcserver)

        self.local_rpcserver.logging.getLogger = mock.MagicMock()
        self.rabbit_consumer = mock.MagicMock()
        self.local_rpcserver.consumer.Consumer = mock.MagicMock(return_value=self.rabbit_consumer)

        self.server = self.local_rpcserver.RPCServer(MQ_CONFIG)
        self.server.run()
    #---

    def test_CreatesAConsumer(self):
        """
        Tests that run creates a consumer, also tests that the config gets neutered before being passed.

        """
        self.local_rpcserver.consumer.Consumer.assert_called_with(self.server._rabbit_callback,
                MQ_CONFIG['queue_name'], MQ_CONFIG['exchange'], MQ_CONFIG['connection_settings'] )
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
        mq_config = {
            'queue_name': 'rabbitrpc',
            'exchange': '',

            'connection_settings': {
                'host': 'localhost',
                'port': 5672,
                'virtual_host': '/',
                'username': 'guest',
                'password': 'guest',
            }
        }
        self.local_rpcserver = reload(rpcserver)

        self.local_rpcserver.logging.getLogger = mock.MagicMock()
        self.rabbit_consumer = mock.MagicMock()
        self.local_rpcserver.consumer.Consumer = mock.MagicMock(return_value=self.rabbit_consumer)

        self.server = self.local_rpcserver.RPCServer(mq_config)
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

        self.local_rpcserver.logging.getLogger = mock.MagicMock()

        self.server = self.local_rpcserver.RPCServer(MQ_CONFIG)
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

        self.local_rpcserver.logging.getLogger = mock.MagicMock()

        self.server = self.local_rpcserver.RPCServer(MQ_CONFIG)
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

class Test__validate_request_structure(object):
    """
    Tests RPCServer's `_validate_request_structure` method.

    """

    def setup_method(self, method):
        """
        Test setup

        """
        self.local_rpcserver = reload(rpcserver)

        self.local_rpcserver.logging.getLogger = mock.MagicMock()

        self.server = self.local_rpcserver.RPCServer(MQ_CONFIG)
    #---

    def test_RaisesErrorIfCallNameNotDefined(self):
        """
        Tests that _validate_request_structure will raise an error if the call_name parameter is not defined.

        """
        call = {
            'internal': True,
            'module': None,
            'args': None,
        }

        with pytest.raises(self.local_rpcserver.CallFormatError):
            self.server._validate_request_structure(call)
    #---

    def test_RaisesErrorIfArgsNotDefined(self):
        """
        Tests that _validate_request_structure will raise an error if the args parameter is not defined.

        """
        call = {
            'internal': True,
            'call_name': 'Bob',
            'module': None,
        }

        with pytest.raises(self.local_rpcserver.CallFormatError):
            self.server._validate_request_structure(call)
    #---

    def test_RaisesErrorIfVarArgsNotDefined(self):
        """
        Tests that _validate_request_structure will raise an error if the varargs sub-parameter is not defined and args is.

        """
        call = {
            'internal': True,
            'call_name': 'Bob',
            'module': None,
            'args': {
                'kwargs': None,
            },
        }

        with pytest.raises(self.local_rpcserver.CallFormatError):
            self.server._validate_request_structure(call)
    #---

    def test_RaisesErrorIfKwArgsNotDefined(self):
        """
        Tests that _validate_request_structure will raise an error if the kwargs sub-parameter is not defined and args is.

        """
        call = {
            'internal': True,
            'call_name': 'Bob',
            'module': None,
            'args': {
                'varargs': None,
            }
        }

        with pytest.raises(self.local_rpcserver.CallFormatError):
            self.server._validate_request_structure(call)
    #---

    def test_RaisesErrorIfInternalNotDefined(self):
        """
        Tests that _validate_request_structure will raise an error if the internal parameter is not defined.

        """
        call = {
            'call_name': 'Bob',
            'module': None,
            'args': None,
        }

        with pytest.raises(self.local_rpcserver.CallFormatError):
            self.server._validate_request_structure(call)
    #---

    def test_RaisesErrorIfModuleNotDefined(self):
        """
        Tests that _validate_request_structure will raise an error if the module parameter is not defined.

        """
        call = {
            'internal': True,
            'call_name': 'Bob',
            'args': None,
        }

        with pytest.raises(self.local_rpcserver.CallFormatError):
            self.server._validate_request_structure(call)
    #---

    def test_DoesNotRaiseErrorIfArgsIsNone(self):
        """
        Tests that _validate_request_structure will not raise an error if Args is set to None.

        """
        call = {
            'internal': True,
            'call_name': 'Bob',
            'args': None,
            'module': None,
        }

        self.server._validate_request_structure(call)
    #---

    def test_DoesNotRaiseErrorIfVarArgsIsNoneButKwArgsExists(self):
        """
        Tests that _validate_request_structure will not raise an error if varargs is set to None, if kwargs also exists.

        """
        call = {
            'internal': True,
            'call_name': 'Bob',
            'args': {
                'varargs': None,
                'kwargs': {'bob': True},
            },
            'module': None,
        }

        self.server._validate_request_structure(call)
    #---

    def test_DoesNotRaiseErrorIfKwArgsIsNoneButVarArgsExists(self):
        """
        Tests that _validate_request_structure will not raise an error if kwargs is set to None, if varargs also exists.

        """
        call = {
            'internal': True,
            'call_name': 'Bob',
            'args': {
                'varargs': [True, False],
                'kwargs': None,
            },
            'module': None,
        }

        self.server._validate_request_structure(call)
    #---

    def test_DoesNotRaiseErrorIfKwArgsAndVarArgsAreSetToNone(self):
        """
        Tests that _validate_request_structure will not raise an error if kwargs is set to None, if varargs also exists.

        """
        call = {
            'internal': True,
            'call_name': 'Bob',
            'args': {
                'varargs': None,
                'kwargs': None,
            },
            'module': None,
        }

        self.server._validate_request_structure(call)
    #---

class Test__validate_call(object):
    """
    Tests RPCServer's `_validate_call` method.

    """

    def setup_method(self, method):
        """
        Test setup

        """
        self.local_rpcserver = reload(rpcserver)

        self.local_rpcserver.logging.getLogger = mock.MagicMock()

        self.local_rpcserver.RPCServer.definitions = {
            'sys': {
                'Bob': {
                    'args': None
                }
            }
        }

        self.server = self.local_rpcserver.RPCServer(MQ_CONFIG)
        self.server._module_map['sys'] = 'sys'
    #---

    def test_RaisesErrorIfInternalCallNotDefined(self):
        """
        Tests that _validate_call will raise an error if the requested internal call is not defined

        """
        call = {
            'internal': True,
            'call_name': 'Bob',
            'module': None,
            'args': None,
        }

        with pytest.raises(self.local_rpcserver.CallError):
            self.server._validate_call(call)
    #---

    def test_RaisesErrorIfNormalCallNotAvailable(self):
        """
        Tests that _validate_call will raise an error if the requested call is not available from the
        given module

        """
        call = {
            'internal': False,
            'call_name': 'Bob',
            'module': 'sys',
            'args': None,
        }

        with pytest.raises(self.local_rpcserver.CallError):
            self.server._validate_call(call)
    #---

    def test_RaisesErrorIfModuleIsNotAvailable(self):
        """
        Tests that _validate_call will raise an error if the requested module is not defined

        """
        self.server.definitions = {
            'Bob': {
                'args': None,
            }
        }
        call = {
            'internal': False,
            'call_name': 'Bob',
            'module': 'werkit',
            'args': None,
        }

        with pytest.raises(self.local_rpcserver.ModuleError):
            self.server._validate_call(call)
    #---

    def test_RaisesErrorIfCallIsNotDefined(self):
        """
        Tests that _validate_call will raise an error if the requested module is not defined in the server
        definitions

        """
        call = {
            'internal': False,
            'call_name': 'Bob',
            'module': 'sys'
        }

        with pytest.raises(self.local_rpcserver.CallError):
            self.server._validate_call(call)
    #---

    def test_DoesNotRaiseErrorIfInternalCallIsDefined(self):
        """
        Tests that _validate_call will not raise an error if the internal call is defined.

        """
        definition = {
            'Bob': {
            'args': None
            }
        }
        call = {
            'internal': True,
            'call_name': 'Bob',
            'module': None,
            'args': None,
        }
        self.server.internal_definitions = definition
        self.server.Bob = lambda : True
        self.server._validate_call(call)
    #---

    def test_DoesNotRaiseErrorIfNormalCallIsDefined(self):
        """
        Tests that _validate_call will not raise an error if the normal call is defined.

        """
        definition = {
            'sys': {
                'Bob': {
                    'args': None
                }
            }
        }
        call = {
            'internal': False,
            'call_name': 'Bob',
            'module': 'sys',
            'args': None,
        }
        self.server.definitions = definition
        self.local_rpcserver.sys.Bob = lambda : True
        self.server._validate_call(call)
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
        self.local_rpcserver = reload(rpcserver)

        self.local_rpcserver.logging = mock.MagicMock()

        self.server = self.local_rpcserver.RPCServer(MQ_CONFIG)
    #---

    def test_IncludesResult(self):
        """
        Tests that _encode_results includes the result of the call

        """
        result = 'foo'
        expected_result = cPickle.dumps({
            'call': '',
            'result': result,
            'error': None,
        })

        encoded_result = self.server._encode_result(result, '')

        assert encoded_result == expected_result
    #---

    def test_IncludesCallRequest(self):
        """
        Tests that _encode_results includes the original call request.

        """
        call_request = 'foo'
        expected_result = cPickle.dumps({
            'call': call_request,
            'result': '',
            'error': None,
        })

        encoded_result = self.server._encode_result('', call_request)

        assert encoded_result == expected_result
    #---

    def test_IncludesError(self):
        """
        Tests that _encode_results includes the error which stopped the call processing.

        """
        call = {
            'internal': False,
            'call_name': 'Bob',
            'module': 'sys',
            'args': None,
        }

        try:
            raise Exception('word')
        except Exception as error:
            exception_info = sys.exc_info()

        expected_result = cPickle.dumps({
            'call': call,
            'result': error,
            'error': {
                'traceback': ''.join(traceback.format_exception(*exception_info))
            },
        })

        encoded_result = self.server._encode_result(error, call, exception_info)



        assert encoded_result == expected_result
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
        self.local_rpcserver = reload(rpcserver)

        self.local_rpcserver.logging.getLogger = mock.MagicMock()

        self.server = self.local_rpcserver.RPCServer(MQ_CONFIG)
    #---

    def test_RaisesInvalidMessageErrorIfBodyCantBeDecoded(self):
        """
        Tests that _rabbit_callback will raise an error if the message body can't be decoded.

        """
        with pytest.raises(self.local_rpcserver.consumer.InvalidMessageError):
            self.server._rabbit_callback('abeacvf243312')
    #---

    def test_ValidatesTheCall(self):
        """
        Tests that _rabbit_callback validates the call.

        """
        call = cPickle.dumps({
            'internal': True,
            'call_name': 'Bob123',
            'args': None,
            'module': None,
        })

        result = cPickle.loads(self.server._rabbit_callback(call))
        assert type(result['result']) is self.local_rpcserver.CallError
    #---

    def test_RunsTheCall(self):
        """
        Tests that _rabbit_callback actually runs the requested call.

        """
        self.server.Bob = mock.MagicMock(return_value=True)
        self.server.internal_definitions = {
            'Bob': {
                'args': None
            }
        }
        call = cPickle.dumps({
            'internal': True,
            'call_name': 'Bob',
            'args': None,
            'module': None,
        })

        self.server._rabbit_callback(call)
        self.server.Bob.assert_called_once_with()
    #---

    def test_HandlesErrorsFromTheCall(self):
        """
        Tests that _rabbit_callback handles unexpected errors from the call.

        """
        error = Exception('Bad things')
        self.server.Bob = mock.MagicMock()
        self.server.Bob.side_effect = error
        self.server.internal_definitions = {
            'Bob': {
                'args': None
            }
        }
        call = cPickle.dumps({
            'internal': True,
            'call_name': 'Bob',
            'args': None,
            'module': None,
        })

        result = cPickle.loads(self.server._rabbit_callback(call))

        assert type(result['result']) == Exception
    #---

    def test_EncodesTheCallResult(self):
        """
        Tests that _rabbit_callback encodes the call results.

        """
        self.server.Bob = mock.MagicMock(return_value=True)
        self.server.internal_definitions = {
            'Bob': {
                'args': None
            }
        }
        call = {
            'internal': True,
            'call_name': 'Bob',
            'args': None,
            'module': None,
        }

        expected_results = {
            'call': call,
            'result': True,
            'error': None,
        }

        results = cPickle.loads(self.server._rabbit_callback(cPickle.dumps(call)))

        assert expected_results == results
    #---
#---
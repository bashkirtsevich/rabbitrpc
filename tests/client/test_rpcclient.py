# coding=utf-8
#
# $Id: $
#
# NAME:         test_rpcclient.py
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
#   Tests rabbitrpcclient
#

import imp
import mock
import pytest
from rabbitrpc.client import rpcclient
import sys


class Test___init__(object):
    """
    Tests RPCClient's `__init__` method

    """
    def setup_method(self, method):
        """
        Test Setup

        """
        self.config = {
            'someconfig': 'yes'
        }
        self.localclient = reload(rpcclient)

        self.localclient.logging = mock.MagicMock()
        self.localclient.producer.Producer = mock.MagicMock()

        self.client = self.localclient.RPCClient(self.config)
    #---

    def test_InitializesALogger(self):
        """
        Tests that __init__ starts a logger.

        """
        self.localclient.logging.getLogger.assert_called_once_with(self.localclient.__name__)
    #---

    def test_InitializesRabbitProducer(self):
        """
        Tests that __init__ initializes a producer

        """
        self.localclient.producer.Producer.called_once_with(self.config)
    #---

    def test_PrintTracebackDisabledByDefault(self):
        """
        Tests that __init__ does not enable printing of tracebacks by default

        """
        assert self.client.print_tracebacks is False
    #---

    def test_AllowsPrintTracebackToBeEnabled(self):
        """
        Tests that __init__ allows the caller to enable printing of tracebacks

        """
        self.client = self.localclient.RPCClient(self.config, print_tracebacks = True)
        assert self.client.print_tracebacks is True
    #---

    def test_LogTracebackEnabledByDefault(self):
        """
        Tests that __init__ enables the logging of tracebacks by default

        """
        assert self.client.log_tracebacks is True
    #---

    def test_AllowLoggingOfTracebacksToBeDisabled(self):
        """
        Tests that __init__ allows traceback logging to be disabled

        """
        self.client = self.localclient.RPCClient(self.config, log_tracebacks = False)
        assert self.client.log_tracebacks is False
    #---
#---

class Test___del__(object):
    """
    Tests RPCClient's `__del__` method

    """
    def setup_method(self, method):
        """
        Test Setup

        """
        self.localclient = reload(rpcclient)

        self.localclient.logging = mock.MagicMock()
        self.localclient.producer.Producer = mock.MagicMock()

        self.client = self.localclient.RPCClient({})
        self.client.stop = mock.MagicMock()
    #---

    def test_(self):
        """
        Tests that __del__ simply calls stop

        """
        self.client.__del__()
        self.client.stop.called_once_with()
    #---

#---

class Test_start(object):
    """
    Tests RPCClient's `start` method

    """
    def setup_method(self, method):
        """
        Test Setup

        """
        self.localclient = reload(rpcclient)

        self.localclient.logging = mock.MagicMock()
        self.producer = mock.MagicMock()
        self.localclient.producer.Producer = mock.MagicMock(self.producer)

        self.client = self.localclient.RPCClient({})
        self.client.refresh = mock.MagicMock()

        self.client.start()
    #---

    def test_StartsRabbitProducer(self):
        """
        Tests that 'start' starts the RabbitMQ producer

        """
        self.producer.start.called_once_with()
    #---

    def test_StartsTheDefinitionRefresh(self):
        """
        Tests that 'start' starts a definition refresh

        """
        self.client.refresh.called_once_with()
    #---

#---

class Test_stop(object):
    """
    Tests RPCClient's `stop` method

    """
    def setup_method(self, method):
        """
        Test Setup

        """
        self.localclient = reload(rpcclient)

        self.localclient.logging = mock.MagicMock()
        self.producer = mock.MagicMock()
        self.localclient.producer.Producer = mock.MagicMock(self.producer)

        self.client = self.localclient.RPCClient({})
        self.client._remove_rpc_modules = mock.MagicMock()

        self.client.stop()
    #---

    def test_StopsProducer(self):
        """
        Tests that `stop` stops the RabbitRPC producer

        """
        self.client.rabbit_producer.stop.assert_called_once_with()
    #---

    def test_TriggersModuleRemoval(self):
        """
        Tests that `stop` triggers the removal of the RPC modules

        """
        self.client._remove_rpc_modules.assert_called_once_with()
    #---
#---

class Test_refresh(object):
    """
    Tests RPCClient's `refresh` method

    """
    def setup_method(self, method):
        """
        Test Setup

        """
        self.localclient = reload(rpcclient)

        self.localclient.logging = mock.MagicMock()
        self.producer = mock.MagicMock()
        self.localclient.producer.Producer = mock.MagicMock(self.producer)

        self.client = self.localclient.RPCClient({})
        self.client._fetch_definitions = mock.MagicMock()
        self.client._build_rpc_modules = mock.MagicMock()

        self.client.refresh()
    #---

    def test_TriggersDefinitionFetch(self):
        """
        Tests that `refresh` triggers a definitions refresh

        """
        self.client._fetch_definitions.called_once_with()
    #---

    def test_TriggersModuleBuild(self):
        """
        Tests that `refresh` triggers a module build

        """
        self.client._build_rpc_modules.called_once_with()
    #---
#---

class Test__proxy_handler(object):
    """
    Tests RPCClient's `_proxy_handler` method

    """
    def setup_method(self, method):
        """
        Test Setup

        """
        self.method_name = 'some_method'
        self.module = 'rpcendpoints'
        self.varargs = ('arg1', 'arg2')
        self.kwargs = {
            'kwarg1': 'bob',
            'kwarg2': 'barker',
        }
        self.result = [False, True]

        self.localclient = reload(rpcclient)

        self.localclient.logging = mock.MagicMock()
        self.producer = mock.MagicMock()
        self.localclient.producer.Producer = mock.MagicMock(self.producer)
        self.localclient.cPickle = mock.MagicMock()

        self.client = self.localclient.RPCClient({})
        self.client._result_handler = mock.MagicMock(return_value=self.result)

        self.handler_result =self.client._proxy_handler(self.method_name, self.module, *self.varargs, **self.kwargs)
    #---

    def test_NoArgsSetsNone(self):
        """
        Tests that if `_proxy_handler` does not receive any args, it will pass ``None`` in the call definition.

        """
        self.client._proxy_handler(self.method_name, self.module)
        call = self.localclient.cPickle.dumps.call_args
        
        assert call is not None

        call_definition = call[0][0]
        assert call_definition['args'] is None
    #---

    def test_VarargsAreIncludedInCallIfPopulated(self):
        """
        Tests that if varargs is populated, it's included in the call.

        """
        call = self.localclient.cPickle.dumps.call_args

        assert call is not None

        call_definition = call[0][0]
        assert 'varargs' in call_definition['args']
        assert call_definition['args']['varargs'] == self.varargs
    #---

    def test_VarargsAreNotIncludedInCallIfNotPopulated(self):
        """
        Tests that if varargs is not populated, it's not included in the call.

        """
        self.client._proxy_handler(self.method_name, self.module, **self.kwargs)
        call = self.localclient.cPickle.dumps.call_args

        assert call is not None

        call_definition = call[0][0]
        assert 'varargs' in call_definition['args']
        assert call_definition['args']['varargs'] is None
    #---

    def test_KwargsAreIncludedInCallIfPopulated(self):
        """
        If kwargs is populated, it's included in the call

        """
        call = self.localclient.cPickle.dumps.call_args

        assert call is not None

        call_definition = call[0][0]
        assert 'kwargs' in call_definition['args']
        assert call_definition['args']['kwargs'] == self.kwargs
    #---

    def test_KwargsAreNotIncludedInCallIfNotPopulated(self):
        """
        If kwargs is not populated, it's not included in the call

        """
        self.client._proxy_handler(self.method_name, self.module, *self.varargs)
        call = self.localclient.cPickle.dumps.call_args

        assert call is not None

        call_definition = call[0][0]
        assert 'kwargs' in call_definition['args']
        assert call_definition['args']['kwargs'] is None
    #---

    def test_BothArgStylesAreIncludedIfPresent(self):
        """
        If both varargs and kwargs are populated, they're both included

        """
        call = self.localclient.cPickle.dumps.call_args

        assert call is not None

        call_definition = call[0][0]
        assert 'varargs' in call_definition['args']
        assert 'kwargs' in call_definition['args']
        assert call_definition['args']['varargs'] == self.varargs
        assert call_definition['args']['kwargs'] == self.kwargs
    #---

    def test_CallNameIsSet(self):
        """
        Tests that `_proxy_handler` appropriately sets the call_name

        """
        call = self.localclient.cPickle.dumps.call_args

        assert call is not None

        call_definition = call[0][0]
        assert call_definition['call_name'] == self.method_name
    #---

    def test_InternalIsNotSet(self):
        """
        Tests that `_proxy_handler` does not enabled the 'internal` option

        """
        call = self.localclient.cPickle.dumps.call_args

        assert call is not None

        call_definition = call[0][0]
        assert call_definition['internal'] is False
    #---

    def test_ModuleIsSet(self):
        """
        Tests that `_proxy_handler` sets the module option

        """
        call = self.localclient.cPickle.dumps.call_args

        assert call is not None

        call_definition = call[0][0]
        assert call_definition['module'] == self.module
    #---

    def test_CallDefinitionIsEncoded(self):
        """
        Tests that `_proxy_handler` encodes the call definition

        """
        assert self.localclient.cPickle.dumps.called
    #---

    def test_ResultIsDecoded(self):
        """
        Tests that `_proxy_handler` decodes the call result

        """
        assert self.localclient.cPickle.loads.called
    #---

    def test_TriggersTheResultHandler(self):
        """
        Tests that the result handler is triggered

        """
        assert self.client._result_handler.called
    #---

    def test_ReturnsTheCallResults(self):
        """
        Tests that `_proxy_handler` returns the result handler's ... results >.>

        """
        assert self.handler_result == self.result
    #---

#---

class Test__result_handler(object):
    """
    Tests RPCClient's `_result_handler` method

    """
    def setup_method(self, method):
        """
        Test Setup

        """
        class SomeRandomError(Exception): pass

        self.result = SomeRandomError('Blah')
        self.traceback = 'Some Traceback'
        self.call_result ={
            'call': {
                'module': 'rpcendpoints',
                'call_name': 'no',
            },
           'result': self.result,
           'error': {
               'traceback': self.traceback,
           },
        }

        self.localclient = reload(rpcclient)

        self.log = mock.MagicMock()
        self.localclient.logging.getLogger = mock.MagicMock(return_value=self.log)
        self.producer = mock.MagicMock()
        self.localclient.producer.Producer = mock.MagicMock(self.producer)

        self.client = self.localclient.RPCClient({})
    #---

    def test_ReturnsResult(self):
        """
        Tests that `_result_handler` returns the result

        """
        self.call_result['result'] = self.result
        self.call_result['error'] = None
        self.handler_result = self.client._result_handler(self.call_result)

        assert self.result == self.handler_result

    #---

    def test_RaisesExceptionIfExists(self):
        """
        Tests that `_result_handler` will raise an exception if one exists

        """
        with pytest.raises(self.result.__class__):
            self.client._result_handler(self.call_result)
    #---

    def test_LogsTracebackIfEnabled(self):
        """
        Tests that `_result_handler` logs  a traceback if logging is enabled.

        """
        try:
            self.client._result_handler(self.call_result)
        except self.result.__class__:
            assert self.traceback in self.log.error.call_args[0][0]
    #---

    def test_DoesNotLogTracebackIfNotEnabled(self):
        """
        Tests that `_result_handler` does not log a traceback if logging is not enabled.

        """
        self.client.log_tracebacks = False
        try:
            self.client._result_handler(self.call_result)
        except self.result.__class__:
            assert self.traceback not in self.log.error.call_args[0][0]
    #---
#---

class Test__fetch_definitions(object):
    """
    Tests RPCClient's `_fetch_definitions` method

    """
    def setup_method(self, method):
        """
        Test Setup

        """
        self.result_data = {
            'result': {
                'definitions': {'bob': 'barker'},
                'hash': 'Some Random Hash',
            }
        }
        self.localclient = reload(rpcclient)

        self.localclient.logging = mock.MagicMock()
        self.producer = mock.MagicMock()
        self.localclient.producer.Producer = mock.MagicMock(self.producer)
        self.localclient.cPickle = mock.MagicMock()
        self.localclient.cPickle.loads.return_value = self.result_data

        self.client = self.localclient.RPCClient({})
        self.client.rabbit_producer.send.return_value = self.result_data
        self.client._fetch_definitions()
    #---

    def test_FormsProperCallRequest(self):
        """
        Tests that `_fetch_definitions` forms the proper call request.  Also tests (indirectly) that the data is
        encoded with cPickle before being sent.

        """
        call = {
            'call_name': 'provide_definitions',
            'args': None,
            'internal': True,
            'module': None,
        }

        self.localclient.cPickle.dumps.assert_called_once_with(call)
    #---

    def test_SendsDataToRabbitMQ(self):
        """
        Tests that `_fetch_definitions` sends the data to the server

        """
        called = self.client.rabbit_producer.send.called
        assert called
    #---

    def test_DecodesResultData(self):
        """
        Tests that `_fetch_definitions` decodes the result data

        """
        self.localclient.cPickle.loads.assert_called_once_with(self.result_data)
    #---

    def test_UpdatesDefinitions(self):
        """
        Tests that `_fetch_definitions` updates the definitions from the call result data.

        """
        assert self.client.definitions == self.result_data['result']['definitions']
    #---

    def test_UpdatesDefinitionsHash(self):
        """
        Tests that `_fetch_definitions` updates the definitions hash from the call result data.

        """
        assert self.client.definitions_hash == self.result_data['result']['hash']
    #---
#---

class Test__build_rpc_modules(object):
    """
    Tests RPCClient's `_build_rpc_modules` method

    """
    def setup_method(self, method):
        """
        Test Setup

        """
        self.module = 'rpcendpoints'
        self.instantiated_module = imp.new_module(self.module)
        self.function = 'bpb'
        self.doc = 'Some docs'
        self.definitions = {
            self.module: {
                self.function: {
                    'args': None,
                    'doc': self.doc,
                }
            }
        }
        self.localclient = reload(rpcclient)

        self.localclient.logging = mock.MagicMock()
        self.producer = mock.MagicMock()
        self.localclient.producer.Producer = mock.MagicMock(self.producer)
        self.localclient.imp.new_module = mock.MagicMock(return_value=self.instantiated_module)

        self.client = self.localclient.RPCClient({})
        self.client.definitions = self.definitions
        self.client._build_module_functions = mock.MagicMock()

        self.client._build_rpc_modules()

    #---

    def teardown_method(self, method):
        """
        Test Cleanup

        """
        if self.module in sys.modules:
            del sys.modules[self.module]
    #---

    def test_CreatesNewModule(self):
        """
        Tests that `_build_rpc_modules` creates a new module with the requested name (in defs)

        """
        self.localclient.imp.new_module.assert_called_once_with(self.module)
    #---

    def test_TriggersFunctionBuilds(self):
        """
        Tests that `_build_rpc_modules` triggers the function builds

        """
        self.client._build_module_functions.assert_called_once_with(self.definitions[self.module], self.instantiated_module)
    #---

    def test_SetsProxyClassAttribute(self):
        """
        Tests that `_build_rpc_modules` sets a reference to the client class in the module (for callback use)

        """
        assert self.instantiated_module.proxy_class == self.client
    #---

    def test_RegistersModule(self):
        """
        Tests that `_build_rpc_modules` registers the module with Python

        """
        assert self.module in sys.modules
        assert sys.modules[self.module] == self.instantiated_module
    #---
#---

class Test__build_module_functions(object):
    """
    Tests RPCClient's `_build_module_functions` method

    """
    def setup_method(self, method):
        """
        Test Setup

        """
        self.module = 'rpcendpoints'
        self.instantiated_module = imp.new_module(self.module)
        self.instantiated_module.proxy_class = self
        self.function = 'bpb'
        self.doc = 'Some docs'
        self.def_args = {
            'defined': {
                'bob': 'barker',
            },
        }
        self.definitions = {
            self.module: {
                self.function: {
                    'args': None,
                    'doc': self.doc,
                }
            }
        }

        self.args = 'bob'
        self.proxy_args = ', bob'
        self.arg_strings = (self.args, self.proxy_args)
        self.localclient = reload(rpcclient)

        self.localclient.logging = mock.MagicMock()
        self.producer = mock.MagicMock()
        self.localclient.producer.Producer = mock.MagicMock(self.producer)

        self.client = self.localclient.RPCClient({})
        self.client._convert_args_to_strings = mock.MagicMock(return_value=self.arg_strings)

        self.client._build_module_functions(self.definitions[self.module], self.instantiated_module)
    #---

    def _proxy_handler(self, method_name, module, *varargs, **kwargs):
        """
        Helper for proxy call tests
        """
        return method_name, module, varargs, kwargs
    #---

    def test_ConvertsArgsToStringsIfTheyAreAvailable(self):
        """
        Tests that `_build_module_functions` converts the function args to strings for use in the proxy method
        definitions.

        """
        self.definitions[self.module][self.function]['args'] = self.def_args
        self.client._build_module_functions(self.definitions[self.module], self.instantiated_module)

        self.client._convert_args_to_strings.assert_called_once_with(self.definitions[self.module][self.function]['args']['defined'])
    #---

    def test_DoesNotConvertArgsToStringsIfTheyAreNotAvailable(self):
        """
        Tests that `_build_module_functions`

        """
        called = self.client._convert_args_to_strings.called
        assert not called
    #---

    def test_CreatesFunctionOnModuleWithProperName(self):
        """
        Tests that `_build_module_functions` creates a function on the module with the provided name

        """
        assert self.function in self.instantiated_module.__dict__
    #---

    def test_SetsTheFunctionsDocumentation(self):
        """
        Tests that `_build_module_functions` sets the function's doctag.  This test has to strip the doctag due to the
        proxy function's definition being text and adding formatting/spacing.

        """
        assert self.doc == self.instantiated_module.__dict__[self.function].__doc__.strip()
    #---

    def test_SetsProxyHandlerCallWithAppropriateInformation(self):
        """
        Tests that `_build_module_functions` appropriately sets the proxy function's arguments

        """
        self.definitions[self.module][self.function]['args'] = self.def_args
        self.client._build_module_functions(self.definitions[self.module], self.instantiated_module)

        test_value = 'some Test'
        proxy_handler_return = self.instantiated_module.__dict__[self.function](test_value)

        assert proxy_handler_return == (self.function, self.module, (test_value,), {})
    #---
#---

class Test__convert_args_to_strings(object):
    """
    Tests RPCClient's `_convert_args_to_strings` method

    """
    def setup_method(self, method):
        """
        Test Setup

        """
        self.localclient = reload(rpcclient)

        self.localclient.logging = mock.MagicMock()
        self.producer = mock.MagicMock()
        self.localclient.producer.Producer = mock.MagicMock(self.producer)

        self.client = self.localclient.RPCClient({})
    #---

    def test_ConvertsVarArgsToStringsIfTheyAreAvailable(self):
        """
        Tests that `_convert_args_to_strings` converts varargs to the function argument and proxy handler call argument
        strings.

        """
        varargs = ('bob', 'barker')
        args = dict(kw=None, var=varargs)
        arg_tuple = self.client._convert_args_to_strings(args)

        expected_return = ('%s, %s' % (varargs[0], varargs[1]), ', %s, %s' % (varargs[0], varargs[1]))

        assert arg_tuple == expected_return
    #---

    def testConvertsKWargsToStringsIfTheyAreAvailable(self):
        """
        Tests that `_convert_args_to_strings`converts kwargs to the function argument and proxy handler call argument
        strings.

        """
        arg1 = 'wat'
        arg2 = 'bob'
        kwargs = {arg1: 'No', arg2: 'barker'}
        args = dict(kw=kwargs, var=None)
        arg_tuple = self.client._convert_args_to_strings(args)

        expected_return = ('%s = "%s", %s = "%s"' % (arg1, kwargs[arg1], arg2 , kwargs[arg2] ),
                           ', %s = %s, %s = %s' % (arg1, arg1, arg2, arg2))

        assert arg_tuple == expected_return
    #---
#---
class Test__remove_rpc_modules(object):
    """
    Tests RPCClient's `_remove_rpc_modules` method

    """
    def setup_method(self, method):
        """
        Test Setup

        """
        self.localclient = reload(rpcclient)

        self.localclient.logging = mock.MagicMock()
        self.producer = mock.MagicMock()
        self.localclient.producer.Producer = mock.MagicMock(self.producer)

        self.client = self.localclient.RPCClient({})

        self.client.definitions = {
            'rpcendpoints': {
            },
            'bobbarker': {
            }
        }
        sys.modules['rpcendpoints'] = imp.new_module('testmodule')
        self.client._remove_rpc_modules()
    #---

    def test_SystemModulesAreNotTouchedIfNoDefinitions(self):
        """
        Tests that `_remove_rpc_modules` does not alter sys.modules if there are no definitions

        """
        self.client.definitions = {}
        new_module = imp.new_module('testmodule')
        sys.modules['rpcendpoints'] = new_module

        self.client._remove_rpc_modules()

        # Screwed up way to test this, but it works
        assert sys.modules['rpcendpoints'] is new_module
    #---

    def test_RemovesDefinedModulesFromSystemModules(self):
        """
        Tests that `_remove_rpc_modules` removes defined modules from sys.modules

        """
        assert 'rpcendpoints' not in sys.modules
        assert 'bobbarker' not in sys.modules
    #---

#---
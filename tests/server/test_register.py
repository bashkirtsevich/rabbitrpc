# coding=utf-8
#
# $Id: $
#
# NAME:         test_register.py
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
#   Tests the server 'register' module.
#


import inspect
from rabbitrpc.server import register

class Test_RPCFunction(object):
    """
    Tests register's `RPCFunction` method.

    """

    def setup_method(self, method):
        """
        Test setup

        """
        class RPCServerStub(object):
            definitions = {}

            @classmethod
            def register_definition(cls, definition):
                cls.definitions.update(definition)
        #---

        self.server_stub = RPCServerStub
        self.module = self.__module__.split('.')[-1]

        self.local_register = reload(register)
        self.local_register.rpcserver.RPCServer = RPCServerStub
    #---

    def test_DoctagIsIncluded(self):
        """
        Tests that a function's raw doctag is included in the definitions.

        """
        def function_with_doctag():
            """
            I have a doctag!

            """
        #---
        self.local_register.RPCFunction(function_with_doctag)

        func = self.server_stub.definitions[self.module]['function_with_doctag']

        assert func['doc'] == inspect.cleandoc(function_with_doctag.__doc__)
    #---

    def test_VarArgsAreIncluded(self):
        """
        Tests that varargs are included with the function definition.

        """
        def function_with_varargs(arg1, arg2):
            return
        #---
        self.local_register.RPCFunction(function_with_varargs)

        defined_args = self.server_stub.definitions[self.module]['function_with_varargs']['args']['defined']['var']
        assert defined_args == ['arg1', 'arg2']
    #---

    def test_KeywordArgsAreIncluded(self):
        """
        Tests that keyword args are included with the function definition

        """
        def function_with_kwargs(argument1='test1', argument2='test2'):
            return
        #---
        self.local_register.RPCFunction(function_with_kwargs)

        defined_args = self.server_stub.definitions[self.module]['function_with_kwargs']['args']['defined']['kw']
        assert defined_args == {'argument1': 'test1', 'argument2': 'test2'}
    #---

    def test_KeywordAndVarArgsAreIncluded(self):
        """
        Tests that var and keyword args are included when they exist at the same time.

        """
        def function_with_var_and_kwargs(arg1, arg2, argument1='test1', argument2='test2'):
            return
        #---
        self.local_register.RPCFunction(function_with_var_and_kwargs)

        defined_args = self.server_stub.definitions[self.module]['function_with_var_and_kwargs']['args']['defined']

        defined_var_args = defined_args['var']
        defined_kw_args = defined_args['kw']

        assert defined_var_args == ['arg1', 'arg2']
        assert defined_kw_args == {'argument1': 'test1', 'argument2': 'test2'}
    #---

    def test_NoArgumentsSetsNone(self):
        """
        Tests that when there are no arguments 'defined' is set to `None`.

        """
        def function_without_args():
            return
        #---
        self.local_register.RPCFunction(function_without_args)

        defined_args = self.server_stub.definitions[self.module]['function_without_args']['args']
        assert defined_args is None
    #---

    def test_KeywordParameterIsIncluded(self):
        """
        Tests that when there is a **<name> keyword argument, it is included

        """
        def function_with_kw(**kw):
            return
        #---
        self.local_register.RPCFunction(function_with_kw)

        kwargs_var_name = self.server_stub.definitions[self.module]['function_with_kw']['args']['kwargs_var']
        assert kwargs_var_name == 'kw'
    #---

    def test_VarParameterIsIncluded(self):
        """
        Tests that when there is a *<name> var argument, it is included

        """
        def function_with_var(*var):
            return
        #---
        self.local_register.RPCFunction(function_with_var)

        varargs_var_name = self.server_stub.definitions[self.module]['function_with_var']['args']['varargs_var']
        assert varargs_var_name == 'var'
    #---

    def test_BothVarAndKeywordParametersAreIncluded(self):
        """
        Tests that when there is both **<name> keyword parameter and a *<name> var parameter, they are both included

        """
        def function_with_var_and_kw(*varargs, **kwargs):
            return
        #---
        self.local_register.RPCFunction(function_with_var_and_kw)

        kwargs_var_name = self.server_stub.definitions[self.module]['function_with_var_and_kw']['args']['kwargs_var']
        assert kwargs_var_name == 'kwargs'

        varargs_var_name = self.server_stub.definitions[self.module]['function_with_var_and_kw']['args']['varargs_var']
        assert varargs_var_name == 'varargs'
    #---

    def test_FunctionModuleIsIncluded(self):
        """
        Tests that the definitions include the function's module name

        """
        def function_local_module():
            return
        #---
        self.local_register.RPCFunction(function_local_module)

        assert self.module in self.server_stub.definitions
    #---

    def test_FunctionNameIsIncluded(self):
        """
        Tests that the definitions include the function's name

        """
        def function_local_module2():
            return
        #---
        self.local_register.RPCFunction(function_local_module2)

        assert 'function_local_module2' in self.server_stub.definitions[self.module]
    #---
#---
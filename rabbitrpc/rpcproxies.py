# coding=utf-8
#
# $Id: $
#
# NAME:         rpcproxies.py
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
#   Proxy functionality for RPC calls.
#

from types import MethodType
import new


def RPCFunctionProxy(*args, **kwargs):
    """

    :return:
    """
    return
#---


class RPCClassProxy(object):
    """
    Provides a proxy for RPC calls to classes.  Target methods must be class methods (for obvious reasons).  The proxy
    method will construct a Python data-structure that will be used to inform the RPC server what method we want to
    execute.

    This class should _never_ be invoked directly.  Use the `generate` method to properly create custom RPC classes that
    mimic the remote class.  Method definitions are produced by the RPC server and can be requested by the RPC client
    class (which should be what invokes `generate`).

    """
    methods = {
        'dog': {
            'required_args': 0,
            'doc': '',
        },

        'echo': {
            'required_args': 1,
            'doc': 'This is a simple echo service',
        },

        'trance_pants': {
            'required_args': 0,
            'doc': 'Bob Barker is present',
        },
    }

    @classmethod
    def generate(cls, definitions = None, name = None):
        """
        Generates a custom RPCClassProxy class that impersonates the remote class.

        :param definitions: RPC/API Class definition
        :type definitions: dict
        :param name: What to name the proxy class
        :type name: str

        :rtype: RPCClassProxy

        """
        if definitions is None:
            definitions = {}
        if name:
            cls.__name__ = name

        cls.methods.update(definitions)

        # Generates a stub for the new method to call (which in turn calls the proxy method)
        def generateStub(method_name, method):
            def stub(self, *args, **kwargs):
                return cls._proxy_method_call(self, method_name, method, *args, **kwargs)

            stub.__name__ = method_name
            stub.__doc__ = method['doc']
            return stub
        #---

        # Create instance methods on the class
        for method_name in cls.methods:
            if hasattr(cls, method_name):
                continue

            method_def = cls.methods[method_name]
            proxy_stub = new.instancemethod(generateStub(method_name, method_def), None, cls)
            setattr(cls, method_name, proxy_stub)

        # Return the custom class
        return cls
    #---

    # TODO: Finish me
    def _registerMethods(self):
        """
        This method should be used to refresh the abilities of an instantiated proxy class.

        :return:

        """
        orig_func = self._method_mask.__func__

        for method in self.methods:
            if hasattr(self, method):
                continue

            self._method_mask.__func__.__name__ = method
            setattr(self, method, new.instancemethod(self._method_mask, None, self.__class__))
    #---

    # TODO: Finish me
    def _proxy_method_call(self, method_name, method, *args, **kwargs):
        """
        This method does the actual work of proxying a registered instance method call out to the remote server via the
        MQ.

        :param method_name: The name of the method that was invoked
        :param method: This appears to be the method definition from the RPC server... WHAT ARE YOU!?
        :param args: The args to pass to the invoked method
        :param kwargs: The keyword arguments to pass to the invoked method
        :return:
        """
        print method_name
        print method
        print args
        print kwargs
    #---
#---
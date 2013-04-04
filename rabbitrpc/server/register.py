# coding=utf-8
#
# $Id: $
#
# NAME:         register.py
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
#   Provides RPC function/class registration functions (via decorators)
#

from . import rpcserver
import inspect


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

    func_wire_protocol = {
        function.__name__: dict(args=args, doc=inspect.cleandoc(function.__doc__), module=function.__module__)
    }

    rpcserver.RPCServer.register_definition(func_wire_protocol)

    return function
#---
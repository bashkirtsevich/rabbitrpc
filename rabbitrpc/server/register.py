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

import collections
from . import rpcserver
import inspect


def RPCFunction(function):
    """
    Decorator to register a function as an RPC function.

    :param function:  Incoming function to register

    :rtype: func

    """
    kwargs = None
    varargs = None
    docs = None

    # Reads the function's args and arranges them into a format that's easy to use on the other side
    argspec = inspect.getargspec(function)

    if argspec.defaults:
        num_args = len(argspec.args)
        kwargs_start = num_args - len(argspec.defaults)

        # Only keyword args
        if kwargs_start == num_args:
            kwargs = dict(zip(argspec.args,argspec.defaults))
        else:
            varargs = argspec.args[:kwargs_start]
            kwargs = dict(zip(argspec.args[kwargs_start:],argspec.defaults))
    elif argspec.args:
        varargs = argspec.args

    if not varargs and not kwargs:
        defined_args = None
    else:
        defined_args = dict(var=varargs, kw=kwargs)

    # :(
    if defined_args is None and argspec.keywords is None and argspec.varargs is None:
        args = None
    else:
        args = {'defined': defined_args, 'kwargs_var': argspec.keywords, 'varargs_var': argspec.varargs}

    if function.__doc__:
        docs = inspect.cleandoc(function.__doc__)

    # We're not interested in the full path
    stripped_module = function.__module__.split('.')[-1]
    function_definition = {
        stripped_module: {
            function.__name__: dict(args=args, doc=docs)
        }
    }

    rpcserver.RPCServer.register_definition(function_definition, {stripped_module: function.__module__})

    return function
#---
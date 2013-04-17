# coding=utf-8
#
# $Id: $
#
# NAME:         rpcendpoints.py
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
#   Defines some simple endpoints as examples for the rpc server
#

from rabbitrpc.server import register


@register.RPCFunction
def no_args():
    """
    A function with no args.

    """
    return 'I have no args'
#---

@register.RPCFunction
def no_return():
    """
    This function does not return anything

    """
    return
#---

@register.RPCFunction
def echo(to_echo):
    """
    Just a simple 'echo' function.

    :param to_echo: Something you want to echo back to yourself
    :return: Whatever was returned
    """

    return to_echo
#---

@register.RPCFunction
def accept_varargs(arg1, arg2):
    """
    Just demonstrates that varargs work.

    :param arg1: First arg
    :param arg2: Second arg
    :return:
    """

    return 'arg1: %s\narg1: %s' % (arg1,arg2)
#---

@register.RPCFunction
def accept_keywords(random_arg='Yes', bob='The price is WRONG'):
    """
    Just demonstrates that keyword arguments work too.

    :param random_arg: A keyword arg
    :param bob: Another keyword arg
    :return:
    """

    return 'random_arg: %s\nbob: %s' % (random_arg,bob)
#---

@register.RPCFunction
def varargs_and_keywords(arg1, random_arg='Yes', bob='The price is WRONG'):
    """
    Just demonstrates that keyword arguments work too.

    :param arg1: First arg
    :param random_arg: A keyword arg
    :param bob: Another keyword arg
    :return:
    """

    return 'arg1: %s\nrandom_arg: %s\nbob: %s' % (arg1, random_arg,bob)
#---
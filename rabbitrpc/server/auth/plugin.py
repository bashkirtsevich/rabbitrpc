# coding=utf-8
#
# $Id: $
#
# NAME:         plugin.py
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
#   Class decorators which provide auth plugin functionality for the RPC server.
#

from rabbitrpc.server import rpcserver


class ServerAuthenticationPluginError(Exception): pass

# Authentication

def rpc_authentication(cls):
    """
    Registers an authentication plugin with the RPC server

    :param cls: The class being registered
    :return: Untouched class definition

    """
    _validate_authentication_class(cls)

    rpcserver.RPCServer.register_authentication_plugin(cls)
#---

def _validate_authentication_class(cls):
    """
    Validates that an authentication class implements the API in a sane manner.

    :param cls: The authentication API class to validate
    :raises: AuthenticationPluginError

    """
    required_methods = ('start', 'authenticate', 'about')

    for method in required_methods:
        if method not in cls.__dict__:
            raise ServerAuthenticationPluginError("'%s' method is missing" % method)
#---

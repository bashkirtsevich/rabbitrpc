# coding=utf-8
#
# $Id: $
#
# NAME:         client.py
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
#   RPC client demo.  It's literally this simple.
#

from rabbitrpc.client import rpcclient
from rabbitrpc.examples.client.config import RABBITMQ_CONFIG

client = rpcclient.RPCClient(RABBITMQ_CONFIG, print_tracebacks=True)
client.start()

import rpcendpoints
result = rpcendpoints.varargs_and_keywords('This is a vararg')

print 'result: %s' % result

# Help works too, un-comment this for a demo
# help(rpcendpoints.varargs_and_keywords)

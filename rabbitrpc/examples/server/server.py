# coding=utf-8
#
# $Id: $
#
# NAME:         server.py
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
#   Just a simple example RPC server which utilizes RabbitRPC
#

import logging
from rabbitrpc.server import rpcserver
from rabbitrpc.examples.server.config import RABBITMQ_CONFIG

# This loads the module which has our endpoints we want to register
from rabbitrpc.examples.server import rpcendpoints

# Set up root logger
log_format = '%(asctime)s %(name)s [%(levelname)s]: %(message)s'
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)         # Debug is insanely noisy, as in wall of text noisy (due to pika)
formatter = logging.Formatter(log_format)

# Set up console output
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
root_logger.addHandler(console_handler)

# Local logger
log = logging.getLogger('rpcserver.test')

# Init the RPC server
server = rpcserver.RPCServer(RABBITMQ_CONFIG)
log.info('Starting server')

# Run the server until we get CTRL+C
try:
    server.run()
except KeyboardInterrupt:
    server.stop()
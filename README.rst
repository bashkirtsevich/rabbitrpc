=========
RabbitRPC
=========
:Author: Nick Whalen <nickw@mindstorm-networks.net>

RabbitRPC is an RPC over AMQP framework for Python.  It allows the user to worry less about how he's doing remote method
calls and more about her/his actual code.  It was written to scratch an itch that developed during the development of a
much larger software project which needed a highly scalable internal API.

As of 0.6.0, RabbitRPC is capable of completely mocking remote functions and their modules.  This means that using the
framework is as simple as instantiating the RPCClient class and calling 'start()' (after having written and registered
some server-side components, of course).  See below for an example of how this works.

RabbitRPC tries to keep things feeling as native as possible.  As mentioned above, imports and function calls on modules
work exactly like you'd use them for local code.  The RPC client will also return the exact data that was produced from
the server-side functions (within pickleable limits).  Should an exception occur in the remote code, that exact
exception will be thrown and its traceback will be shown.

Please keep in mind, this package is still a work in progress.  Here's a current list of what is planned before 1.0.0:

* Add support for remote class registrations and stateful class management from within the server, on a per-client basis.
* Authentication
* Authorization (along with the ability to create groups/roles specifying what functions/methods/classes may or may not be run by a particular account.
* Dead-letter support in AMQP backend (for those rare times when something goes wrong and you need to recover).
* 'Versioning' for RPC endpoints, which would allow servers to serve subsets of an API/set of endpoints

Real documentation is in the plans, my time is just limited at the moment.  All of the source is well documented with
doctags.  Please check that out for the time being.

**Bugs and Feature Requests:**

Please leave them on the project's Github tracker: https://github.com/nwhalen/rabbitrpc/issues

Example
=======
For actual, working code examples, see the 'examples' directory in the source tree.  You'll need a RabbitMQ server set
up before you run them.  But you know that.

**RPC Endpoints**::

    from rabbitrpc.server import register

    @register.RPCFunction
    def the_price_is_wrong():
        print '-- Bob Barker'

**RPC Server**::

    import <your endpoint modules here>
    from config import RABBITCONF

    server = rpcserver.RPCServer(RABBITCONF)

    try:
        server.run()
    except KeyboardInterrupt:
        server.stop()

**RPC Client**::

    from config import RABBITCONF

    # Fire up the client
    client = rpcclient.RPCClient(RABBITCONF)
    client.start()

    # This module is dynamically created by the client, along with it's function 'all_the_things'.  Calling
    # 'all_the_things' will cause the client to transparently proxy the call out to the RPC server, via RabbitMQ.
    import rpcendpoints
    result = rpcendpoints.the_price_is_wrong()

    print 'result: %s' % result


Dependencies
============

* `pika`: http://pypi.python.org/pypi/pika

**Tests Only:**

* `pytest`: http://pypi.python.org/pypi/pytest
* `mock`: http://pypi.python.org/pypi/mock


License
=======
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

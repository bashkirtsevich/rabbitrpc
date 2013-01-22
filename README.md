=========
RabbitRPC
=========

RabbitRPC is an RPC over AMQP framework.  It allows the user to worry less about how he's doing remote method calls and
more about her/his actual code.  It was written to scratch an itch that developed during the development of a much
larger software project which needed a highly scalable internal API.

The framework is currently a work in progress.  The basic client and server have been written/tested, but lack anything
that make the framework 'feel' more like the method calls we're used to.  The next goal is to provide an additional
layer on top of the existing client/server that will actually provide a dynamic interface which would allow you to
do something like this on the client side::

        import rpcclient

        foo_class = rpcclient.RPCClient('remote_api_module_name', '/path/to/config/file')
        return_value = foo_class.remote_api_method()

This will happen via server-side method registration.  The RPC server will keep track of all public methods and, at
the request of the RPC client, provide a list of these methods and their parameters.  The RPC client will them use
this list to dynamically build a stubbed out class.  The stubs will call a translation method which will translate and
pickle the method call and send it to the RPC request queue.  A RPC worker can then take the API request package,
process it, and return the results via the RPC server library.

Future plans also include the ability for the RPC workers to be versioned.  This means you can spin up separate worker
hives for varying implementations of your API.

============
Example
============
**RPC Server Example:**

    from rabbitrpc import rabbitrpcserver

    def rpc_callback(body):
        # Based on the body content, select which method to call
        # Call it
        # Return the results

    self.rpc_server = rabbitrpcserver.RabbitRPCServer(rpc_callback, 'RPCRequestQueue')

    try:
        self.rpc_server.run()
    finally:
        self.rpc_server.stop()

**RPC Client Example:**

    from rabbitrpc import rabbitrpcclient

    rpc_client = rabbitrpcclient.RabbitRPCClient('RPCRequestQueue', reply_timeout=3000)

    request = # API call definition, any pickleable structure

    reply = rpc_client.send(request)

    print 'API REPLY: %s' % reply

============
Dependencies
============

* `pika`: http://pypi.python.org/pypi/pika

Tests Only:
* `pytest`: http://pypi.python.org/pypi/pytest
* `mock`: http://http://pypi.python.org/pypi/mock

=======
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
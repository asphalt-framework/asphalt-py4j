Using the Java gateway
======================

Given the inherently synchronous nature of the Py4J API, it is strongly recommended that all code
using Java gateways is run in a thread pool. The :class:`~py4j.java_gateway.JavaGateway` class is
not wrapped in any way by the component so slow calls to any Java API will block the event loop if
not run in a worker thread.

The following is a simple example that writes the text "Hello, Python!" to a file at
``/tmp/test.txt``. More examples can be found in the ``examples`` directory of the source
distribution.

.. code-block:: python3

    from asyncio_extras import threadpool


    async def handler(ctx):
        async with threadpool():
            f = ctx.java.jvm.java.io.File('/tmp/test.txt')
            writer = ctx.java.jvm.java.io.FileWriter(f)
            writer.write('Hello, Python!')
            writer.close()

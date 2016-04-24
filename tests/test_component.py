import os

import pytest
from py4j.java_gateway import JavaGateway, CallbackServerParameters

from asphalt.core.context import Context
from asphalt.py4j.component import Py4JComponent


@pytest.mark.asyncio
async def test_default_gateway(caplog):
    """Test that the default gateway is started and is available on the context."""
    async with Context() as context:
        await Py4JComponent().start(context)

    records = [record for record in caplog.records if record.name == 'asphalt.py4j.component']
    records.sort(key=lambda r: r.message)
    assert len(records) == 2
    assert records[0].message.startswith("Configured Py4J gateway "
                                         "(default / ctx.java; address=127.0.0.1, port=")
    assert records[1].message == 'Py4J gateway (default) shut down'


@pytest.mark.parametrize('params', [
    CallbackServerParameters('1.2.3.4', 5678),
    {'address': '1.2.3.4', 'port': 5678}
], ids=['object', 'dict'])
def test_callback_server_params(params):
    """
    Test that the callback server parameters can be given as both a CallbackServerParameters
    instance or a dict.

    """
    params = Py4JComponent.configure_gateway('default', callback_server=params)[-3]
    assert params.address == '1.2.3.4'
    assert params.port == 5678


def test_classpath_pkgname_substitution():
    """
    Test that package names in the class path are substituted with the corresponding absolute
    directory paths.

    """
    import asphalt.py4j
    classpath = Py4JComponent.configure_gateway('default',
                                                classpath='{asphalt.py4j}/javadir/*')[-2]
    assert classpath == '%s/javadir/*' % os.path.dirname(asphalt.py4j.__file__)
    assert classpath.endswith(os.path.join('asphalt', 'py4j', 'javadir', '*'))


@pytest.mark.asyncio
async def test_callback_server():
    """Test that the gateway's callback server works when enabled in the configuration."""
    class NumberCallable:
        def call(self):
            return 7

        class Java:
            implements = ['java.util.concurrent.Callable']

    async with Context() as context:
        await Py4JComponent(callback_server=True).start(context)
        executor = context.java.jvm.java.util.concurrent.Executors.newFixedThreadPool(1)
        try:
            future = executor.submit(NumberCallable())
            assert future.get() == 7
        finally:
            executor.shutdown()


@pytest.mark.asyncio
async def test_multiple_gateways(caplog):
    """Test that a multiple gateway configuration works as intended."""
    async with Context() as context:
        await Py4JComponent(gateways={
            'java1': {},
            'java2': {}
        }).start(context)
        assert isinstance(context.java1, JavaGateway)
        assert isinstance(context.java2, JavaGateway)

    records = [record for record in caplog.records if record.name == 'asphalt.py4j.component']
    records.sort(key=lambda r: r.message)
    assert len(records) == 4
    assert records[0].message.startswith("Configured Py4J gateway "
                                         "(java1 / ctx.java1; address=127.0.0.1, port=")
    assert records[1].message.startswith("Configured Py4J gateway "
                                         "(java2 / ctx.java2; address=127.0.0.1, port=")
    assert records[2].message == 'Py4J gateway (java1) shut down'
    assert records[3].message == 'Py4J gateway (java2) shut down'


@pytest.mark.asyncio
async def test_gateway_close():
    """
    Test that shutting down the context does not shut down the Java side gateway if launch_jvm was
    False.

    """
    gateway = JavaGateway.launch_gateway()
    async with Context() as context:
        await Py4JComponent(gateway={'port': gateway.gateway_parameters.port},
                            launch_jvm=False).start(context)
        context.java.jvm.java.lang.System.setProperty('TEST_VALUE', 'abc')

    assert gateway.jvm.java.lang.System.getProperty('TEST_VALUE') == 'abc'
    gateway.shutdown()

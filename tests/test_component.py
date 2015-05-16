import os

from py4j.java_gateway import JavaGateway, CallbackServerParameters
from asphalt.core.context import Context
import pytest

from asphalt.py4j.component import Py4JComponent


@pytest.mark.asyncio
def test_default_gateway(caplog):
    """Tests that the default gateway is started and is available on the context."""

    component = Py4JComponent()
    context = Context()

    yield from component.start(context)
    try:
        assert isinstance(context.java, JavaGateway)
    finally:
        yield from context.__aexit__(None, None, None)

    records = [record for record in caplog.records() if record.name == 'asphalt.py4j.component']
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
    Tests that the callback server parameters can be given as both a
    CallbackServerParameters instance or a dict.
    """

    params = Py4JComponent.create_gateway('default', callback_server=params)[-3]
    assert params.address == '1.2.3.4'
    assert params.port == 5678


def test_classpath_pkgname_substitution():
    """
    Tests that package names in the class path are substituted with the
    corresponding absolute directory paths.
    """

    import asphalt.py4j
    classpath = Py4JComponent.create_gateway('default', classpath='{asphalt.py4j}/javadir/*')[-2]
    assert classpath == '%s/javadir/*' % os.path.dirname(asphalt.py4j.__file__)
    assert classpath.endswith(os.path.join('asphalt', 'py4j', 'javadir', '*'))


@pytest.mark.asyncio
def test_callback_server():
    """
    Tests that the gateway's callback server works when enabled in the
    configuration.
    """

    class NumberCallable:
        def call(self):
            return 7

        class Java:
            implements = ['java.util.concurrent.Callable']

    component = Py4JComponent(callback_server=True)
    context = Context()

    yield from component.start(context)
    try:
        executor = context.java.jvm.java.util.concurrent.Executors.newFixedThreadPool(1)
        try:
            future = executor.submit(NumberCallable())
            assert future.get() == 7
        finally:
            executor.shutdown()
    finally:
        yield from context.__aexit__(None, None, None)


@pytest.mark.asyncio
def test_multiple_gateways(caplog):
    """Tests that a multiple gateway configuration works as intended."""

    component = Py4JComponent(gateways={
        'java1': {},
        'java2': {}
    })
    context = Context()
    yield from component.start(context)
    try:
        assert isinstance(context.java1, JavaGateway)
        assert isinstance(context.java2, JavaGateway)
    finally:
        yield from context.__aexit__(None, None, None)

    records = [record for record in caplog.records() if record.name == 'asphalt.py4j.component']
    records.sort(key=lambda r: r.message)
    assert len(records) == 4
    assert records[0].message.startswith("Configured Py4J gateway "
                                         "(java1 / ctx.java1; address=127.0.0.1, port=")
    assert records[1].message.startswith("Configured Py4J gateway "
                                         "(java2 / ctx.java2; address=127.0.0.1, port=")
    assert records[2].message == 'Py4J gateway (java1) shut down'
    assert records[3].message == 'Py4J gateway (java2) shut down'


def test_gateway_close():
    """
    Tests that shutting down the context does not shut down the Java
    side gateway if launch_jvm was False.
    """

    gateway = JavaGateway.launch_gateway()
    component = Py4JComponent(gateway={'port': gateway.gateway_parameters.port}, launch_jvm=False)
    context = Context()
    yield from component.start(context)
    context.java.jvm.java.lang.System.setProperty('TEST_VALUE', 'abc')
    yield from context.__aexit__(None, None, None)
    assert gateway.jvm.java.lang.System.getProperty('TEST_VALUE') == 'abc'
    gateway.shutdown()


def test_conflicting_config():
    exc = pytest.raises(ValueError, Py4JComponent, gateways={'default': {}}, backend='smtp')
    assert str(exc.value) == ('specify either a "gateways" dictionary or the default gateway\'s '
                              'options directly, but not both')

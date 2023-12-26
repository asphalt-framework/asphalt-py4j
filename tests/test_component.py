from __future__ import annotations

import logging
import os
from typing import Any

import asphalt.py4j
import pytest
from asphalt.core.context import Context
from asphalt.py4j.component import Py4JComponent
from py4j.java_gateway import CallbackServerParameters, GatewayParameters, JavaGateway
from pytest import LogCaptureFixture


@pytest.mark.anyio
@pytest.mark.parametrize(
    "kwargs, resource_name",
    [
        pytest.param({}, "default", id="default"),
        pytest.param({"resource_name": "alt"}, "alt", id="alternate"),
    ],
)
async def test_default_gateway(
    kwargs: dict[str, Any], resource_name: str, caplog: LogCaptureFixture
) -> None:
    """Test that the default gateway is started and is available on the context."""
    caplog.set_level(logging.INFO, logger="asphalt.py4j.component")
    async with Context() as context:
        await Py4JComponent(**kwargs).start(context)
        context.require_resource(JavaGateway, resource_name)

    records = [
        record for record in caplog.records if record.name == "asphalt.py4j.component"
    ]
    records.sort(key=lambda r: r.message)
    assert len(records) == 2
    assert records[0].message.startswith(
        f"Configured Py4J gateway ({resource_name}; address=127.0.0.1, port="
    )
    assert records[1].message == f"Py4J gateway ({resource_name}) shut down"


def test_bad_classpath_entry() -> None:
    """Test that a built-in package in the classpath results in a proper ValueError."""
    with pytest.raises(ValueError):
        Py4JComponent(classpath=["{builtins}"])


def test_gateway_params() -> None:
    """Test that a GatewayParameters instance is used as-is."""
    params = GatewayParameters()
    component = Py4JComponent(gateway=params)
    assert component.gateway_params is params


@pytest.mark.parametrize(
    "params",
    [
        pytest.param(CallbackServerParameters("1.2.3.4", 5678), id="object"),
        pytest.param({"address": "1.2.3.4", "port": 5678}, id="dict"),
    ],
)
def test_callback_server_params(
    params: CallbackServerParameters | dict[str, Any],
) -> None:
    """
    Test that the callback server parameters can be given as both a
    CallbackServerParameters instance or a dict.

    """
    component = Py4JComponent(callback_server=params)
    assert component.callback_server_params.address == "1.2.3.4"
    assert component.callback_server_params.port == 5678


def test_classpath_pkgname_substitution() -> None:
    """
    Test that package names in the class path are substituted with the corresponding
    absolute directory paths.

    """
    component = Py4JComponent(classpath="{asphalt.py4j}/javadir/*")
    assert component.classpath == f"{os.path.dirname(asphalt.py4j.__file__)}/javadir/*"
    assert component.classpath.endswith(os.path.join("asphalt", "py4j", "javadir", "*"))


@pytest.mark.anyio
async def test_callback_server() -> None:
    """
    Test that the gateway's callback server works when enabled in the configuration.
    """

    class NumberCallable:
        def call(self) -> int:
            return 7

        class Java:
            implements = ["java.util.concurrent.Callable"]

    async with Context() as context:
        await Py4JComponent(callback_server=True).start(context)
        gateway = context.require_resource(JavaGateway)
        executor = gateway.jvm.java.util.concurrent.Executors.newFixedThreadPool(1)
        try:
            future = executor.submit(NumberCallable())
            assert future.get() == 7
        finally:
            executor.shutdown()


@pytest.mark.anyio
async def test_gateway_close() -> None:
    """
    Test that shutting down the context does not shut down the Java side gateway if
    launch_jvm was False.

    """
    gateway = JavaGateway.launch_gateway()
    async with Context() as context:
        await Py4JComponent(
            gateway={"port": gateway.gateway_parameters.port}, launch_jvm=False
        ).start(context)
        gateway2 = context.require_resource(JavaGateway)
        gateway2.jvm.java.lang.System.setProperty("TEST_VALUE", "abc")

    assert gateway.jvm.java.lang.System.getProperty("TEST_VALUE") == "abc"
    gateway.shutdown()

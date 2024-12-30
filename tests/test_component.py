from __future__ import annotations

import os
from typing import Any, ClassVar

import pytest
from asphalt.core import Context, get_resource_nowait, start_component
from py4j.java_gateway import CallbackServerParameters, GatewayParameters, JavaGateway

import asphalt.py4j
from asphalt.py4j import Py4JComponent

pytestmark = pytest.mark.anyio


async def test_default_gateway() -> None:
    """Test that the default gateway is started and is available on the context."""
    async with Context():
        await start_component(Py4JComponent)
        get_resource_nowait(JavaGateway)


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
    component = Py4JComponent(
        classpath=f"{{asphalt.py4j}}{os.path.sep}javadir{os.path.sep}*"
    )
    assert component.classpath == (
        f"{os.path.dirname(asphalt.py4j.__file__)}{os.path.sep}javadir{os.path.sep}*"
    )
    assert component.classpath.endswith(os.path.join("asphalt", "py4j", "javadir", "*"))


async def test_callback_server() -> None:
    """
    Test that the gateway's callback server works when enabled in the configuration.
    """

    class NumberCallable:
        def call(self) -> int:
            return 7

        class Java:
            implements: ClassVar[list[str]] = ["java.util.concurrent.Callable"]

    async with Context():
        await start_component(Py4JComponent, {"callback_server": True})
        gateway = get_resource_nowait(JavaGateway)
        executor = gateway.jvm.java.util.concurrent.Executors.newFixedThreadPool(1)
        try:
            future = executor.submit(NumberCallable())
            assert future.get() == 7
        finally:
            executor.shutdown()


async def test_gateway_close() -> None:
    """
    Test that shutting down the context does not shut down the Java side gateway if
    launch_jvm was False.

    """
    gateway = JavaGateway.launch_gateway()
    async with Context():
        await start_component(
            Py4JComponent,
            {"gateway": {"port": gateway.gateway_parameters.port}, "launch_jvm": False},
        )
        gateway2 = get_resource_nowait(JavaGateway)
        gateway2.jvm.java.lang.System.setProperty("TEST_VALUE", "abc")

    assert gateway.jvm.java.lang.System.getProperty("TEST_VALUE") == "abc"
    gateway.shutdown()

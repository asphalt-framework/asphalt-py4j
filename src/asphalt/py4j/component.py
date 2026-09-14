from __future__ import annotations

import logging
import os
import re
from collections.abc import AsyncGenerator
from importlib import import_module
from typing import Any, Iterable, cast

from asphalt.core import Component, Context, context_teardown

from py4j.java_gateway import (
    CallbackServerParameters,
    GatewayParameters,
    JavaGateway,
    launch_gateway,
)

logger = logging.getLogger(__name__)
package_re = re.compile(r"\{(.+?)\}")


class Py4JComponent(Component):
    """
    Creates a :class:`~py4j.java_gateway.JavaGateway` resource.

    :param resource_name: name of the Java gateway resource to be published
    :param launch_jvm: ``True`` to spawn a Java Virtual Machine in a subprocess and
        connect to it, ``False`` to connect to an existing Py4J enabled JVM
    :param gateway: either a :class:`~py4j.java_gateway.GatewayParameters` object or
        a dictionary of keyword arguments for it
    :param callback_server: callback server parameters or a boolean indicating if a
        callback server is wanted
    :param javaopts: options passed to Java itself
    :param classpath: path or iterable of paths to pass to the JVM launcher as the
        class path
    """

    def __init__(
        self,
        resource_name: str = "default",
        launch_jvm: bool = True,
        gateway: GatewayParameters | dict[str, Any] | None = None,
        callback_server: CallbackServerParameters | dict[str, Any] | bool = False,
        javaopts: Iterable[str] = (),
        classpath: Iterable[str] = "",
    ):
        self.resource_name = resource_name
        self.launch_jvm = launch_jvm
        classpath = (
            classpath if isinstance(classpath, str) else os.pathsep.join(classpath)
        )
        self.javaopts = list(javaopts)

        # Substitute package names with their absolute directory paths
        self.classpath = (
            classpath if isinstance(classpath, str) else os.pathsep.join(classpath)
        )
        for match in package_re.finditer(classpath):
            pkgname = match.group(1)
            module = import_module(pkgname)
            try:
                module_dir = os.path.dirname(cast(str, module.__file__))
            except AttributeError:
                raise ValueError(
                    f"Cannot determine the file system path of package {pkgname}, as "
                    f"it has no __file__ attribute"
                ) from None

            self.classpath = self.classpath.replace(match.group(0), module_dir)

        if isinstance(gateway, GatewayParameters):
            self.gateway_params = gateway
        else:
            if gateway is None:
                gateway = {}

            gateway.setdefault("eager_load", True)
            gateway.setdefault("auto_convert", True)
            self.gateway_params = GatewayParameters(**gateway)

        if isinstance(callback_server, dict):
            self.callback_server_params = CallbackServerParameters(**callback_server)
        elif callback_server is True:
            self.callback_server_params = CallbackServerParameters()
        else:
            self.callback_server_params = callback_server

    @context_teardown
    async def start(self, ctx: Context) -> AsyncGenerator[None, Exception | None]:
        if self.launch_jvm:
            self.gateway_params.port = launch_gateway(
                classpath=self.classpath, javaopts=self.javaopts
            )

        gateway = JavaGateway(
            gateway_parameters=self.gateway_params,
            callback_server_parameters=self.callback_server_params,
        )
        ctx.add_resource(gateway, self.resource_name)
        logger.info(
            "Configured Py4J gateway (%s; address=%s, port=%d)",
            self.resource_name,
            self.gateway_params.address,
            self.gateway_params.port,
        )

        yield

        if self.launch_jvm:
            gateway.shutdown()
        else:
            gateway.close()

        logger.info("Py4J gateway (%s) shut down", self.resource_name)

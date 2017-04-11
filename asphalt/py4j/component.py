import logging
import os
import re
from importlib import import_module
from typing import Dict, Any, Union, Iterable

from asphalt.core import Component, Context, merge_config, context_teardown
from async_generator import yield_
from py4j.java_gateway import (JavaGateway, launch_gateway, GatewayParameters,
                               CallbackServerParameters)
from typeguard import check_argument_types

logger = logging.getLogger(__name__)
package_re = re.compile(r'\{(.+?)\}')


class Py4JComponent(Component):
    """
    Creates one or more :class:`~py4j.java_gateway.JavaGateway` resources.

    If ``gateways`` is given, a Java gateway resource will be published for each key in the
    dictionary, using the key as the resource name. Any extra keyword arguments to the component
    constructor will be used as defaults for omitted configuration values. The context attribute
    will by default be the same as the resource name, unless explicitly set with the
    ``context_attr`` option.

    If ``gateways`` is omitted, a single gateway resource (``default`` / ``ctx.java``)
    is published using any extra keyword arguments passed to the component.

    :param gateways: a dictionary of resource name ⭢ :meth:`configure_gateway` arguments
    :param default_gateway_args: default values for omitted :meth:`configure_gateway` arguments
    """

    def __init__(self, gateways: Dict[str, Dict[str, Any]] = None, **default_gateway_args):
        assert check_argument_types()
        if not gateways:
            default_gateway_args.setdefault('context_attr', 'java')
            gateways = {'default': default_gateway_args}

        self.gateways = []
        for resource_name, config in gateways.items():
            config = merge_config(default_gateway_args, config)
            context_attr = config.pop('context_attr', resource_name)
            gateway_settings = self.configure_gateway(**config)
            self.gateways.append((resource_name, context_attr) + tuple(gateway_settings))

    @classmethod
    def configure_gateway(
            cls, launch_jvm: bool = True,
            gateway: Union[GatewayParameters, Dict[str, Any]] = None,
            callback_server: Union[CallbackServerParameters, Dict[str, Any]] = False,
            javaopts: Iterable[str] = (), classpath: Iterable[str] = ''):
        """
        Configure a Py4J gateway.

        :param launch_jvm: ``True`` to spawn a Java Virtual Machine in a subprocess and connect to
            it, ``False`` to connect to an existing Py4J enabled JVM
        :param gateway: either a :class:`~py4j.java_gateway.GatewayParameters` object or a
            dictionary of keyword arguments for it
        :param callback_server: callback server parameters or a boolean indicating if a
            callback server is wanted
        :param javaopts: options passed to Java itself
        :param classpath: path or iterable of paths to pass to the JVM launcher as the class path

        """
        assert check_argument_types()
        classpath = classpath if isinstance(classpath, str) else os.pathsep.join(classpath)
        javaopts = list(javaopts)

        # Substitute package names with their absolute directory paths
        for match in package_re.finditer(classpath):
            pkgname = match.group(1)
            module = import_module(pkgname)
            module_dir = os.path.dirname(module.__file__)
            classpath = classpath.replace(match.group(0), module_dir)

        if gateway is None:
            gateway = {}
        if isinstance(gateway, dict):
            gateway.setdefault('eager_load', True)
            gateway.setdefault('auto_convert', True)
            gateway = GatewayParameters(**gateway)

        if isinstance(callback_server, dict):
            callback_server = CallbackServerParameters(**callback_server)
        elif callback_server is True:
            callback_server = CallbackServerParameters()

        return launch_jvm, gateway, callback_server, classpath, javaopts

    @context_teardown
    async def start(self, ctx: Context):
        gateways = []
        for (resource_name, context_attr, launch_jvm, gateway_params, callback_server_params,
             classpath, javaopts) in self.gateways:
            if launch_jvm:
                gateway_params.port = launch_gateway(classpath=classpath, javaopts=javaopts)

            gateway = JavaGateway(gateway_parameters=gateway_params,
                                  callback_server_parameters=callback_server_params)
            gateways.append((resource_name, launch_jvm, gateway))
            ctx.add_resource(gateway, resource_name, context_attr)
            logger.info('Configured Py4J gateway (%s / ctx.%s; address=%s, port=%d)',
                        resource_name, context_attr, gateway_params.address, gateway_params.port)

        await yield_()

        for resource_name, shutdown_jvm, gateway in gateways:
            if shutdown_jvm:
                gateway.shutdown()
            else:
                gateway.close()

            logger.info('Py4J gateway (%s) shut down', resource_name)

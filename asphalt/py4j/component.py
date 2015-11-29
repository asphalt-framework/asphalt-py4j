from asyncio import coroutine
from importlib import import_module
from typing import Dict, Any, Union, Iterable
import logging
import os
import re

from py4j.java_gateway import (JavaGateway, launch_gateway, GatewayParameters,
                               CallbackServerParameters)
from asphalt.core.component import Component
from asphalt.core.context import Context

logger = logging.getLogger(__name__)


class Py4JComponent(Component):
    """
    Provides Py4J integration.

    Publishes one or more :class:`~py4j.java_gateway.JavaGateway`
    objects as resources and context variables.

    :param gateways: a dictionary of JavaGateway resource name ->
        :meth:`create_gateway` keyword arguments
    :param default_gateway_args: :meth:`create_gateway` arguments for
        the default gateway
    """

    package_re = re.compile(r'\{(.+?)\}')

    def __init__(self, gateways: Dict[str, Dict[str, Any]]=None, **default_gateway_args):
        if gateways and default_gateway_args:
            raise ValueError('specify either a "gateways" dictionary or the default gateway\'s '
                             'options directly, but not both')

        if not gateways:
            default_gateway_args.setdefault('context_attr', 'java')
            gateways = {'default': default_gateway_args}

        self.gateways = [self.create_gateway(alias, **kwargs)
                         for alias, kwargs in gateways.items()]

    @classmethod
    def create_gateway(cls, resource_name: str, context_attr: str=None, launch_jvm: bool=True,
                       gateway: Union[GatewayParameters, Dict[str, Any]]=None,
                       callback_server: Union[CallbackServerParameters, Dict[str, Any]]=False,
                       javaopts: Iterable[str]=(), classpath: Iterable[str]=''):
        """
        Configures a Py4J gateway with the given parameters.

        :param resource_name: resource name the mailer will be
            published as
        :param context_attr: the mailer's attribute name on the context
             (defaults to the value of ``resource_name``)
        :param launch_jvm: ``True`` to spawn a Java Virtual Machine in
            a subprocess and connect to it, ``False`` to connect to an
            existing Py4J enabled JVM
        :param gateway: either a
            :class:`~py4j.java_gateway.GatewayParameters` object or a
            dictionary of keyword arguments for it
        :param callback_server: callback server parameters or a boolean
            indicating if a callback server is wanted
        :param javaopts: options passed to Java itself
        :param classpath: path or iterable of paths to pass to the JVM
            launcher as the class path

        """
        context_attr = context_attr or resource_name
        classpath = classpath if isinstance(classpath, str) else os.pathsep.join(classpath)
        javaopts = list(javaopts)

        # Substitute package names with their absolute directory paths
        for match in cls.package_re.finditer(classpath):
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

        return (resource_name, context_attr, launch_jvm, gateway, callback_server, classpath,
                javaopts)

    @coroutine
    def start(self, ctx: Context):
        for (resource_name, context_attr, launch_jvm, gateway_params, callback_server_params,
             classpath, javaopts) in self.gateways:
            if launch_jvm:
                gateway_params.port = launch_gateway(classpath=classpath, javaopts=javaopts)

            gateway = JavaGateway(gateway_parameters=gateway_params,
                                  callback_server_parameters=callback_server_params)
            ctx.add_listener('finished', self.shutdown_gateway,
                             args=[gateway, resource_name, launch_jvm])
            yield from ctx.publish_resource(gateway, resource_name, context_attr)
            logger.info('Configured Py4J gateway (%s / ctx.%s; address=%s, port=%d)',
                        resource_name, context_attr, gateway_params.address, gateway_params.port)

    @staticmethod
    def shutdown_gateway(ctx, gateway: JavaGateway, resource_name: str, shutdown_jvm: bool):
        if shutdown_jvm:
            gateway.shutdown()
        else:
            gateway.close()

        logger.info('Py4J gateway (%s) shut down', resource_name)

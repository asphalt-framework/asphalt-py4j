Configuration
=============

There are two principal ways to use a Java Virtual Machine with Py4J:

#. Launch a new JVM just for the application, in a subprocess
#. Connect to an existing JVM

The first method is what most people will want. The Java Virtual Machine is started along with
the application and is shut down when the application is shut down.

The second method is primarly useful in special scenarios like connecting to a Java EE container.
Shutting down the application has no effect in the Java side gateway then.

The minimal configuration is as follows:

.. code-block:: yaml

    components:
      py4j:

This will publish a resource of type :class:`py4j.java_gateway.JavaGateway`, named ``default``.
It will appear in the context as the ``java`` attribute.


Connecting to an existing JVM
-----------------------------

To connect to an existing Java Virtual Machine, specify the host address and port of the JVM that
has a GatewayServer_ running, you can use a configuration similar to this:

.. code-block:: yaml

    components:
      py4j:
        launch_jvm: false
        host: 10.0.0.1
        port: 25334

This configuration will connect to a JVM listening on ``10.0.0.1``, port 25334.

By default the JavaGateway connects to 127.0.0.1 port 25333, so you can leave out either value if
you want to use the default.

.. _GatewayServer: https://www.py4j.org/_static/javadoc/index.html?py4j/GatewayServer.html


Multiple gateways
-----------------

If you need to configure multiple gateways, you can do so by using the ``gateways`` configuration
option:

.. code-block:: yaml

    components:
      py4j:
        gateways:
          default:
            context_attr: java
          remote:
            launch_jvm: false
            host: 10.0.0.1


This configures two :class:`py4j.gateway.JavaGateway` resources, named ``default`` and  ``remote``.
Their corresponding context attributes are ``java`` and ``remote``.
If you omit the ``context_attr`` option for a gateway, its resource name will be used.


Adding jars to the class path
-----------------------------

When you distribute your application, you often want to include some jar files with your
application. But when configuring the gateway to launch a new JVM, you need to include those jar
files on the class path. The problem is of course that you don't necessarily know the absolute
file system path to your jar files beforehand. The solution is to define a *package relative* class
path in your Py4J configuration. This feature is provided by the Py4J component and not the
upstream library itself.

Suppose your project has a package named ``foo.bar.baz`` and a subdirectory named ``javalib``.
The relative path from your project root to this subdirectory would then be
``foo/bar/baz/javalib``. To properly express this in your class path configuration,

.. code-block:: yaml

    components:
      py4j:
        classpath: "{foo.bar.baz}/javalib/*"

This will add all the jars in the javalib subdirectory to the class path. The ``{foo.bar.baz}``
part is substituted with the computed absolute path to the ``foo.bar.baz`` package directory.

.. note::
  Remember to enclose the path in quotes when specifying the class path in a YAML configuration
  file. Otherwise the parser may mistake it for the beginning of a dictionary definition.

.. code-block:: yaml

    components:
      py4j:
        classpath:
          - "{foo.bar.baz}/javalib/*"
          - "{x.y}/jars/*"

This specifies a class path of multiple elements in an operating system independent manner using a
list. The final class path is computed by joining the elements using the operation system's path
separator character.

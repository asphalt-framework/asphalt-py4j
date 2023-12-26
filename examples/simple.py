"""
A simple example that reads its own source code using Java classes and then prints it on
standard output.
"""

from py4j.java_gateway import JavaGateway

from asphalt.core import CLIApplicationComponent, Context, run_application


class ApplicationComponent(CLIApplicationComponent):
    async def start(self, ctx: Context) -> None:
        self.add_component("py4j")
        await super().start(ctx)

    async def run(self, ctx: Context) -> None:
        javagw = ctx.require_resource(JavaGateway)
        async with ctx.threadpool():
            f = javagw.jvm.java.io.File(__file__)
            buffer = javagw.new_array(javagw.jvm.char, f.length())
            reader = javagw.jvm.java.io.FileReader(f)
            reader.read(buffer)
            reader.close()
            print(javagw.jvm.java.lang.String(buffer))


run_application(ApplicationComponent())

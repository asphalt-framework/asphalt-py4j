"""
A simple example that reads its own source code using Java classes and then prints it on standard
output.
"""

from asphalt.core import CLIApplicationComponent, Context, run_application


class ApplicationComponent(CLIApplicationComponent):
    async def start(self, ctx: Context):
        self.add_component('py4j')
        await super().start(ctx)

    async def run(self, ctx):
        async with ctx.threadpool():
            f = ctx.java.jvm.java.io.File(__file__)
            buffer = ctx.java.new_array(ctx.java.jvm.char, f.length())
            reader = ctx.java.jvm.java.io.FileReader(f)
            reader.read(buffer)
            reader.close()
            print(ctx.java.jvm.java.lang.String(buffer))

run_application(ApplicationComponent())

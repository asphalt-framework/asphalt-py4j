"""
A simple example that reads its own source code using Java classes and then prints it on standard
output.
"""

import asyncio

from asyncio_extras.threads import threadpool
from asphalt.core import ContainerComponent, Context, run_application


class ApplicationComponent(ContainerComponent):
    async def start(self, ctx: Context):
        self.add_component('py4j')
        await super().start(ctx)

        async with threadpool():
            f = ctx.java.jvm.java.io.File(__file__)
            buffer = ctx.java.new_array(ctx.java.jvm.char, f.length())
            reader = ctx.java.jvm.java.io.FileReader(f)
            reader.read(buffer)
            reader.close()
            print(ctx.java.jvm.java.lang.String(buffer))

        asyncio.get_event_loop().stop()

run_application(ApplicationComponent())

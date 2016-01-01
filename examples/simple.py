"""
A simple example that reads its own source code using Java classes and then
prints it on standard output.
"""

from asphalt.core.component import ContainerComponent
from asphalt.core.context import Context
from asphalt.core.runner import run_application
from asphalt.core.concurrency import blocking, stop_event_loop


class SourcePrinterComponent(ContainerComponent):
    @blocking
    def start(self, ctx: Context):
        self.add_component('py4j')
        super().start(ctx)

        f = ctx.java.jvm.java.io.File(__file__)
        buffer = ctx.java.new_array(ctx.java.jvm.char, f.length())
        reader = ctx.java.jvm.java.io.FileReader(f)
        reader.read(buffer)
        reader.close()
        print(ctx.java.jvm.java.lang.String(buffer))
        stop_event_loop()

run_application(SourcePrinterComponent())

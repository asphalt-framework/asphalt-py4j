"""
A simple example that reads its own source code using Java classes and then prints it on
standard output.
"""
import anyio.to_thread
from asphalt.core import CLIApplicationComponent, get_resource_nowait, run_application
from py4j.java_gateway import JavaGateway


class ApplicationComponent(CLIApplicationComponent):
    async def start(self) -> None:
        self.add_component("py4j")
        await super().start()

    async def run(self) -> None:
        def read_file() -> None:
            f = javagw.jvm.java.io.File(__file__)
            buffer = javagw.new_array(javagw.jvm.char, f.length())
            reader = javagw.jvm.java.io.FileReader(f)
            reader.read(buffer)
            reader.close()
            print(javagw.jvm.java.lang.String(buffer))

        javagw = get_resource_nowait(JavaGateway)
        await anyio.to_thread.run_sync(read_file)


run_application(ApplicationComponent())

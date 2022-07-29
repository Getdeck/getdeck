from getdeck.utils import CMDWrapper


class Docker(CMDWrapper):
    base_command = "docker"

    def check_running(self, name) -> bool:
        """Checks whether an image or a specific container is running."""
        arguments = ["ps"]
        process = self._execute(arguments)
        output = process.stdout.read()
        return name in output

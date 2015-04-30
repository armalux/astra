from .. import Component
import shlex
import datetime


class ConsoleComponent(Component):
    def init(self):
        self.commands = {}
        self.commands['hello'] = None
        self.register('astra.teamserver.commands.run', self.on_command)

    def on_command(self, cmd):
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if not len(cmd):
            return

        try:
            parts = shlex.split(cmd, posix=True)
        except ValueError as e:
            return { 'pipe': 'stderr', 'message': str(e), 'timestamp': timestamp }

        if not len(parts):
            return

        if parts[0] not in self.commands:
            return { 'pipe': 'stderr', 'message': 'No such command "{0}"'.format(parts[0]), 'timestamp': timestamp }

        return {'pipe': 'stdout', 'message': 'Running command...', 'timestamp': timestamp }



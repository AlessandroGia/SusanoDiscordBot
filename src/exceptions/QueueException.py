from discord.app_commands import AppCommandError


class OutOfIndexQueue(AppCommandError):
    pass


class AlreadyLoop(AppCommandError):
    pass


class AlreadyLoopAll(AppCommandError):
    pass


class QueueEmpty(AppCommandError):
    pass

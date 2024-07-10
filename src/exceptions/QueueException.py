from discord.app_commands import AppCommandError


class NoTracksInQueueError(AppCommandError):
    pass


class OutOfIndexQueue(AppCommandError):
    pass


class AlreadyLoop(AppCommandError):
    pass


class AlreadyLoopAll(AppCommandError):
    pass
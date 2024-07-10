from discord.app_commands import AppCommandError


class IllegalState(AppCommandError):
    pass


class AlreadyPaused(AppCommandError):
    pass


class AlreadyResumed(AppCommandError):
    pass


# TRACK


class NoCurrentTrack(AppCommandError):
    pass


# QUEUE

class AlreadyLoop(AppCommandError):
    pass


class AlreadyLoopAll(AppCommandError):
    pass


class QueueEmpty(AppCommandError):
    pass
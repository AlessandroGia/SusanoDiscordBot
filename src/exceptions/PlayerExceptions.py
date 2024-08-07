from discord.app_commands import AppCommandError


class IllegalState(AppCommandError):
    pass


class AlreadyPaused(AppCommandError):
    pass


class AlreadyResumed(AppCommandError):
    pass


class TrackNotSeekable(AppCommandError):
    pass


class InvalidSeekTime(AppCommandError):
    pass


# TRACK


class NoCurrentTrack(AppCommandError):
    pass


# QUEUE


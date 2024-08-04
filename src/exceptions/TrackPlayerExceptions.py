from discord.app_commands import AppCommandError


class TrackNotFoundError(AppCommandError):
    pass


class NoCurrentTrackError(AppCommandError):
    pass


class InvalidSpotifyURL(AppCommandError):
    pass


class TrackException(AppCommandError):
    pass

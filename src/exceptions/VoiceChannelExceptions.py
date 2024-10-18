from discord.app_commands import AppCommandError


class UserNotInVoiceChannel(AppCommandError):
    pass


class BotNotInVoiceChannel(AppCommandError):
    pass


class UserNotInSameVoiceChannel(AppCommandError):
    pass


class BotAlreadyInVoiceChannel(AppCommandError):
    pass

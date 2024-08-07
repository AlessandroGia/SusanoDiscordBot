from discord.app_commands import AppCommandError


class Generic(Exception):
    pass


class InvalidFormat(AppCommandError):
    pass
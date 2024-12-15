"""
This module contains the voice channel check functions for the SusanoMusicBot.
"""

from discord import app_commands, utils, Interaction

from src.exceptions.voice_channel_exceptions import (UserNotInVoiceChannel,
    BotAlreadyInVoiceChannel, BotNotInVoiceChannel, UserNotInSameVoiceChannel)


def __channel_connected_to(interaction: Interaction):
    return utils.get(interaction.client.voice_clients, guild=interaction.guild)


def check_voice_channel():
    """
    Check if the user is in a voice channel and if the bot is in the same voice channel.
    :return:
    """
    def predicate(interaction: Interaction) -> bool:

        if not interaction.user.voice:
            raise UserNotInVoiceChannel

        if interaction.command.name == 'join':
            if __channel_connected_to(interaction):
                raise BotAlreadyInVoiceChannel

        else:
            if not __channel_connected_to(interaction):
                raise BotNotInVoiceChannel

            if not interaction.user.voice.channel == __channel_connected_to(interaction).channel:
                raise UserNotInSameVoiceChannel

        return True
    return app_commands.check(predicate)

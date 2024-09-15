import discord
from discord import Interaction
from discord.ext import commands
from typing import Optional

import wavelink

from src.exceptions.PlayerExceptions import IllegalState
from src.utils.embed import EmbedFactory
from src.voice.guild_data.GuildMusicData import GuildMusicData
from src.voice.voice_state.VoicePlayer import VoicePlayer
from src.ui.PlayerUI import PlayerView


class VoiceState:
    def __init__(self, bot: commands.Bot):
        self.__bot: commands.Bot = bot
        self.__guild_state: dict = {}
        self.__embed = EmbedFactory()
        self.__VoicePlayer = VoicePlayer(bot)

    def server_clean_up(self) -> None:
        for guild_id in list(self.__guild_state.keys()):
            if guild_state := self.__get_guild_state(guild_id):
                if not guild_state.player.connected:
                    if guild_state.last_view and not guild_state.last_view.is_finished():
                        guild_state.last_view.stop()
                    self.__del_guild_state(guild_id)


    def __del_guild_state(self, guild_id: int) -> None:
        self.__guild_state.pop(guild_id)

    def __get_guild_state(self, guild_id: int) -> GuildMusicData:
        return self.__guild_state.get(guild_id)

    def __set_guild_state(self, guild_id: int, data: GuildMusicData) -> None:
        self.__guild_state[guild_id] = data

    async def play_and_send_feedback(self, interaction: Interaction, tracks_queue: wavelink.Search, force: bool, volume: int, start: int, end: int, populate: bool) -> None:
        if guild_state := self.__get_guild_state(interaction.guild_id):

            flag = False

            if guild_state.player.current:
                await interaction.response.send_message(
                    embed=self.__embed.added_to_queue(tracks_queue, interaction.user),
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "Caricamento in corso...",
                )
                flag = True

            await self.__VoicePlayer.play(
                guild_state,
                interaction,
                tracks_queue,
                force,
                volume,
                start,
                end,
                populate
            )

            if flag:
                await interaction.delete_original_response()

        else:
            raise IllegalState

    def __check_guild_state(self, guild_id: int) -> Optional[GuildMusicData]:
        if guild_state := self.__get_guild_state(guild_id):
            if guild_state.player.connected:
                return guild_state
        return None

    def get_player(self, guild_id: int) -> wavelink.Player:
        if guild_state := self.__check_guild_state(guild_id):
            return guild_state.player
        else:
            raise IllegalState

    def get_last_view(self, guild_id: int) -> discord.ui.View:
        if guild_state := self.__check_guild_state(guild_id):
            return self.__get_guild_state(guild_id).last_view
        else:
            raise IllegalState

    def set_last_view(self, guild_id: int, view: discord.ui.View):
        self.__get_guild_state(guild_id).last_view = view

    def get_channel_id(self, guild_id: int) -> int:
        if guild_state := self.__check_guild_state(guild_id):
            return self.__get_guild_state(guild_id).channel_id
        else:
            raise IllegalState

    ## ----------------- ##
    ## player UI methods ##
    ## ----------------- ##

    def is_paused(self, guild_id: int) -> bool:
        if guild_state := self.__check_guild_state(guild_id):
            return guild_state.player.paused
        else:
            raise IllegalState

    async def pause(self, interaction: Interaction):
        if guild_state := self.__check_guild_state(interaction.guild_id):
            await self.__VoicePlayer.pause(guild_state)
        else:
            raise IllegalState

    async def resume(self, interaction: Interaction):
        if guild_state := self.__check_guild_state(interaction.guild_id):
            await self.__VoicePlayer.resume(guild_state)
        else:
            raise IllegalState

    async def restart(self, interaction: Interaction) -> bool:
        if guild_state := self.__check_guild_state(interaction.guild_id):
            return await self.__VoicePlayer.restart(guild_state)
        else:
            raise IllegalState

    def get_queue_mode(self, interaction: Interaction) -> wavelink.QueueMode:
        if guild_state := self.__check_guild_state(interaction.guild_id):
            return guild_state.player.queue.mode
        else:
            raise IllegalState

    async def set_queue_mode(self, interaction: Interaction, mode: wavelink.QueueMode) -> None:
        if guild_state := self.__check_guild_state(interaction.guild_id):
            await self.__VoicePlayer.set_queue_mode(guild_state, mode)
        else:
            raise IllegalState

    async def queue(self, interaction: Interaction) -> tuple[str, list[str]]:
        if guild_state := self.__check_guild_state(interaction.guild_id):
            return await self.__VoicePlayer.queue(
                guild_state
            )
        else:
            raise IllegalState

    ## ----------------- ##
    ## ----------------- ##

    async def join(self, interaction: Interaction):
        player: wavelink.Player = await interaction.user.voice.channel.connect(
            self_deaf=True,
            cls=wavelink.Player
        )
        player.inactive_timeout = 180
        self.__set_guild_state(
            interaction.guild_id,
            GuildMusicData(
                interaction.channel_id,
                player
            )
        )

    async def leave(self, interaction: Interaction):
        if guild_state := self.__check_guild_state(interaction.guild_id):
            await self.__VoicePlayer.leave(guild_state)
        else:
            raise IllegalState

    async def play(self, interaction: Interaction, tracks: wavelink.Search, force: bool, volume: int, start: int, end: int, populate: bool) -> None:
        if guild_state := self.__check_guild_state(interaction.guild_id):
            return await self.__VoicePlayer.play(
                guild_state,
                interaction,
                tracks,
                force,
                volume,
                start,
                end,
                populate
            )
        else:
            raise IllegalState

    async def stop(self, interaction: Interaction) -> bool:
        if guild_state := self.__check_guild_state(interaction.guild_id):
            return await self.__VoicePlayer.stop(guild_state)
        else:
            raise IllegalState

    async def volume(self, interaction: Interaction, volume: int) -> None:
        if guild_state := self.__check_guild_state(interaction.guild_id):
            await self.__VoicePlayer.volume(guild_state, volume)
        else:
            raise IllegalState

    async def seek(self, interaction: Interaction, position: int) -> None:
        if guild_state := self.__check_guild_state(interaction.guild_id):
            await self.__VoicePlayer.seek(guild_state, position)
        else:
            raise IllegalState

    async def loop(self, interaction: Interaction) -> bool:
        if guild_state := self.__check_guild_state(interaction.guild_id):
            return await self.__VoicePlayer.loop(guild_state)
        else:
            raise IllegalState

    async def loop_all(self, interaction: Interaction):
        if guild_state := self.__check_guild_state(interaction.guild_id):
            return await self.__VoicePlayer.loop_all(guild_state)
        else:
            raise IllegalState

    async def skip(self, interaction: Interaction, force: bool = True):
        if guild_state := self.__check_guild_state(interaction.guild_id):
            await self.__VoicePlayer.skip(guild_state, force)
        else:
            raise IllegalState

    async def shuffle(self, interaction: Interaction):
        if guild_state := self.__check_guild_state(interaction.guild_id):
            await self.__VoicePlayer.shuffle(guild_state)
        else:
            raise IllegalState

    async def reset(self, interaction: Interaction):
        if guild_state := self.__check_guild_state(interaction.guild_id):
            await self.__VoicePlayer.reset(guild_state)
        else:
            raise IllegalState

    async def remove(self, interaction: Interaction, index: int) -> wavelink.Playable:
        if guild_state := self.__check_guild_state(interaction.guild_id):
            return await self.__VoicePlayer.remove(
                guild_state,
                index
            )
        else:
            raise IllegalState

    async def swap(self, interaction: Interaction, index1: int, index2: int) -> tuple[wavelink.Playable, wavelink.Playable]:
        if guild_state := self.__check_guild_state(interaction.guild_id):
            return await self.__VoicePlayer.swap(
                guild_state,
                index1,
                index2
            )
        else:
            raise IllegalState

    async def play_next(self, guild_id: int):
        if guild_state := self.__check_guild_state(guild_id):
            await self.__VoicePlayer.play_next(guild_state)
        else:
            raise IllegalState

    async def inactive_player(self, guild_id: int):
        if guild_state := self.__check_guild_state(guild_id):
            await self.__VoicePlayer.inactive_player(guild_state)
            #self.__del_guild_state(guild_id)
        else:
            raise IllegalState


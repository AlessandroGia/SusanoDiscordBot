import discord
from discord import Interaction
from discord.ext import commands
from typing import Optional

import wavelink

from src.exceptions.PlayerExceptions import IllegalState
from src.utils.embed import EmbedFactory
from src.voice.guild_data.GuildMusicData import GuildMusicData
from src.voice.voice_state.VoicePlayer import VoicePlayer


class VoiceState:
    def __init__(self, bot: commands.Bot):
        self.__bot: commands.Bot = bot
        self.__guild_state: dict = {}
        self.__embed = EmbedFactory()
        self.__VoicePlayer = VoicePlayer(bot)

    def __del_guild_state(self, guild_id: int) -> None:
        self.__guild_state.pop(guild_id)

    def __get_guild_state(self, guild_id: int) -> GuildMusicData:
        return self.__guild_state.get(guild_id)

    def __set_guild_state(self, guild_id: int, data: GuildMusicData) -> None:
        self.__guild_state[guild_id] = data

    async def feedback_play_command(self, interaction: Interaction, track_playing: Optional[wavelink.Playable], tracks_queue: Optional[wavelink.Search]) -> None:
        if guild_state := self.__get_guild_state(interaction.guild_id):
            if track_playing:
                if tracks_queue:
                    await interaction.response.send_message(
                        embed=self.__embed.now_playing_and_added_to_queue_with_player(
                            tracks_queue,
                            guild_state.player
                        )
                    )
                else:
                    await interaction.response.send_message(
                        embed=self.__embed.now_playing_with_player(
                            guild_state.player
                        )
                    )

                self.set_last_message(
                    guild_state.player.guild.id,
                    interaction
                )
            else:
                await interaction.response.send_message(
                    embed=self.__embed.added_to_queue(
                        tracks_queue,
                        interaction.user
                    ),
                )
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

    def set_last_message(self, guild_id: int, message: discord.Message | Interaction):
        self.__get_guild_state(guild_id).last_message = message

    def get_channel_id(self, guild_id: int) -> int:
        if guild_state := self.__check_guild_state(guild_id):
            return self.__get_guild_state(guild_id).channel_id
        else:
            raise IllegalState

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
            self.__del_guild_state(interaction.guild_id)
        else:
            raise IllegalState

    async def play(self, interaction: Interaction, tracks: wavelink.Search, force: bool, volume: int, start: int, end: int, populate: bool) -> tuple[Optional[wavelink.Playable], wavelink.Search]:
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

    async def skip(self, interaction: Interaction):
        if guild_state := self.__check_guild_state(interaction.guild_id):
            await self.__VoicePlayer.skip(guild_state)
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
            await self.__VoicePlayer.remove(
                guild_state,
                index
            )
        else:
            raise IllegalState

    async def swap(self, interaction: Interaction, index1: int, index2: int) -> tuple[wavelink.Playable, wavelink.Playable]:
        if guild_state := self.__check_guild_state(interaction.guild_id):
            await self.__VoicePlayer.swap(
                guild_state,
                index1,
                index2
            )
        else:
            raise IllegalState

    async def queue(self, interaction: Interaction) -> tuple[str, list[str]]:
        if guild_state := self.__check_guild_state(interaction.guild_id):
            return await self.__VoicePlayer.queue(
                guild_state
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
            self.__del_guild_state(guild_id)
        else:
            raise IllegalState

    async def clear_now_playing(self, guild_id: int):
        if guild_state := self.__check_guild_state(guild_id):
            try:
                await self.__VoicePlayer.clear_now_playing(guild_state)
            except Exception as e:
                print("Error in clear_now_playing: ", e)
        else:
            raise IllegalState

    async def update_now_playing(self, guild_id: int):
        if guild_state := self.__check_guild_state(guild_id):
            await self.__VoicePlayer.update_now_playing(guild_state)
        else:
            raise IllegalState

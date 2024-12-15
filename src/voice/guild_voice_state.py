from typing import Optional

import discord
from discord import Interaction

import wavelink

from src.exceptions.player_exceptions import IllegalState
from src.exceptions.QueueException import QueueEmpty
from src.utils.embed import EmbedFactory
from src.voice.guild_data.guild_data import GuildMusicData
from src.voice.voice_state.voice_player import VoicePlayer

class GuildVoiceState:
    def __init__(self):
        self.__guild_state: dict = {}
        self.__embed = EmbedFactory()

    async def guild_clean_up(self, guild_id):
        if guild_state := self.__get_guild_state(guild_id):
            if guild_state.last_view and not guild_state.last_view.is_finished():
                if guild_state.last_mess:
                    await guild_state.last_mess.edit(view=None)
                guild_state.last_view.stop()
            self.__del_guild_state(guild_id)


    def __del_guild_state(self, guild_id: int) -> None:
        self.__guild_state.pop(guild_id)

    def __get_guild_state(self, guild_id: int) -> GuildMusicData:
        return self.__guild_state.get(guild_id)

    def __set_guild_state(self, guild_id: int, data: GuildMusicData) -> None:
        self.__guild_state[guild_id] = data

    def __ensure_guild_state(self, guild_id: int) -> GuildMusicData:
        guild_state = self.__get_guild_state(guild_id)

        if not guild_state or not guild_state.voice_player.is_connected():
            raise IllegalState

        return guild_state

    async def play_and_send_feedback(self, interaction: Interaction, tracks: wavelink.Search) -> None:
        guild_state = self.__ensure_guild_state(interaction.guild_id)
        current = guild_state.voice_player.get_current_track()

        if current:
            await interaction.response.send_message(
                embed=self.__embed.added_to_queue(tracks, interaction.user),
                ephemeral=True
            )
        else:
            if len(tracks) > 1:
                await interaction.response.send_message(
                    embed=self.__embed.added_to_queue(tracks, interaction.user, True),
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "Caricamento in corso...",
                )

        await self.__play(
            interaction,
            guild_state,
            tracks,
        )

        if not current and len(tracks) <= 1:
            await interaction.delete_original_response()


    def get_last_view(self, guild_id: int) -> discord.ui.View:
        guild_state = self.__ensure_guild_state(guild_id)

        return guild_state.last_view

    def get_last_mess(self, guild_id: int) -> discord.Message:
        guild_state = self.__ensure_guild_state(guild_id)

        return guild_state.last_mess

    def set_last_view(self, guild_id: int, view: discord.ui.View) -> None:
        self.__get_guild_state(guild_id).last_view = view

    def set_last_mess(self, guild_id: int, mess: discord.Message) -> None:
        self.__get_guild_state(guild_id).last_mess = mess

    def get_channel_id(self, guild_id: int) -> int:
        guild_state = self.__ensure_guild_state(guild_id)

        return guild_state.channel_id


    ## ----------------- ##
    ## player UI methods ##
    ## ----------------- ##

    def get_current_track(self, guild_id: int) -> Optional[wavelink.Playable]:
        guild_state = self.__ensure_guild_state(guild_id)

        return guild_state.voice_player.get_current_track()

    def is_paused(self, guild_id: int) -> bool:
        guild_state = self.__ensure_guild_state(guild_id)

        return guild_state.voice_player.is_paused()

    async def restart(self, interaction: Interaction) -> None:
        guild_state = self.__ensure_guild_state(interaction.guild_id)

        await guild_state.voice_player.restart()

    async def toggle_pause(self, interaction: Interaction) -> bool:
        guild_state = self.__ensure_guild_state(interaction.guild_id)

        is_paused: bool = guild_state.voice_player.is_paused()
        await guild_state.voice_player.pause() if not is_paused else await guild_state.voice_player.resume()

        return not is_paused

    def toggle_loop(self, interaction: Interaction) -> wavelink.QueueMode:
        guild_state = self.__ensure_guild_state(interaction.guild_id)
        queue_mode = guild_state.voice_player.get_queue_mode()

        if queue_mode == wavelink.QueueMode.normal:
            guild_state.voice_player.set_queue_mode(wavelink.QueueMode.loop_all)
            return wavelink.QueueMode.loop_all
        if queue_mode == wavelink.QueueMode.loop_all:
            guild_state.voice_player.set_queue_mode(wavelink.QueueMode.loop)
            return wavelink.QueueMode.loop
        else:
            guild_state.voice_player.set_queue_mode(wavelink.QueueMode.normal)
            return wavelink.QueueMode.normal

    def get_queue_mode(self, guild_id: int) -> wavelink.QueueMode:
        guild_state = self.__ensure_guild_state(guild_id)

        return guild_state.voice_player.get_queue_mode()

    def auto_queue(self, interaction: Interaction) -> wavelink.Queue:
        guild_state = self.__ensure_guild_state(interaction.guild_id)

        return guild_state.voice_player.auto_queue()

    def queue(self, interaction: Interaction) -> wavelink.Queue:
        guild_state = self.__ensure_guild_state(interaction.guild_id)

        return guild_state.voice_player.queue()

    def queues(self, interaction: Interaction) -> wavelink.Queue:
        guild_state = self.__ensure_guild_state(interaction.guild_id)
        queue: wavelink.Queue = guild_state.voice_player.queue().copy()
        auto_queue: wavelink.Queue = guild_state.voice_player.auto_queue()

        queue.put(list(auto_queue)) #PROVARE
        if queue.is_empty:
            raise QueueEmpty

        return queue

    async def play_previous(self, interaction: Interaction) -> None:
        guild_state = self.__ensure_guild_state(interaction.guild_id)

        vc_player = guild_state.voice_player

        if not vc_player.get_current_track().recommended:
            vc_player.put_in_front_at_queue(vc_player.get_from_queue_history(-1))
        previous_track = vc_player.get_from_queue_history(-1)

        queue_mode = vc_player.get_queue_mode()
        if queue_mode == wavelink.QueueMode.loop:
            vc_player.set_queue_mode(wavelink.QueueMode.loop_all)

        await vc_player.play_previous(previous_track)

    async def skip(self, interaction: Interaction, force: bool = True) -> None:
        guild_state = self.__ensure_guild_state(interaction.guild_id)

        queue_mode = guild_state.voice_player.get_queue_mode()
        if queue_mode == wavelink.QueueMode.loop:
            guild_state.voice_player.set_queue_mode(wavelink.QueueMode.loop_all)
        force = False if queue_mode == wavelink.QueueMode.loop_all else force
        await guild_state.voice_player.skip(force)

    async def reset(self, interaction: Interaction) -> None:
        guild_state = self.__ensure_guild_state(interaction.guild_id)

        if guild_state.voice_player.get_queue_mode() != wavelink.QueueMode.normal:
            guild_state.voice_player.set_queue_mode(wavelink.QueueMode.normal)
        if guild_state.auto_queue and guild_state.voice_player.get_auto_play_mode() != wavelink.AutoPlayMode.partial:
            guild_state.voice_player.set_auto_play_mode(wavelink.AutoPlayMode.partial)
            print(guild_state.voice_player.get_auto_play_mode())

        await guild_state.voice_player.reset()

    ## ----------------- ##
    ## ----------------- ##

    async def join(self, interaction: Interaction, inactive_time: int = 180, auto_queue: bool = False) -> None:
        player: wavelink.Player = await interaction.user.voice.channel.connect(
            self_deaf=True,
            cls=wavelink.Player,
        )
        player.inactive_timeout = inactive_time
        player.autoplay = wavelink.AutoPlayMode.partial if auto_queue else wavelink.AutoPlayMode.partial

        self.__set_guild_state(
            interaction.guild_id,
            GuildMusicData(
                interaction.channel_id,
                VoicePlayer(player),
                auto_queue
            )
        )

    async def leave(self, interaction: Interaction) -> None:
        guild_state = self.__ensure_guild_state(interaction.guild_id)
        await self.guild_clean_up(interaction.guild_id)
        await guild_state.voice_player.leave()

    def switch_auto_play_mode(self, interaction: Interaction) -> None:
        guild_state = self.__ensure_guild_state(interaction.guild_id)

        if guild_state.auto_queue and guild_state.voice_player.get_auto_play_mode() == wavelink.AutoPlayMode.partial:
            guild_state.voice_player.set_auto_play_mode(wavelink.AutoPlayMode.enabled)

    def position(self, interaction: Interaction) -> int:
        guild_state = self.__ensure_guild_state(interaction.guild_id)

        return guild_state.voice_player.position()

    def queue_history(self, interaction: Interaction) -> wavelink.Queue:
        guild_state = self.__ensure_guild_state(interaction.guild_id)

        return guild_state.voice_player.queue_history()

    async def play_next(self, guild_id: int) -> None:
        guild_state = self.__ensure_guild_state(guild_id)

        await guild_state.voice_player.play_next()

    async def inactive_player(self, guild_id: int) -> None:
        guild_state = self.__ensure_guild_state(guild_id)

        await guild_state.voice_player.inactive_player()
        # self.__del_guild_state(guild_id)

    @staticmethod
    async def __play(interaction: Interaction, guild_state: GuildMusicData, tracks: wavelink.Search) -> None:
        for track in tracks:
            track.extras = {
                'requester_name': interaction.user.display_name,
                'requester_avatar': interaction.user.display_avatar.url
            }
        guild_state.voice_player.put_in_queue(tracks)

        if not guild_state.voice_player.get_current_track():
            await guild_state.voice_player.play_next()

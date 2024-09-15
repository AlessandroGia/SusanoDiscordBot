import discord
from discord import Interaction
from typing import Optional

import wavelink

from src.exceptions.PlayerExceptions import IllegalState
from src.utils.embed import EmbedFactory
from src.voice.guild_data.GuildMusicData import GuildMusicData
from src.voice.voice_state.VoicePlayer import VoicePlayer

class VoiceState:
    def __init__(self):
        self.__guild_state: dict = {}
        self.__embed = EmbedFactory()

    def server_clean_up(self) -> None:
        for guild_id in list(self.__guild_state.keys()):
            if guild_state := self.__get_guild_state(guild_id):
                if not guild_state.voice_player.is_connected():
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
        if not (guild_state := self.__get_guild_state(interaction.guild_id)):
            raise IllegalState

        current = guild_state.voice_player.get_current_track()

        if current:
            print('a')
            await interaction.response.send_message(
                embed=self.__embed.added_to_queue(tracks_queue, interaction.user),
                ephemeral=True
            )
        else:
            print('c')
            await interaction.response.send_message(
                "Caricamento in corso...",
            )

        await self.__play(
            interaction,
            guild_state,
            tracks_queue,
            force,
            volume,
            start,
            end,
            populate
        )

        if not current:
            await interaction.delete_original_response()


    def __check_guild_state(self, guild_id: int) -> Optional[GuildMusicData]:
        if guild_state := self.__get_guild_state(guild_id):
            if guild_state.voice_player.is_connected():
                return guild_state
        return None

    def get_player(self, guild_id: int) -> wavelink.Player:
        if not (guild_state := self.__check_guild_state(guild_id)):
            raise IllegalState

        return guild_state.voice_player.get_player()


    def get_last_view(self, guild_id: int) -> discord.ui.View:
        if not (guild_state := self.__check_guild_state(guild_id)):
            raise IllegalState

        return guild_state.last_view

    def set_last_view(self, guild_id: int, view: discord.ui.View) -> None:
        self.__get_guild_state(guild_id).last_view = view

    def get_channel_id(self, guild_id: int) -> int:
        if not (guild_state := self.__check_guild_state(guild_id)):
            raise IllegalState

        return guild_state.channel_id


    ## ----------------- ##
    ## player UI methods ##
    ## ----------------- ##

    def is_paused(self, guild_id: int) -> bool:
        if not (guild_state := self.__check_guild_state(guild_id)):
            raise IllegalState

        return guild_state.voice_player.is_paused()

    async def pause(self, interaction: Interaction) -> None:
        if not (guild_state := self.__check_guild_state(interaction.guild_id)):
            raise IllegalState

        await guild_state.voice_player.pause()

    async def resume(self, interaction: Interaction) -> None:
        if not (guild_state := self.__check_guild_state(interaction.guild_id)):
            raise IllegalState

        await guild_state.voice_player.resume()

    async def restart(self, interaction: Interaction) -> bool:
        if not (guild_state := self.__check_guild_state(interaction.guild_id)):
            raise IllegalState

        return await guild_state.voice_player.restart()

    async def toggle_pause(self, interaction: Interaction) -> bool:
        if not (guild_state := self.__check_guild_state(interaction.guild_id)):
            raise IllegalState

        if guild_state.voice_player.is_paused():
            await guild_state.voice_player.resume()
            return False
        else:
            await guild_state.voice_player.pause()
            return True

    def toggle_loop(self, interaction: Interaction) -> wavelink.QueueMode:
        if not (guild_state := self.__check_guild_state(interaction.guild_id)):
            raise IllegalState

        queue_mode = guild_state.voice_player.get_queue_mode()

        if queue_mode == wavelink.QueueMode.normal:
            guild_state.voice_player.set_queue_mode(wavelink.QueueMode.loop_all)
            return wavelink.QueueMode.loop_all
        elif queue_mode == wavelink.QueueMode.loop_all:
            guild_state.voice_player.set_queue_mode(wavelink.QueueMode.loop)
            return wavelink.QueueMode.loop
        else:
            guild_state.voice_player.set_queue_mode(wavelink.QueueMode.normal)
            return wavelink.QueueMode.normal


    def get_queue_mode(self, interaction: Interaction) -> wavelink.QueueMode:
        if not (guild_state := self.__check_guild_state(interaction.guild_id)):
            raise IllegalState

        return guild_state.voice_player.get_queue_mode()

    def set_queue_mode(self, interaction: Interaction, mode: wavelink.QueueMode) -> None:
        if not (guild_state := self.__check_guild_state(interaction.guild_id)):
            raise IllegalState

        guild_state.voice_player.set_queue_mode(mode)


    async def queue(self, interaction: Interaction) -> tuple[str, list[str]]:
        if not (guild_state := self.__check_guild_state(interaction.guild_id)):
            raise IllegalState

        queue: wavelink.Queue = await guild_state.voice_player.queue()
        queues, current = [], []
        for i, song in enumerate(queue, start=1):
            queue_str = f"{i}. [{song.title}]({song.uri})\n"
            if sum(len(s) for s in current) + len(queue_str) > 4090:
                queues.append("".join(current))
                current = []
            current.append(queue_str)
        if current:
            queues.append("".join(current))
        return queues[0], queues[1:]


    ## ----------------- ##
    ## ----------------- ##

    async def join(self, interaction: Interaction) -> None:
        player: wavelink.Player = await interaction.user.voice.channel.connect(
            self_deaf=True,
            cls=wavelink.Player
        )
        player.inactive_timeout = 180
        self.__set_guild_state(
            interaction.guild_id,
            GuildMusicData(
                interaction.channel_id,
                VoicePlayer(player)
            )
        )

    async def leave(self, interaction: Interaction) -> None:
        if not (guild_state := self.__check_guild_state(interaction.guild_id)):
            raise IllegalState

        await guild_state.voice_player.leave()

    async def play(self, interaction: Interaction, tracks: wavelink.Search, force: bool, volume: int, start: int, end: int, populate: bool) -> None:
        if not (guild_state := self.__check_guild_state(interaction.guild_id)):
            raise IllegalState

        await self.__play(
            interaction,
            guild_state,
            tracks,
            force,
            volume,
            start,
            end,
            populate
        )

    async def stop(self, interaction: Interaction) -> bool:
        if not (guild_state := self.__check_guild_state(interaction.guild_id)):
            raise IllegalState

        return await guild_state.voice_player.stop()

    async def volume(self, interaction: Interaction, volume: int) -> None:
        if not (guild_state := self.__check_guild_state(interaction.guild_id)):
            raise IllegalState

        await guild_state.voice_player.volume(volume)

    async def seek(self, interaction: Interaction, position: int) -> None:
        if not (guild_state := self.__check_guild_state(interaction.guild_id)):
            raise IllegalState

        await guild_state.voice_player.seek(position)


    async def skip(self, interaction: Interaction, force: bool = True) -> None:
        if not (guild_state := self.__check_guild_state(interaction.guild_id)):
            raise IllegalState

        queue_mode = guild_state.voice_player.get_queue_mode()
        if queue_mode == wavelink.QueueMode.loop:
            guild_state.voice_player.set_queue_mode(wavelink.QueueMode.loop_all)
        force = False if queue_mode == wavelink.QueueMode.loop_all else force
        await guild_state.voice_player.skip(force)

    async def shuffle(self, interaction: Interaction) -> None:
        if not (guild_state := self.__check_guild_state(interaction.guild_id)):
            raise IllegalState

        await guild_state.voice_player.shuffle()

    async def reset(self, interaction: Interaction) -> None:
        if not (guild_state := self.__check_guild_state(interaction.guild_id)):
            raise IllegalState

        await guild_state.voice_player.reset()

    async def remove(self, interaction: Interaction, index: int) -> wavelink.Playable:
        if not (guild_state := self.__check_guild_state(interaction.guild_id)):
            raise IllegalState

        return await guild_state.voice_player.remove(index)

    async def swap(self, interaction: Interaction, index1: int, index2: int) -> tuple[wavelink.Playable, wavelink.Playable]:
        if not (guild_state := self.__check_guild_state(interaction.guild_id)):
            raise IllegalState

        return await guild_state.voice_player.swap(index1, index2)

    async def play_next(self, guild_id: int) -> None:
        if not (guild_state := self.__check_guild_state(guild_id)):
            raise IllegalState

        await guild_state.voice_player.play_next()

    async def inactive_player(self, guild_id: int) -> None:
        if not (guild_state := self.__check_guild_state(guild_id)):
            raise IllegalState

        await guild_state.voice_player.inactive_player()
        # self.__del_guild_state(guild_id)


    @staticmethod
    async def __play(interaction: Interaction, guild_state: GuildMusicData, tracks: wavelink.Search, force: bool, volume: int, start: int, end: int, populate: bool) -> None:
        requester = {
            'requester_name': interaction.user.display_name,
            'requester_avatar': interaction.user.display_avatar.url
        }
        for track in tracks:
            track.extras = requester
        if len(tracks) == 1:
            track = tracks[0]
            track.extras = {
                'requester_name': interaction.user.display_name,
                'requester_avatar': interaction.user.display_avatar.url,
                'volume': volume,
                'start': start,
                'end': end,
                'populate': populate
            }
            if force:
                guild_state.voice_player.put_in_queue_at(0, track)
            else:
                guild_state.voice_player.put_in_queue(track)
        if guild_state.voice_player.get_current_track():
            await guild_state.voice_player.play()



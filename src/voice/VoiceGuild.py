import discord
from discord import Interaction
from typing import Optional

import wavelink
from wavelink import Playlist

from src.exceptions.PlayerExceptions import IllegalState
from src.exceptions.QueueException import QueueEmpty
from src.utils.embed import EmbedFactory
from src.voice.guild_data.GuildMusicData import GuildMusicData
from src.voice.voice_state.VoicePlayer import VoicePlayer

class VoiceState:
    def __init__(self):
        self.__guild_state: dict = {}
        self.__embed = EmbedFactory()

    def server_clean_up(self) -> None:
        for guild_id in self.__guild_state.keys():
            if (guild_state := self.__get_guild_state(guild_id)) and not guild_state.voice_player.is_connected():
                if guild_state.last_view and not guild_state.last_view.is_finished():
                    if guild_state.last_mess:
                        guild_state.last_mess.edit(view=None)
                    guild_state.last_view.stop()

                self.__del_guild_state(guild_id)

    def __del_guild_state(self, guild_id: int) -> None:
        self.__guild_state.pop(guild_id)

    def __get_guild_state(self, guild_id: int) -> GuildMusicData:
        return self.__guild_state.get(guild_id)

    def __set_guild_state(self, guild_id: int, data: GuildMusicData) -> None:
        self.__guild_state[guild_id] = data

    async def play_and_send_feedback(self, interaction: Interaction, tracks: wavelink.Search) -> None:
        if not (guild_state := self.__get_guild_state(interaction.guild_id)):
            raise IllegalState

        current = guild_state.voice_player.get_current_track()
        _type = type(tracks)
        print(_type)
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

    def get_last_mess(self, guild_id: int) -> discord.Message:
        if not (guild_state := self.__check_guild_state(guild_id)):
            raise IllegalState

        return guild_state.last_mess

    def set_last_view(self, guild_id: int, view: discord.ui.View) -> None:
        self.__get_guild_state(guild_id).last_view = view

    def set_last_mess(self, guild_id: int, mess: discord.Message) -> None:
        self.__get_guild_state(guild_id).last_mess = mess

    def get_channel_id(self, guild_id: int) -> int:
        if not (guild_state := self.__check_guild_state(guild_id)):
            raise IllegalState

        return guild_state.channel_id


    ## ----------------- ##
    ## player UI methods ##
    ## ----------------- ##

    def get_current_track(self, guild_id: int) -> Optional[wavelink.Playable]:
        if not (guild_state := self.__check_guild_state(guild_id)):
            raise IllegalState

        return guild_state.voice_player.get_current_track()

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

    async def restart(self, interaction: Interaction) -> None:
        if not (guild_state := self.__check_guild_state(interaction.guild_id)):
            raise IllegalState

        await guild_state.voice_player.restart()

    async def toggle_pause(self, interaction: Interaction) -> bool:
        if not (guild_state := self.__check_guild_state(interaction.guild_id)):
            raise IllegalState

        is_paused: bool = guild_state.voice_player.is_paused()
        await guild_state.voice_player.pause() if not is_paused else await guild_state.voice_player.resume()
        return not is_paused

    def toggle_shuffle(self, interaction: Interaction) -> bool:
        if not (guild_state := self.__check_guild_state(interaction.guild_id)):
            raise IllegalState

        is_shuffled: bool = guild_state.voice_player.is_shuffled()
        guild_state.voice_player.shuffle() if not is_shuffled else guild_state.voice_player.un_shuffle()
        return not is_shuffled
        # TRUE = shuffle, FALSE = un_shuffle

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

    def get_queue_mode(self, guild_id: int) -> wavelink.QueueMode:
        if not (guild_state := self.__check_guild_state(guild_id)):
            raise IllegalState

        return guild_state.voice_player.get_queue_mode()

    def auto_queue(self, interaction: Interaction) -> wavelink.Queue:
        if not (guild_state := self.__check_guild_state(interaction.guild_id)):
            raise IllegalState

        return guild_state.voice_player.auto_queue()

    def queue(self, interaction: Interaction) -> wavelink.Queue:
        if not (guild_state := self.__check_guild_state(interaction.guild_id)):
            raise IllegalState

        return guild_state.voice_player.queue()

    def queues(self, interaction: Interaction) -> wavelink.Queue:
        if not (guild_state := self.__check_guild_state(interaction.guild_id)):
            raise IllegalState

        queue: wavelink.Queue = guild_state.voice_player.queue().copy()
        auto_queue: wavelink.Queue = guild_state.voice_player.auto_queue()
        queue.put([track for track in auto_queue])

        if queue.is_empty:
            raise QueueEmpty

        return queue


    ## ----------------- ##
    ## ----------------- ##

    async def join(self, interaction: Interaction, inactive_time: int = 180) -> None:
        player: wavelink.Player = await interaction.user.voice.channel.connect(
            self_deaf=True,
            cls=wavelink.Player,
        )
        player.inactive_timeout = inactive_time
        player.autoplay = wavelink.AutoPlayMode.enabled
        self.__set_guild_state(
            interaction.guild_id,
            GuildMusicData(
                interaction.channel_id,
                VoicePlayer(player)
            )
        )

    def switch_auto_play_mode(self, interaction: Interaction) -> None:
        if not (guild_state := self.__check_guild_state(interaction.guild_id)):
            raise IllegalState

        if guild_state.voice_player.get_auto_play_mode() == wavelink.AutoPlayMode.partial:
            guild_state.voice_player.set_auto_play_mode(wavelink.AutoPlayMode.enabled)

    async def leave(self, interaction: Interaction) -> None:
        if not (guild_state := self.__check_guild_state(interaction.guild_id)):
            raise IllegalState

        await guild_state.voice_player.leave()

    async def reset(self, interaction: Interaction) -> None:
        if not (guild_state := self.__check_guild_state(interaction.guild_id)):
            raise IllegalState
        if guild_state.voice_player.get_queue_mode() != wavelink.QueueMode.normal:
            guild_state.voice_player.set_queue_mode(wavelink.QueueMode.normal)
        if guild_state.voice_player.get_auto_play_mode() != wavelink.AutoPlayMode.partial:
            guild_state.voice_player.set_auto_play_mode(wavelink.AutoPlayMode.partial)
            print(guild_state.voice_player.get_auto_play_mode())

        await guild_state.voice_player.reset()

    async def volume(self, interaction: Interaction, volume: int) -> None:
        if not (guild_state := self.__check_guild_state(interaction.guild_id)):
            raise IllegalState

        await guild_state.voice_player.volume(volume)

    async def seek(self, interaction: Interaction, position: int) -> None:
        if not (guild_state := self.__check_guild_state(interaction.guild_id)):
            raise IllegalState

        await guild_state.voice_player.seek(position)

    def position(self, interaction: Interaction) -> int:
        if not (guild_state := self.__check_guild_state(interaction.guild_id)):
            raise IllegalState

        return guild_state.voice_player.position()

    def queue_history(self, interaction: Interaction) -> wavelink.Queue:
        if not (guild_state := self.__check_guild_state(interaction.guild_id)):
            raise IllegalState

        return guild_state.voice_player.queue_history()

    async def play_previous(self, interaction: Interaction) -> None:
        if not (guild_state := self.__check_guild_state(interaction.guild_id)):
            raise IllegalState

        vc_player = guild_state.voice_player

        if not vc_player.get_current_track().recommended:
            vc_player.put_in_front_at_queue(vc_player.get_from_queue_history(-1))
        previous_track = vc_player.get_from_queue_history(-1)

        queue_mode = vc_player.get_queue_mode()
        if queue_mode == wavelink.QueueMode.loop:
            vc_player.set_queue_mode(wavelink.QueueMode.loop_all)

        await vc_player.play_previous(previous_track)

    async def skip(self, interaction: Interaction, force: bool = True) -> None:
        if not (guild_state := self.__check_guild_state(interaction.guild_id)):
            raise IllegalState

        queue_mode = guild_state.voice_player.get_queue_mode()
        if queue_mode == wavelink.QueueMode.loop:
            guild_state.voice_player.set_queue_mode(wavelink.QueueMode.loop_all)
        force = False if queue_mode == wavelink.QueueMode.loop_all else force
        await guild_state.voice_player.skip(force)

    def is_shuffled(self, guild_id: int) -> bool:
        if not (guild_state := self.__check_guild_state(guild_id)):
            raise IllegalState

        return guild_state.voice_player.is_shuffled()

    def remove(self, interaction: Interaction, index: int) -> wavelink.Playable:
        if not (guild_state := self.__check_guild_state(interaction.guild_id)):
            raise IllegalState

        return guild_state.voice_player.remove(index)

    def swap(self, interaction: Interaction, index1: int, index2: int) -> tuple[wavelink.Playable, wavelink.Playable]:
        if not (guild_state := self.__check_guild_state(interaction.guild_id)):
            raise IllegalState

        return guild_state.voice_player.swap(index1, index2)

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
    async def __play(interaction: Interaction, guild_state: GuildMusicData, tracks: wavelink.Search) -> None:
        for track in tracks:
            track.extras = {
                'requester_name': interaction.user.display_name,
                'requester_avatar': interaction.user.display_avatar.url
            }
        guild_state.voice_player.put_in_queue(tracks)

        if not guild_state.voice_player.get_current_track():
            await guild_state.voice_player.play_next()

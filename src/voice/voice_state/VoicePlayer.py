from typing import Optional

import discord
import wavelink
from discord import Interaction
from discord.ext import commands

from src.utils.embed import EmbedFactory
from src.voice.guild_data.GuildMusicData import GuildMusicData

from src.exceptions.PlayerExceptions import AlreadyPaused, AlreadyResumed, NoCurrentTrack, TrackNotSeekable, InvalidSeekTime
from src.exceptions.QueueException import AlreadyLoop, AlreadyLoopAll, QueueEmpty


class VoicePlayer:
    def __init__(self, bot: commands.Bot):
        self.__bot: commands.Bot = bot
        self.__embed = EmbedFactory()

    @staticmethod
    async def leave(guild_state: GuildMusicData):
        await guild_state.player.disconnect(force=True)


    async def play(self, guild_state: GuildMusicData, interaction: Interaction, tracks: wavelink.Search, force: bool, volume: int, start: int, end: int, populate: bool) -> None:
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
                guild_state.player.queue.put_at(0, track)
            else:
                guild_state.player.queue.put(track)

        else:
            guild_state.player.queue.put(tracks)

        if not guild_state.player.current:
            await self.play_next(guild_state)


    @staticmethod
    async def skip(guild_state: GuildMusicData, force: bool):
        if not await guild_state.player.stop(force=force):
            raise NoCurrentTrack

    @staticmethod
    async def pause(guild_state: GuildMusicData):

        if not guild_state.player.current:
            raise NoCurrentTrack

        if guild_state.player.paused:
            raise AlreadyPaused

        await guild_state.player.pause(True)

    @staticmethod
    async def resume(guild_state: GuildMusicData):

        if not guild_state.player.current:
            raise NoCurrentTrack

        if not guild_state.player.paused:
            raise AlreadyResumed

        await guild_state.player.pause(False)

    @staticmethod
    async def stop(guild_state: GuildMusicData) -> bool:
        player: wavelink.Player = guild_state.player

        if not player.current:
            raise NoCurrentTrack

        if flag := not player.queue.is_empty:
            player.queue.clear()

        await player.skip()

        return flag

    @staticmethod
    async def volume(guild_state: GuildMusicData, volume: int):
        if volume < 0 or volume > 1000:
            raise ValueError

        await guild_state.player.set_volume(volume)

    @staticmethod
    async def seek(guild_state: GuildMusicData, position: int):
        player: wavelink.Player = guild_state.player

        if not player.current:
            raise NoCurrentTrack

        if not player.current.is_seekable:
            raise TrackNotSeekable

        if position < 0 or position >= player.current.length:
            raise InvalidSeekTime

        await player.seek(position)

    @staticmethod
    async def restart(guild_state: GuildMusicData) -> bool:
        player: wavelink.Player = guild_state.player

        if not player.current:
            raise NoCurrentTrack

        await player.seek(0)
        return True

    @staticmethod
    async def set_queue_mode(guild_state: GuildMusicData, mode: wavelink.QueueMode):
        guild_state.player.queue.mode = mode

    @staticmethod
    async def loop(guild_state: GuildMusicData) -> bool:
        queue: wavelink.Queue = guild_state.player.queue

        if not guild_state.player.current:
            raise NoCurrentTrack

        if queue.mode == wavelink.QueueMode.loop_all:
            raise AlreadyLoopAll

        if queue.mode == wavelink.QueueMode.normal:
            queue.mode = wavelink.QueueMode.loop
            return True
        elif queue.mode == wavelink.QueueMode.loop:
            queue.mode = wavelink.QueueMode.normal
            return False

    @staticmethod
    async def loop_all(guild_state: GuildMusicData):
        queue: wavelink.Queue = guild_state.player.queue

        if not guild_state.player.current:
            raise NoCurrentTrack

        if queue.mode == wavelink.QueueMode.loop:
            raise AlreadyLoop

        if queue.mode == wavelink.QueueMode.normal:
            queue.mode = wavelink.QueueMode.loop_all
            return True
        elif queue.mode == wavelink.QueueMode.loop_all:
            queue.mode = wavelink.QueueMode.normal
            return False

    @staticmethod
    async def shuffle(guild_state: GuildMusicData):
        queue: wavelink.Queue = guild_state.player.queue

        if queue.is_empty:
            raise QueueEmpty

        queue.shuffle()

    @staticmethod
    async def reset(guild_state: GuildMusicData):
        queue: wavelink.Queue = guild_state.player.queue

        if queue.is_empty:
            raise QueueEmpty

        queue.clear()

    @staticmethod
    async def remove(guild_state: GuildMusicData, index: int) -> wavelink.Playable:
        queue: wavelink.Queue = guild_state.player.queue

        if queue.is_empty:
            raise QueueEmpty

        if index < 0 or index >= len(queue):
            raise IndexError

        track = queue.peek(index)
        queue.delete(index)

        return track

    @staticmethod
    async def swap(guild_state: GuildMusicData, index1: int, index2: int) -> tuple[wavelink.Playable, wavelink.Playable]:
        queue: wavelink.Queue = guild_state.player.queue

        if queue.is_empty:
            raise QueueEmpty

        if index1 != index2 and (index1 < 0 or index1 >= len(queue) or index2 < 0 or index2 >= len(queue)):
            raise IndexError

        tracks = queue.peek(index1), queue.peek(index2)
        queue.swap(index1, index2)

        return tracks

    @staticmethod
    async def queue(guild_state: GuildMusicData) -> tuple[str, list[str]]:
        queue: wavelink.Queue = guild_state.player.queue

        if queue.is_empty:
            raise QueueEmpty

        queues = []
        current = ""
        for i, song in enumerate(queue):
            queue_str = f"{i + 1}. [{song.title}]({song.uri})\n"
            if len(current) + len(queue_str) <= 4090:
                current += queue_str
            else:
                queues.append(current)
                current = queue_str
        if current:
            queues.append(current)
        return queues[0], queues[1:]

    @staticmethod
    async def play_next(guild_state: GuildMusicData):
        player: wavelink.Player = guild_state.player
        try:
            await player.play(player.queue.get())
        except wavelink.QueueEmpty:
            pass

    async def inactive_player(self, guild_state: GuildMusicData):
        await self.leave(guild_state)

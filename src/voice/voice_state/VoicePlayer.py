from src.exceptions.PlayerExceptions import *
from src.exceptions.QueueException import *
from typing import Optional

import wavelink


class VoicePlayer:
    def __init__(self, player: wavelink.Player) -> None:
        self.__player: wavelink.Player = player

    def get_player(self) -> wavelink.Player:
        return self.__player

    def get_current_track(self) -> Optional[wavelink.Playable]:
        return self.__player.current

    def is_connected(self) -> bool:
        return self.__player.connected

    def is_paused(self) -> bool:
        return self.__player.paused

    async def leave(self) -> None:
        await self.__player.disconnect(force=True)

    def put_in_queue(self, track: wavelink.Playable) -> None:
        self.__player.queue.put(track)

    def put_in_queue_at(self, index: int, track: wavelink.Playable) -> None:
        self.__player.queue.put_at(index, track)

    async def play(self) -> None:
        await self.play_next()

    async def skip(self, force: bool) -> None:
        if not await self.__player.stop(force=force):
            raise NoCurrentTrack

    async def pause(self) -> None:

        if not self.__player.current:
            raise NoCurrentTrack

        if self.__player.paused:
            raise AlreadyPaused

        await self.__player.pause(True)

    async def resume(self) -> None:

        if not self.__player.current:
            raise NoCurrentTrack

        if not self.__player.paused:
            raise AlreadyResumed

        await self.__player.pause(False)

    async def stop(self) -> bool:
        player: wavelink.Player = self.__player

        if not player.current:
            raise NoCurrentTrack

        if flag := not player.queue.is_empty:
            player.queue.clear()

        await player.skip()

        return flag

    async def volume(self, volume: int) -> None:
        if volume < 0 or volume > 1000:
            raise ValueError

        await self.__player.set_volume(volume)

    async def seek(self, position: int) -> None:
        player: wavelink.Player = self.__player

        if not player.current:
            raise NoCurrentTrack

        if not player.current.is_seekable:
            raise TrackNotSeekable

        if position < 0 or position >= player.current.length:
            raise InvalidSeekTime

        await player.seek(position)

    async def restart(self) -> bool:
        player: wavelink.Player = self.__player

        if not player.current:
            raise NoCurrentTrack

        await player.seek(0)
        return True

    def get_queue_mode(self) -> wavelink.QueueMode:
        return self.__player.queue.mode

    def set_queue_mode(self, mode: wavelink.QueueMode) -> None:
        self.__player.queue.mode = mode

    async def shuffle(self) -> None:
        queue: wavelink.Queue = self.__player.queue

        if queue.is_empty:
            raise QueueEmpty

        queue.shuffle()

    async def reset(self) -> None:
        queue: wavelink.Queue = self.__player.queue

        if queue.is_empty:
            raise QueueEmpty

        queue.clear()

    async def remove(self, index: int) -> wavelink.Playable:
        queue: wavelink.Queue = self.__player.queue

        if queue.is_empty:
            raise QueueEmpty

        if index < 0 or index >= len(queue):
            raise IndexError

        track = queue.peek(index)
        queue.delete(index)

        return track

    async def swap(self, index1: int, index2: int) -> tuple[wavelink.Playable, wavelink.Playable]:
        queue: wavelink.Queue = self.__player.queue

        if queue.is_empty:
            raise QueueEmpty

        if index1 != index2 and (index1 < 0 or index1 >= len(queue) or index2 < 0 or index2 >= len(queue)):
            raise IndexError

        tracks = queue.peek(index1), queue.peek(index2)
        queue.swap(index1, index2)

        return tracks

    async def queue(self) -> wavelink:
        queue: wavelink.Queue = self.__player.queue

        if queue.is_empty:
            raise QueueEmpty

        return self.__player.queue

    async def play_next(self) -> None:
        player: wavelink.Player = self.__player
        try:
            await player.play(player.queue.get())
        except wavelink.QueueEmpty:
            pass

    async def inactive_player(self) -> None:
        await self.leave()

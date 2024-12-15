from src.exceptions.player_exceptions import *
from src.exceptions.QueueException import *
from typing import Optional

import wavelink


class VoicePlayer:
    def __init__(self, player: wavelink.Player) -> None:
        self.__player: wavelink.Player = player
        self.__original_queue: Optional[wavelink.Queue] = None

    def get_auto_play_mode(self) -> wavelink.AutoPlayMode:
        return self.__player.autoplay

    def set_auto_play_mode(self, mode: wavelink.AutoPlayMode) -> None:
        self.__player.autoplay = mode

    def get_current_track(self) -> Optional[wavelink.Playable]:
        return self.__player.current

    def is_connected(self) -> bool:
        return self.__player.connected

    def is_paused(self) -> bool:
        return self.__player.paused

    async def leave(self) -> None:
        await self.__player.disconnect(force=True)

    def put_in_front_at_queue(self, track: wavelink.Playable) -> None:
        self.__player.queue.put_at(0, track)

    def put_in_queue(self, tracks: list[wavelink.Playable] | wavelink.Playable | wavelink.Playlist) -> None:
        self.__player.queue.put(tracks)

    async def skip(self, force: bool) -> None:
        if not await self.__player.skip(force=force):
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

    async def reset(self) -> None:
        player: wavelink.Player = self.__player

        if not player.current:
            raise NoCurrentTrack

        player.queue.reset()
        player.auto_queue.reset()

        await player.skip()

    async def restart(self) -> None:
        player: wavelink.Player = self.__player

        if not player.current:
            raise NoCurrentTrack

        await player.seek(0)

    def get_queue_mode(self) -> wavelink.QueueMode:
        return self.__player.queue.mode

    def set_queue_mode(self, mode: wavelink.QueueMode) -> None:
        self.__player.queue.mode = mode

    def queue(self) -> wavelink.Queue:
        return self.__player.queue

    def queue_history(self) -> wavelink.Queue:
        return self.__player.queue.history

    def get_from_queue_history(self, index: int | None):
        if index is None:
            return self.__player.queue.history.get()
        return self.__player.queue.history.get_at(index)

    def auto_queue(self) -> wavelink.Queue:
        return self.__player.auto_queue

    async def play_previous(self, track: wavelink.Playable) -> None:
        await self.__player.play(track, replace=True)

    def position(self) -> int:
        return self.__player.position

    async def play_next(self) -> None:
        player: wavelink.Player = self.__player
        try:
            track = player.queue.get()
            if track.recommended:
                self.__switch_to_recommended()
            await player.play(track)
        except wavelink.QueueEmpty:
            pass

    def __switch_to_recommended(self) -> None:
        player: wavelink.Player = self.__player
        if player.queue.mode != wavelink.QueueMode.normal:
            player.queue.mode = wavelink.QueueMode.normal
        if self.__original_queue is not None:
            self.__original_queue = None

    async def inactive_player(self) -> None:
        await self.leave()

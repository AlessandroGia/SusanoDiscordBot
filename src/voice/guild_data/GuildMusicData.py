from typing import Optional

import wavelink


class GuildMusicData:
    def __init__(self, channel_id: int, player: wavelink.Player):
        self.channel_id: int = channel_id
        self.player: wavelink.Player = player

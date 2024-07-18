from typing import Optional

import discord
import wavelink


class GuildMusicData:
    def __init__(self, channel_id: int, player: wavelink.Player):
        self.channel_id: int = channel_id
        self.player: wavelink.Player = player
        self.last_message: Optional[discord.Message | discord.Interaction] = None

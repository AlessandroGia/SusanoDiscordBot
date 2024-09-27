from typing import Optional

import discord
import wavelink

from src.voice.voice_state.VoicePlayer import VoicePlayer


class GuildMusicData:
    def __init__(self, channel_id: int, voice_player: VoicePlayer):
        self.channel_id: int = channel_id
        self.voice_player: VoicePlayer = voice_player
        self.last_view: Optional[discord.ui.View] = None
        self.last_mess: Optional[discord.Message] = None


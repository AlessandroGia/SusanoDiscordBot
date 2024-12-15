from discord import Interaction
from discord.ui import Button

import discord

from src.voice.guild_voice_state import GuildVoiceState


class Back(Button):
    def __init__(self, voice_state: GuildVoiceState, row: int):
        self.__voice_state = voice_state

        super().__init__(
            emoji="⏮️",
            style=discord.ButtonStyle.secondary,
            row=row
        )

    async def callback(self, interaction: Interaction):
        if self.__voice_state.position(interaction) // 1000 > 5 or self.__voice_state.queue_history(interaction).count < 2:
            await self.__voice_state.restart(interaction)
            view = self.view
        else:
            await self.__voice_state.play_previous(interaction)
            view = None

        await interaction.response.edit_message(view=view)

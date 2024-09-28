import discord
from discord import Interaction
from discord.ui import Button

from src.voice.VoiceGuild import VoiceState


class ResumePause(Button):
    def __init__(self, voice_state: VoiceState, guild_id: int, row: int):
        self.__voice_state = voice_state
        emoji = "▶️" if self.__voice_state.is_paused(guild_id) else "⏸️"

        super().__init__(
            emoji=emoji,
            style=discord.ButtonStyle.primary,
            row=row
        )

    async def callback(self, interaction: Interaction):
        state = await self.__voice_state.toggle_pause(interaction)
        self.emoji = "▶️" if state else "⏸️"
        await interaction.response.edit_message(view=self.view)
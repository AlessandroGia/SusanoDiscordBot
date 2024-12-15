import discord
from discord import Interaction
from discord.ui import Button

from src.voice.guild_voice_state import GuildVoiceState


class Reset(Button):
    def __init__(self, voice_state: GuildVoiceState, row: int):
        self.__voice_state = voice_state

        super().__init__(
            emoji="⏹️",
            style=discord.ButtonStyle.danger,
            row=row
        )

    async def callback(self, interaction: Interaction):
        await self.__voice_state.reset(interaction)
        await interaction.response.edit_message(view=None)
        self.view.stop()
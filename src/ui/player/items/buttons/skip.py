import discord
from discord import Interaction
from discord.ui import Button

from src.voice.VoiceGuild import VoiceState


class Skip(Button):
    def __init__(self, voice_state: VoiceState, row: int):
        self.__voice_state = voice_state

        super().__init__(
            emoji="⏭️",
            style=discord.ButtonStyle.secondary,
            row=row
        )

    async def callback(self, interaction: Interaction):
        await self.__voice_state.skip(interaction)
        await interaction.response.edit_message(view=None)
        self.view.stop()
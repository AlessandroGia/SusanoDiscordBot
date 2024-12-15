import discord
from discord import Interaction
from discord.ui import Button
import wavelink

from src.voice.guild_voice_state import GuildVoiceState


class Loop(Button):
    def __init__(self, voice_state: GuildVoiceState, guild_id: int, row: int):
        self.__voice_state = voice_state
        queue_mode = self.__voice_state.get_queue_mode(guild_id)

        super().__init__(
            emoji="🔂" if queue_mode == wavelink.QueueMode.loop else "🔁",
            style=discord.ButtonStyle.secondary if queue_mode == wavelink.QueueMode.normal else discord.ButtonStyle.success,
            row=row
        )

    async def callback(self, interaction: Interaction):

        mode = self.__voice_state.toggle_loop(interaction)

        if mode == wavelink.QueueMode.loop_all:
            self.emoji = "🔁"
            self.style = discord.ButtonStyle.success
        elif mode == wavelink.QueueMode.loop:
            self.emoji = "🔂"
            self.style = discord.ButtonStyle.success
        else:
            self.emoji = "🔁"
            self.style = discord.ButtonStyle.secondary

        await interaction.response.edit_message(view=self.view)

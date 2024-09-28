from math import ceil

import discord
import wavelink
from discord import Interaction
from discord.ui import Button

from src.ui.QueueUI import QueueView
from src.utils.embed import EmbedQueue, EmbedFactory
from src.voice.VoiceGuild import VoiceState


class Queue(Button):
    def __init__(self, voice_state: VoiceState, row: int):
        self.__voice_state = voice_state
        self.__embed = EmbedFactory()

        super().__init__(
            emoji="📜",
            style=discord.ButtonStyle.secondary,
            row=row
        )

    async def callback(self, interaction: Interaction):
        queue: wavelink.Queue = self.__voice_state.queues(interaction)
        track_per_page: int = 10
        max_page: int = ceil(queue.count / track_per_page)
        embed: EmbedQueue = EmbedQueue(
            queue.count,
            max_page,
            track_per_page
        )

        await interaction.response.send_message(
            embed=embed.queue(
                queue[:track_per_page],
                1
            ),
            view=QueueView(
                queue,
                embed
            ),
            ephemeral=True
        )

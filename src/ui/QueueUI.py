from enum import Enum
from multiprocessing.dummy import current_process

import wavelink
from discord.ui import Button, View, Item
import discord

from src.utils.embed import EmbedFactory, EmbedQueue


class DirectionButton(Enum):
    BACK = '⬅️'
    FORWARD = '➡️'

class QueueButton(Button):
    def __init__(self, direction: DirectionButton):
        self.__direction = direction
        super().__init__(
            emoji=direction.value,
            style=discord.ButtonStyle.secondary,
        )

    async def callback(self, interaction):
        if self.__direction == DirectionButton.BACK:
            self.view.current_page -= 1
        elif self.__direction == DirectionButton.FORWARD:
            self.view.current_page += 1

        queue = self.view.get_tracks_by_page(self.view.current_page)
        self.view.check()
        await interaction.response.edit_message(
            embed=self.view.embed.queue(
                queue,
                self.view.current_page,
            ),
            view=self.view,
        )


class QueueView(View):
    def __init__(self, queue: wavelink.Queue, embed: EmbedQueue):
        super().__init__()
        self.__queue = queue

        self.embed = embed
        self.current_page = 1

        self.back_button = QueueButton(DirectionButton.BACK)
        self.forward_button = QueueButton(DirectionButton.FORWARD)

        if embed.max_page > 1:
            self.add_item(self.back_button)
            self.add_item(self.forward_button)

        self.check()


    def get_tracks_by_page(self, page: int):
        return self.__queue[(page - 1) * self.embed.track_per_page: page * self.embed.track_per_page]

    def check(self):
        self.back_button.disabled = self.current_page <= 1
        self.forward_button.disabled = self.current_page >= self.embed.max_page


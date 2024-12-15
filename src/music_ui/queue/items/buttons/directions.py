from enum import Enum

import discord
from discord.ui import Button


class DirectionButton(Enum):
    BACK = '⬅️'
    FORWARD = '➡️'

class Direction(Button):
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
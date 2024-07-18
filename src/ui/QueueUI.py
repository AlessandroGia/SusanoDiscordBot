import discord
import wavelink
from discord import Interaction

from src.utils.embed import EmbedFactory


class ButtonSwitch(discord.ui.Button):
    def __init__(self, update_message: callable):
        super().__init__(
            label='Next',
            style=discord.ButtonStyle.primary
        )
        self.__update_message = update_message

    async def callback(self, interaction: discord.Interaction):
        self.__update_message(interaction)


class QueueView(discord.ui.View):
    def __init__(self, interaction: Interaction, queue: wavelink.Queue, items_per_page: int = 2):
        super().__init__()
        self.__interaction: Interaction = interaction
        self.__queue: wavelink.Queue = queue
        self.__items_per_page: int = items_per_page
        self.__current_page = 0
        self.__embed = EmbedFactory()
        self.update_buttons()

    def update_buttons(self):

        print(self.__current_page)
        if self.__current_page == 0:
            self.previous_button.disabled = True
        else:
            self.previous_button.disabled = False

        if self.__current_page == len(self.__queue) // self.__items_per_page:
            self.next_button.disabled = True
        else:
            self.next_button.disabled = False

    async def __update_message(self, interaction: Interaction):
        await self.__interaction.delete_original_response()
        await interaction.response.send_message(
            embed=self.__embed.queue(
                self.__queue,
                self.__current_page + 1,
                self.__items_per_page
            ),
            view=self,
            ephemeral=True
        )
        self.__interaction = interaction

    @discord.ui.button(label='Previous', style=discord.ButtonStyle.primary)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.update_buttons()
        self.__current_page -= 1
        await self.__update_message(interaction)

    @discord.ui.button(label='Next', style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.update_buttons()
        self.__current_page += 1
        await self.__update_message(interaction)

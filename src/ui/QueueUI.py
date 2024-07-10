import discord
import wavelink
from discord import Interaction


class QueueView(discord.ui.View):
    def __init__(self, interaction: Interaction, queue: wavelink.Queue, items_per_page: int = 2):
        super().__init__()
        self.__interaction: Interaction = interaction
        self.__queue: wavelink.Queue = queue
        self.__items_per_page: int = items_per_page
        self.__current_page = 0
        self.__update_buttons()

    def __update_buttons(self):
        self.clear_items()
        if self.__current_page > 0:
            self.add_item(discord.ui.Button(label='Previous', style=discord.ButtonStyle.primary, custom_id='previous'))
        if (self.__current_page + 1) * self.__items_per_page < self.__queue.count:
            self.add_item(discord.ui.Button(label='Next', style=discord.ButtonStyle.primary, custom_id='next'))

    async def __update_message(self):
        start = self.__current_page * self.__items_per_page
        end = start + self.__items_per_page
        queue_page = self.__queue[start:end]
        queue_str = ""
        for i, song in enumerate(queue_page, start=start):
            queue_str += f"{i+1}. {song['title']} - [Link]({song['webpage_url']})\n"

        embed = discord.Embed(
            title=f"Coda di Riproduzione - Pagina {self.__current_page + 1}",
            description=queue_str,
            color=discord.Color.blue()
        )
        embed.set_footer(
            text=f"Pagina {self.__current_page + 1} di {len(self.__queue) // self.__items_per_page + 1}"
        )
        await self.__interaction.message.edit(
            embed=embed,
            view=self
        )

    @discord.ui.button(label='Previous', style=discord.ButtonStyle.primary, custom_id='previous')
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.__current_page -= 1
        self.__update_buttons()
        await self.__update_message()

    @discord.ui.button(label='Next', style=discord.ButtonStyle.primary, custom_id='next')
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.__current_page += 1
        self.__update_buttons()
        await self.__update_message()


from enum import Enum
from typing import Any

import discord.ui
import wavelink
from aiohttp.web_routedef import delete
from discord import Interaction
from discord.ui import Button, View, Item
from math import ceil

from src.exceptions.QueueException import *
from src.exceptions.VoiceChannelExceptions import *
from src.exceptions.PlayerExceptions import *
from src.ui.QueueUI import QueueView

from src.utils.embed import EmbedFactory, EmbedQueue


class ResumePauseButton(Button):
    def __init__(self, voice_state, guild_id: int, row: int):
        self.__voice_state = voice_state

        emoji = "▶️" if self.__voice_state.is_paused(guild_id) else "⏸️"

        super().__init__(
            emoji=emoji,
            style=discord.ButtonStyle.primary,
            row=row
        )

    async def callback(self, interaction):
        state = await self.__voice_state.toggle_pause(interaction)
        self.emoji = "▶️" if state else "⏸️"
        await interaction.response.edit_message(view=self.view)

class BackButton(Button):
    def __init__(self, voice_state, row: int):
        self.__voice_state = voice_state
        super().__init__(
            emoji="⏮️",
            style=discord.ButtonStyle.secondary,
            row=row
        )

    async def callback(self, interaction):
        await self.__voice_state.restart(interaction)
        await interaction.response.edit_message(view=self.view)

class ShuffleButton(Button):
    def __init__(self, voice_state, guild_id: int, row: int):
        self.__voice_state = voice_state
        super().__init__(
            emoji = "🔀",
            style = discord.ButtonStyle.secondary if not self.__voice_state.is_shuffled(guild_id) else discord.ButtonStyle.success,
            disabled=True if self.__voice_state.get_current_track(guild_id).recommended else False,
            row=row
        )

    async def callback(self, interaction):
        is_shuffled: bool = self.__voice_state.toggle_shuffle(interaction)
        self.style = discord.ButtonStyle.success if is_shuffled else discord.ButtonStyle.secondary
        await interaction.response.edit_message(view=self.view)

class SkipButton(Button):
    def __init__(self, voice_state, row: int):
        self.__voice_state = voice_state

        super().__init__(
            emoji="⏭️",
            style=discord.ButtonStyle.secondary,
            row=row
        )

    async def callback(self, interaction):
        await self.__voice_state.skip(interaction)
        await interaction.response.edit_message(view=self.view)
        self.view.stop()

class LoopButton(Button):
    def __init__(self, voice_state, guild_id: int, row: int):
        self.__voice_state = voice_state

        queue_mode = self.__voice_state.get_queue_mode(guild_id)

        super().__init__(
            emoji = "🔂" if queue_mode == wavelink.QueueMode.loop else "🔁",
            style = discord.ButtonStyle.secondary if queue_mode == wavelink.QueueMode.normal else discord.ButtonStyle.success,
            disabled=True if self.__voice_state.get_current_track(guild_id).recommended else False,
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

class ResetButton(Button):
    def __init__(self, voice_state, row: int):
        self.__voice_state = voice_state
        super().__init__(
            emoji="⏹️",
            style=discord.ButtonStyle.danger,
            row=row
        )

    async def callback(self, interaction):
        self.__voice_state.set_queue_mode(interaction, wavelink.QueueMode.normal)
        self.__voice_state.get_player(interaction.guild_id).queue.clear()
        await self.__voice_state.get_player(interaction.guild_id).stop()

        await interaction.response.edit_message(view=self.view)
        self.view.stop()

class QueueButton(Button):
    def __init__(self, voice_state, row: int):
        self.__voice_state = voice_state
        self.__embed = EmbedFactory()
        super().__init__(
            emoji="📜",
            style=discord.ButtonStyle.secondary,
            row=row
        )

    async def callback(self, interaction):
        queue: wavelink.Queue = await self.__voice_state.queue(interaction)
        auto_queue: wavelink.Queue = self.__voice_state.auto_queue(interaction)
        new_queue: wavelink.Queue() = wavelink.Queue()

        print('queue', len(queue), '--->', queue)
        print('auto_queue', len(auto_queue), '--->', auto_queue)

        if not queue and not auto_queue:
            raise QueueEmpty

        for track in queue:
            new_queue.put(track)

        for track in auto_queue:
            new_queue.put(track)

        track_per_page: int = 25

        max_page: int = ceil(new_queue.count / track_per_page)
        embed = EmbedQueue(
            new_queue.count,
            max_page,
            track_per_page
        )
        await interaction.response.send_message(
            embed=embed.queue(
                new_queue[:track_per_page],
                1
            ),
            view=QueueView(
                new_queue,
                embed
            ),
            ephemeral=True
        )


class PlayerView(View):
    def __init__(self, voice_state, guild_id: int):
        super().__init__()
        self.__embed = EmbedFactory()
        self.add_item(ShuffleButton(voice_state, guild_id, 0))
        self.add_item(BackButton(voice_state, 0))
        self.add_item(ResumePauseButton(voice_state, guild_id, 0))
        self.add_item(ResetButton(voice_state, 1))
        self.add_item(SkipButton(voice_state, 0))
        self.add_item(LoopButton(voice_state, guild_id, 0))
        self.add_item(QueueButton(voice_state, 1))


    def __send_error(self, interaction: Interaction, error: str):
        return interaction.response.send_message(
            embed=self.__embed.error(error),
            ephemeral=True,
            delete_after=5
        )

    async def on_error(self, interaction: Interaction, error: Exception, item: Item[Any], /) -> None:

        if isinstance(error, UserNonConnessoError):
            await self.__send_error(interaction, 'Devi essere connesso a un canale vocale')
        elif isinstance(error, BotNonPresenteError):
            await self.__send_error(interaction, 'Il bot non è connesso a un canale vocale')
        elif isinstance(error, UserNonStessoCanaleBotError):
            await self.__send_error(interaction, 'Devi essere nello stesso canale vocale del bot')

        elif isinstance(error, IllegalState):
            await self.__send_error(interaction, 'Comando non valido')

        elif isinstance(error, NoCurrentTrack):
            await self.__send_error(interaction, 'Nessuna canzone in riproduzione')
        elif isinstance(error, AlreadyPaused):
            await self.__send_error(interaction, 'Canzone già in pausa')
        elif isinstance(error, AlreadyResumed):
            await self.__send_error(interaction, 'Canzone già ripresa')

        elif isinstance(error, AlreadyLoopAll):
            await self.__send_error(interaction, 'Canzone già in Loop All')
        elif isinstance(error, AlreadyLoop):
            await self.__send_error(interaction, 'Canzone già in Loop')

        elif isinstance(error, QueueEmpty):
            await self.__send_error(interaction, 'Coda vuota')

        else:
            print("Errore in playerUI: ", error)

from enum import Enum
from typing import Any

import discord.ui
import wavelink
from aiohttp.web_routedef import delete
from discord import Interaction
from discord.ui import Button, View, Item

from src.exceptions.QueueException import *
from src.exceptions.VoiceChannelExceptions import *
from src.exceptions.PlayerExceptions import *

from src.utils.embed import EmbedFactory


class ResumePauseButton(Button):
    def __init__(self, voice_state, guild_id: int):
        self.__voice_state = voice_state

        if self.__voice_state.is_paused(guild_id):
            emoji = "▶️"
        else:
            emoji = "⏸️"

        super().__init__(
            emoji=emoji,
            style=discord.ButtonStyle.primary,
            row=0
        )

    async def callback(self, interaction):

        if not self.__voice_state.is_paused(interaction.guild_id):
            await self.__voice_state.pause(interaction)
            self.emoji = "▶️"
        else:
            await self.__voice_state.resume(interaction)
            self.emoji = "⏸️"

        await interaction.response.edit_message(view=self.view)

class BackButton(Button):
    def __init__(self, voice_state, guild_id: int):
        self.__voice_state = voice_state
        super().__init__(
            emoji="⏮️",
            style=discord.ButtonStyle.secondary,
            row=0
        )

    async def callback(self, interaction):
        await self.__voice_state.restart(interaction)
        await interaction.response.edit_message(view=self.view)

class ShuffleButton(Button):
    def __init__(self, voice_state, guild_id: int):
        self.__voice_state = voice_state
        self.__state = True
        super().__init__(
            emoji = "🔀",
            style = discord.ButtonStyle.secondary,
            row=0
        )

    async def callback(self, interaction):
        if self.__state:
            self.style = discord.ButtonStyle.success
            #await self.__voice_state.shuffle(interaction)
            self.__state = False
        else:
            self.style = discord.ButtonStyle.secondary
            #await self.__voice_state.unshuffle(interaction)
            self.__state = True

        await interaction.response.edit_message(view=self.view)

class SkipButton(Button):
    def __init__(self, voice_state, guild_id: int):
        self.__voice_state = voice_state

        super().__init__(
            emoji="⏭️",
            style=discord.ButtonStyle.secondary,
            row=0
        )

    async def callback(self, interaction):
        queue_mode = self.__voice_state.get_queue_mode(interaction.guild_id)

        if queue_mode == wavelink.QueueMode.loop:
            self.__voice_state.set_queue_mode(interaction, wavelink.QueueMode.loop_all)

        if queue_mode == wavelink.QueueMode.loop_all:
            await self.__voice_state.skip(interaction, force=False)
        else:
            await self.__voice_state.skip(interaction)

        await interaction.response.edit_message(view=self.view)
        self.view.stop()

class LoopButton(Button):
    def __init__(self, voice_state, guild_id: int):
        self.__voice_state = voice_state

        queue_mode = self.__voice_state.get_queue_mode(guild_id)

        super().__init__(
            emoji = "🔂" if queue_mode == wavelink.QueueMode.loop else "🔁",
            style = discord.ButtonStyle.secondary if queue_mode == wavelink.QueueMode.normal else discord.ButtonStyle.success,
            row=0
        )

    async def callback(self, interaction: Interaction):

        queue_mode = self.__voice_state.get_queue_mode(interaction.guild_id)

        if queue_mode == wavelink.QueueMode.normal:
            self.emoji = "🔁"
            self.style = discord.ButtonStyle.success
            self.__voice_state.set_queue_mode(interaction, wavelink.QueueMode.loop_all)
        elif queue_mode == wavelink.QueueMode.loop_all:
            self.emoji = "🔂"
            self.style = discord.ButtonStyle.success
            self.__voice_state.set_queue_mode(interaction, wavelink.QueueMode.loop)
        else:
            self.emoji = "🔁"
            self.style = discord.ButtonStyle.secondary
            self.__voice_state.set_queue_mode(interaction, wavelink.QueueMode.normal)

        await interaction.response.edit_message(view=self.view)

class ResetButton(Button):
    def __init__(self, voice_state, guild_id: int):
        self.__voice_state = voice_state
        super().__init__(
            emoji="⏹️",
            style=discord.ButtonStyle.danger,
            row=1
        )

    async def callback(self, interaction):
        self.__voice_state.set_queue_mode(interaction, wavelink.QueueMode.normal)
        self.__voice_state.get_player(interaction.guild_id).queue.clear()
        await self.__voice_state.get_player(interaction.guild_id).stop()

        await interaction.response.edit_message(view=self.view)
        self.view.stop()

class QueueButton(Button):
    def __init__(self, voice_state, guild_id: int):
        self.__voice_state = voice_state
        self.__embed = EmbedFactory()
        super().__init__(
            emoji="📜",
            style=discord.ButtonStyle.secondary,
            row=1
        )

    async def callback(self, interaction):
        await self.__voice_state.queue(interaction)

        interaction_queue, followup_queues = await self.__voice_state.queue(interaction)

        await interaction.response.send_message(
            embed=self.__embed.queue(interaction_queue, 1, len(followup_queues) + 1),
            ephemeral=True,
        )

        for i, queue in enumerate(followup_queues, 2):
            await interaction.followup.send(
                embed=self.__embed.queue(queue, i, len(followup_queues) + 1),
                ephemeral=True
            )

class PlayerView(View):
    def __init__(self, voice_state, guild_id: int):
        super().__init__()
        self.__embed = EmbedFactory()
        self.add_item(ShuffleButton(voice_state, guild_id))
        self.add_item(BackButton(voice_state, guild_id))
        self.add_item(ResumePauseButton(voice_state, guild_id))
        self.add_item(ResetButton(voice_state, guild_id))
        self.add_item(SkipButton(voice_state, guild_id))
        self.add_item(LoopButton(voice_state, guild_id))
        self.add_item(QueueButton(voice_state, guild_id))


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

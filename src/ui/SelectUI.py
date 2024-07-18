from discord import Interaction
from discord._types import ClientT
from discord.ui import Button, View, Select, Item
from typing import Callable, Coroutine, Any, Optional
from src.voice.VoiceGuild import VoiceState

import wavelink
import discord

from src.exceptions.PlayerExceptions import IllegalState
from src.utils.embed import EmbedFactory
from src.utils.utils import convert_time


class SelectTrackDropdown(Select):
    def __init__(
            self,
            interaction: discord.Interaction,
            voice_state: VoiceState,
            tracks: list[wavelink.Playable]):

        self.__interaction: discord.Interaction = interaction
        self.__voice_state: VoiceState = voice_state
        self.__tracks: list[wavelink.Playable] = tracks
        self.__embed: EmbedFactory = EmbedFactory()

        _format = lambda label: label[:96] + "..." if len(label) >= 100 else label
        options: list[discord.SelectOption] = [
            discord.SelectOption(
                label=_format(
                    f"{track.title} - {track.author}"
                ),
                description=_format(
                    f"{track.album.name + " " if track.album.name else ""}{convert_time(track.length)}"
                ),
                value=track.identifier
            ) for track in tracks[:25]
        ]

        super().__init__(
            placeholder=f'{len(tracks)} tracce trovate...',
            min_values=1,
            max_values=len(tracks),
            options=options
        )

    async def interaction_check(self, interaction: Interaction[ClientT], /) -> bool:
        return not self.disabled

    async def callback(self, interaction: discord.Interaction):
        self.disabled = True
        tracks: list[wavelink.Playable] = [
            track for track in self.__tracks if track.identifier in self.values
        ]
        await self.__interaction.delete_original_response()
        track_playing, tracks_queue = await self.__voice_state.play(interaction, tracks)

        await self.__voice_state.feedback_play_command(
            interaction,
            track_playing,
            tracks_queue
        )


class SelectTrackView(View):
    def __init__(
            self,
            interaction: discord.Interaction,
            voice_state: VoiceState,
            tracks: list[wavelink.Playable]):
        super().__init__()
        self.add_item(SelectTrackDropdown(interaction, voice_state, tracks))
        self.__embed = EmbedFactory()

    def __send_error(self, interaction: Interaction, error: str):
        return interaction.response.send_message(
            embed=self.__embed.error(error),
            ephemeral=True,
            delete_after=5
        )

    async def on_error(self, interaction: Interaction, error: Exception, item: Item[Any], /) -> None:
        if isinstance(error, IllegalState):
            await self.__send_error(interaction, 'Comando non valido')
        else:
            print(f"SelectTrackView.on_error error: {error}")
            await self.__send_error(interaction, 'Errore sconosciuto')


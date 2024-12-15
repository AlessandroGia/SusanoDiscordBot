from discord import Interaction
from discord._types import ClientT
from discord.ui import Button, View, Select, Item
from typing import Callable, Coroutine, Any, Optional
from src.voice.guild_voice_state import GuildVoiceState

import wavelink
import discord

from src.exceptions.player_exceptions import IllegalState
from src.utils.embed import EmbedFactory
from src.music_ui.track_select.items.dropdowns.tracks import Tracks


class SelectTrackView(View):
    def __init__(
            self,
            voice_state: GuildVoiceState,
            interaction: discord.Interaction,
            tracks: list[wavelink.Playable]):
        super().__init__()
        self.add_item(
            Tracks(
                voice_state,
                interaction,
                tracks
            )
        )
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


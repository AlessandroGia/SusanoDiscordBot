from typing import Any


from discord import Interaction
from discord.ui import Button, View, Item


from src.exceptions.QueueException import *
from src.exceptions.voice_channel_exceptions import *
from src.exceptions.player_exceptions import *

from src.music_ui.player.items.buttons.back import Back
from src.music_ui.player.items.buttons.loop import Loop
from src.music_ui.player.items.buttons.resume_pause import ResumePause
from src.music_ui.player.items.buttons.queue import Queue
from src.music_ui.player.items.buttons.reset import Reset
from src.music_ui.player.items.buttons.skip import Skip

from src.utils.embed import EmbedFactory

from src.voice.guild_voice_state import GuildVoiceState


class PlayerView(View):
    def __init__(self, voice_state: GuildVoiceState, guild_id: int):
        super().__init__(timeout=None)
        self.__embed = EmbedFactory()

        self.add_item(Back(voice_state, 0))
        self.add_item(Reset(voice_state, 0))
        self.add_item(ResumePause(voice_state, guild_id, 0))
        self.add_item(Skip(voice_state, 0))
        self.add_item(Loop(voice_state, guild_id, 0))
        self.add_item(Queue(voice_state, 1))


    def __send_error(self, interaction: Interaction, error: str):
        return interaction.response.send_message(
            embed=self.__embed.error(error),
            ephemeral=True,
            delete_after=5
        )

    async def on_error(self, interaction: Interaction, error: Exception, item: Item[Any], /) -> None:

        if isinstance(error, UserNotInVoiceChannel):
            await self.__send_error(interaction, 'Devi essere connesso a un canale vocale')
        elif isinstance(error, BotNotInVoiceChannel):
            await self.__send_error(interaction, 'Il bot non è connesso a un canale vocale')
        elif isinstance(error, UserNotInSameVoiceChannel):
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

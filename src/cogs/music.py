import discord
from discord import Object, Interaction, app_commands, ext
from discord.ext import commands

from src.exceptions.PlayerExceptions import NoCurrentTrack, AlreadyPaused, AlreadyResumed, IllegalState, QueueEmpty
from src.ui import QueueUI
from src.ui.SelectUI import SelectTrackView

from src.exceptions.Generic import Generic
from src.exceptions.QueueException import *
from src.exceptions.TrackPlayerExceptions import *
from src.exceptions.VoiceChannelExceptions import *

from src.checks.VoiceChannelChecks import check_voice_channel

import wavelink

from src.utils.embed import EmbedFactory
from src.voice.VoiceGuild import VoiceState


class Music(ext.commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.__bot: commands.Bot = bot
        self.__VoiceState = VoiceState(bot)
        self.__embed = EmbedFactory()

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, payload: wavelink.NodeReadyEventPayload) -> None:
        print(f"Nodo {payload.node!r} is ready!")

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload) -> None:
        await self.__VoiceState.display_now_playing(
            payload.player.guild.id,
            payload
        )

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload) -> None:
        if payload.player:
            print('Gunner')
            await self.__VoiceState.play_next(payload.player.guild.id)

    @commands.Cog.listener()
    async def on_wavelink_inactive_player(self, player: wavelink.Player):
        await self.__VoiceState.inactive_player(player.guild.id)

    def __send_message(self, interaction: Interaction, message: str, ephemeral: bool = False, delete_after: int = 0):
        return interaction.response.send_message(
            embed=self.__embed.send(message),
            ephemeral=ephemeral,
            delete_after=delete_after
        )
    # --- --- --- --- --- --- #
    #                         #
    # --- PLAYER COMMANDS --- #
    #                         #
    # --- --- --- --- --- --- #

    @app_commands.command(
        name='join',
        description='Fa entrare il bot nel canale vocale'
    )
    @check_voice_channel()
    async def join(self, interaction: Interaction):
        await self.__VoiceState.join(interaction)
        await self.__send_message(
            interaction,
            f'Connesso al canale vocale: {interaction.user.voice.channel.name}',
            delete_after=5
        )

    @app_commands.command(
        name='leave',
        description='Fa uscire il bot dal canale vocale'
    )
    @check_voice_channel()
    async def leave(self, interaction: Interaction):
        await self.__VoiceState.leave(interaction)
        await self.__send_message(
            interaction,
            f'Uscito dal canale vocale: {interaction.user.voice.channel.name}',
            delete_after=5
        )

    @app_commands.command(
        name='play',
        description='Fa partire una canzone'

    )
    @app_commands.describe(
        search='Url o Nome della canzone da cercare',
    )
    @check_voice_channel()
    async def play(self, interaction: Interaction, search: str):
        tracks: wavelink.Search = await wavelink.Playable.search(search)
        if isinstance(tracks, list) and len(tracks) > 1:
            await interaction.response.send_message(
                view=SelectTrackView(interaction, self.__VoiceState.play, tracks),
                ephemeral=True
            )
        else:
            await self.__VoiceState.play(interaction, tracks)

    @app_commands.command(
        name='skip',
        description='Salta la canzone attuale'
    )
    @check_voice_channel()
    async def skip(self, interaction: Interaction):
        await self.__VoiceState.skip(interaction)
        await self.__send_message(
            interaction,
            'Canzone skippata',
            delete_after=5,
        )

    @app_commands.command(
        name='pause',
        description='Mette in pausa la canzone'
    )
    @check_voice_channel()
    async def pause(self, interaction: Interaction):
        await self.__VoiceState.pause(interaction)
        await self.__send_message(
            interaction,
            'Canzone in pausa',
            delete_after=5
        )

    @app_commands.command(
        name='resume',
        description='Riprende la canzone'
    )
    @check_voice_channel()
    async def resume(self, interaction: Interaction):
        await self.__VoiceState.resume(interaction)
        await self.__send_message(
            interaction,
            'Canzone ripresa',
            delete_after=5
        )

    # --- --- --- --- --- ---#
    #                        #
    # --- QUEUE COMMANDS --- #
    #                        #
    # --- --- --- --- --- ---#

    @app_commands.command(
        name='loop',
        description='Ripete la canzone attuale'
    )
    @check_voice_channel()
    async def loop(self, interaction: Interaction):
        await self.__VoiceState.loop(interaction)

    @app_commands.command(
        name='loop_all',
        description='Ripete tutte le canzoni'
    )
    @check_voice_channel()
    async def loop_all(self, interaction: Interaction):
        await self.__VoiceState.loop_all(interaction)

    @app_commands.command(
        name='shuffle',
        description='Mescola la coda delle canzoni'
    )
    @check_voice_channel()
    async def shuffle(self, interaction: Interaction):
        await self.__VoiceState.shuffle(interaction)
        await self.__send_message(
            interaction,
            'Coda mescolata',
            delete_after=5
        )

    @app_commands.command(
        name='reset',
        description='Resetta la coda delle canzoni'
    )
    @check_voice_channel()
    async def reset(self, interaction: Interaction):
        await self.__VoiceState.reset(interaction)
        await self.__send_message(
            interaction,
            'Coda resettata',
            delete_after=5
        )

    @app_commands.command(
        name='remove',
        description='Rimuove una canzone dalla coda'
    )
    @app_commands.describe(
        index='Indice della canzone da rimuovere'
    )
    @check_voice_channel()
    async def remove(self, interaction: Interaction, index: int):
        await self.__VoiceState.remove(interaction, index)

    @app_commands.command(
        name='swap',
        description='Scambia due canzoni nella coda'
    )
    @app_commands.describe(
        index1='Indice della prima canzone',
        index2='Indice della seconda canzone'
    )
    @check_voice_channel()
    async def swap(self, interaction: Interaction, index1: int, index2: int):
        await self.__VoiceState.swap(interaction, index1, index2)


    @app_commands.command(
        name='queue',
        description='Mostra la coda delle canzoni'
    )
    @check_voice_channel()
    async def queue(self, interaction: Interaction):
        await self.__VoiceState.queue(interaction)

    # --- CHECKS --- #

    def __send_error(self, interaction: Interaction, error: str):
        return interaction.response.send_message(
            embed=self.__embed.error(error),
            ephemeral=True,
            delete_after=5
        )

    # --- PLAYER ERROR HANDLING --- #

    async def __check_channel(self, interaction: Interaction, error: ext.commands.CommandError) -> bool:
        if isinstance(error, UserNonConnessoError):
            await self.__send_error(interaction, 'Devi essere connesso a un canale vocale')
        elif isinstance(error, BotNonPresenteError):
            await self.__send_error(interaction, 'Il bot non è connesso a un canale vocale')
        elif isinstance(error, UserNonStessoCanaleBotError):
            await self.__send_error(interaction, 'Devi essere nello stesso canale vocale del bot')
        elif isinstance(error, IllegalState):
            await self.__send_error(interaction, 'Comando non valido')
        else:
            return True
        return False

    @play.error
    async def play_error(self, interaction: Interaction, error: ext.commands.CommandError):
        if not await self.__check_channel(interaction, error):
            pass
        elif isinstance(error, TrackNotFoundError):
            await self.__send_error(interaction, 'Canzone non trovata')
        else:
            print(error)
            await self.__send_error(interaction, 'Errore sconosciuto')

    @leave.error
    async def leave_error(self, interaction: Interaction, error: ext.commands.CommandError):
        if not await self.__check_channel(interaction, error):
            pass
        else:
            print(error)
            await self.__send_error(interaction, 'Errore sconosciuto')

    @join.error
    async def join_error(self, interaction: Interaction, error: ext.commands.CommandError):
        if isinstance(error, UserNonConnessoError):
            await self.__send_error(interaction, 'Devi essere connesso a un canale vocale')
        elif isinstance(error, BotGiaConnessoError):
            await self.__send_error(interaction, 'Il bot è già connesso a un canale vocale')
        else:
            print(error)
            await self.__send_error(interaction, 'Errore sconosciuto')

    @pause.error
    @resume.error
    async def pause_error(self, interaction: Interaction, error: ext.commands.CommandError):
        if not await self.__check_channel(interaction, error):
            pass
        elif isinstance(error, NoCurrentTrack):
            await self.__send_error(interaction, 'Nessuna canzone in riproduzione')
        elif isinstance(error, AlreadyPaused):
            await self.__send_error(interaction, 'Canzone già in pausa')
        elif isinstance(error, AlreadyResumed):
            await self.__send_error(interaction, 'Canzone già ripresa')
        else:
            print(error)
            await self.__send_error(interaction, 'Errore sconosciuto')

    @skip.error
    async def skip_error(self, interaction: Interaction, error: ext.commands.CommandError):
        if not await self.__check_channel(interaction, error):
            pass
        elif isinstance(error, NoCurrentTrack):
            await self.__send_error(interaction, 'Nessuna canzone in riproduzione')
        else:
            print(error)
            await self.__send_error(interaction, 'Errore sconosciuto')

    # --- QUEUE ERROR HANDLING --- #

    @remove.error
    @swap.error
    @reset.error
    @shuffle.error
    async def shuffle_error(self, interaction: Interaction, error: ext.commands.CommandError):
        if not await self.__check_channel(interaction, error):
            pass
        elif isinstance(error, QueueEmpty):
            await self.__send_error(interaction, 'Coda vuota')
        elif isinstance(error, IndexError):
            await self.__send_error(interaction, 'Indice non valido')
        else:
            print(error)
            await self.__send_error(interaction, 'Errore sconosciuto')

    @loop.error
    @loop_all.error
    async def loop_error(self, interaction: Interaction, error: ext.commands.CommandError):
        if not await self.__check_channel(interaction, error):
            pass
        elif isinstance(error, NoCurrentTrack):
            await self.__send_error(interaction, 'Nessuna canzone in riproduzione')
        elif isinstance(error, AlreadyLoopAll):
            await self.__send_error(interaction, 'Canzone già in Loop All')
        elif isinstance(error, AlreadyLoop):
            await self.__send_error(interaction, 'Canzone già in Loop')
        else:
            print(error)
            await self.__send_error(interaction, 'Errore sconosciuto')


async def setup(bot: ext.commands.Bot):
    await bot.add_cog(
        Music(bot),
        guilds=[
            Object(id=928785387239915540)
        ]
    )

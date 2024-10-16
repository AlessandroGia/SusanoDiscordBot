from discord import Object, Interaction, app_commands, ext
from discord.ext import commands

from src.exceptions.Generic import InvalidFormat
from src.ui.player.player import PlayerView
from src.ui.select import SelectTrackView

from src.exceptions.PlayerExceptions import *
from src.exceptions.QueueException import *
from src.exceptions.TrackPlayerExceptions import *
from src.exceptions.VoiceChannelExceptions import *

from src.checks.VoiceChannelChecks import check_voice_channel

from src.utils.utils import check_player, convert_time_to_ms, ms_to_time
from src.utils.embed import EmbedFactory
from src.voice.VoiceGuild import VoiceState

import wavelink
import discord


class Music(ext.commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.__bot: commands.Bot = bot
        self.__voice_state = VoiceState()
        self.__embed = EmbedFactory()

    @commands.Cog.listener()
    async def on_wavelink_websocket_closed(self, payload: wavelink.WebsocketClosedEventPayload):
        self.__voice_state.server_clean_up()

    @commands.Cog.listener()
    async def on_wavelink_node_closed(self, node: wavelink.Node, disconnected: list[wavelink.Player]):
        pass

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, payload: wavelink.NodeReadyEventPayload) -> None:
        print(f"Nodo {payload.node!r} is ready!")

    @commands.Cog.listener()
    async def on_wavelink_track_stuck(self, payload: wavelink.TrackStuckEventPayload) -> None:
        if check_player(payload.player):
            print("Track stuck:", payload.threshold, payload.track.title)
            await self.__send_error_events(
                payload.player.guild.id,
                'Canzone bloccata, passando alla prossima',
            )
            #await self.__voice_state.play_next(payload.player.guild.id)

    @commands.Cog.listener()
    async def on_wavelink_track_exception(self, payload: wavelink.TrackExceptionEventPayload) -> None:
        if check_player(payload.player):
            print("Track exception:", payload.exception, payload.track.title)
            await self.__send_error_events(
                payload.player.guild.id,
                'Errore durante la riproduzione della canzone, passando alla prossima',
            )
            #await self.__voice_state.play_next(payload.player.guild.id)

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload) -> None:
        if check_player(payload.player):

            if last_view := self.__voice_state.get_last_view(payload.player.guild.id):
                if last_mess := self.__voice_state.get_last_mess(payload.player.guild.id):
                    await last_mess.edit(view=None)
                last_view.stop()

            channel: discord.TextChannel = await self.__bot.fetch_channel(
                self.__voice_state.get_channel_id(payload.player.guild.id)
            )

            view = PlayerView(self.__voice_state, payload.player.guild.id)
            mess = await channel.send(embed=self.__embed.now_playing(payload.track), view=view)

            self.__voice_state.set_last_mess(payload.player.guild.id, mess)
            self.__voice_state.set_last_view(payload.player.guild.id, view)


    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload) -> None:
        if check_player(payload.player):
            print('Fine canzone', payload.track.title, 'Motivo:', payload.reason)
            #await self.__voice_state.play_next(payload.player.guild.id)

    @commands.Cog.listener()
    async def on_wavelink_inactive_player(self, player: wavelink.Player):
        if check_player(player):
            channel: discord.TextChannel = await self.__bot.fetch_channel(
                self.__voice_state.get_channel_id(player.guild.id)
            )
            await channel.send(
                embed=self.__embed.send('Bot disconnesso per inattività'),
                delete_after=5
            )
            await self.__voice_state.inactive_player(player.guild.id)

    def __send_message(self, interaction: Interaction, message: str, ephemeral: bool = False, delete_after: int = 0):
        return interaction.response.send_message(
            embed=self.__embed.send(message),
            ephemeral=ephemeral,
            delete_after=delete_after
        )

    async def __send_error_events(self, guild_id: int, mess: str):

        channel: discord.TextChannel = await self.__bot.fetch_channel(
            self.__voice_state.get_channel_id(guild_id)
        )

        await channel.send(
            embed=self.__embed.error(mess),
            delete_after=5
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
        await self.__voice_state.join(interaction, )
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
        await self.__voice_state.leave(interaction)
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
        if not tracks:
            raise TrackNotFoundError

        self.__voice_state.switch_auto_play_mode(interaction)

        if isinstance(tracks, list) and len(tracks) > 1:
            await interaction.response.send_message(
                'Seleziona una canzone...',
                view=SelectTrackView(
                    self.__voice_state,
                    interaction,
                    tracks,
                ),
                ephemeral=True
            )
        else:
            await self.__voice_state.play_and_send_feedback(
                interaction,
                tracks,
            )

    @app_commands.command(
        name='volume',
        description='Imposta il volume della canzone'
    )
    @app_commands.describe(
        volume='Valore da 0 a 1000'
    )
    @check_voice_channel()
    async def volume(self, interaction: Interaction, volume: app_commands.Range[int, 0, 1000]):
        await self.__voice_state.volume(interaction, volume)
        await self.__send_message(
            interaction,
            f'Volume impostato a {volume}',
            delete_after=5
        )

    @app_commands.command(
        name='seek',
        description='Cambia la posizione della canzone'
    )
    @app_commands.describe(
        position='Posizione in formato hh:mm:ss oppure in secondi'
    )
    @check_voice_channel()
    async def seek(self, interaction: Interaction, position: str):
        position = convert_time_to_ms(position)
        await self.__voice_state.seek(interaction, position)
        await self.__send_message(
            interaction,
            f'Posizione cambiata a {ms_to_time(position)}',
            delete_after=5
        )

    # --- --- --- --- --- ---#
    #                        #
    # --- QUEUE COMMANDS --- #
    #                        #
    # --- --- --- --- --- ---#

    @app_commands.command(
        name='remove',
        description='Rimuove una canzone dalla coda di riproduzione'
    )
    @app_commands.describe(
        index='Indice della canzone da rimuovere'
    )
    @check_voice_channel()
    async def remove(self, interaction: Interaction, index: int):
        track = self.__voice_state.remove(interaction, index)
        await interaction.response.send_message(
            embed=self.__embed.send(f"Rimosso {track.title} dalla coda di riproduzione"),
            ephemeral=True,
            delete_after=5
        )

    @app_commands.command(
        name='swap',
        description='Scambia due canzoni nella coda di riproduzione'
    )
    @app_commands.describe(
        index1='Indice della prima canzone',
        index2='Indice della seconda canzone'
    )
    @check_voice_channel()
    async def swap(self, interaction: Interaction, index1: int, index2: int):
        tracks = self.__voice_state.swap(interaction, index1, index2)
        await interaction.response.send_message(
            embed=self.__embed.send(f"Scambiato {tracks[0].title} con {tracks[1].title}"),
            ephemeral=True,
            delete_after=5
        )

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
    @volume.error
    @seek.error
    async def play_error(self, interaction: Interaction, error: ext.commands.CommandError):
        if not await self.__check_channel(interaction, error):
            pass
        elif isinstance(error, TrackNotFoundError):
            await self.__send_error(interaction, 'Canzone non trovata')
        elif isinstance(error, ValueError):
            await self.__send_error(interaction, 'Valore non valido')
        elif isinstance(error, InvalidSeekTime):
            await self.__send_error(interaction, 'Posizione non valida')
        elif isinstance(error, TrackNotSeekable):
            await self.__send_error(interaction, 'Non puoi cambiare la posizione di questa canzone')
        elif isinstance(error, InvalidFormat):
            await self.__send_error(interaction, 'Formato non valido')
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

    # --- QUEUE ERROR HANDLING --- #


    @remove.error
    @swap.error
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

async def setup(bot: ext.commands.Bot):
    await bot.add_cog(
        Music(bot),
        guilds=[
            Object(id=928785387239915540)
        ]
    )

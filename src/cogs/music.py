"""
This module contains the music commands and event listeners for the SusanoMusicBot.
"""

from discord import Object, Interaction, app_commands, ext
from discord.ext import commands
import wavelink
import discord

from src.music_ui.player.player_view import PlayerView
from src.music_ui.track_select.track_select_view import SelectTrackView

from src.utils.utils import check_player
from src.utils.embed import EmbedFactory

from src.checks.voice_channel_check import check_voice_channel

from src.voice.guild_voice_state import GuildVoiceState

from src.exceptions.player_exceptions import TrackNotFound, IllegalState
from src.exceptions.voice_channel_exceptions import (
    UserNotInVoiceChannel,
    BotAlreadyInVoiceChannel,
    BotNotInVoiceChannel,
    UserNotInSameVoiceChannel
)

class Music(ext.commands.Cog):
    """
    The Music cog for the SusanoMusicBot.
    """
    def __init__(self, bot: commands.Bot):
        self.__bot: commands.Bot = bot
        self.__voice_state = GuildVoiceState()
        self.__embed = EmbedFactory()

    @commands.Cog.listener()
    async def on_wavelink_websocket_closed(self, payload: wavelink.WebsocketClosedEventPayload):
        """
        Event listener for the wavelink websocket closed event.

        Args:
            payload:

        Returns:

        """
        print(f"Websocket chiuso: {payload.code} {payload.reason}")
        if check_player(payload.player):
            await self.__voice_state.guild_clean_up(payload.player.guild.id)

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, payload: wavelink.NodeReadyEventPayload) -> None:
        """
        Event listener for the wavelink node ready event

        Args:
            payload:

        Returns:

        """
        print(f"Nodo {payload.node!r} is ready!")

    @commands.Cog.listener()
    async def on_wavelink_track_stuck(self, payload: wavelink.TrackStuckEventPayload) -> None:
        """
        Event listener for the wavelink track stuck event.

        Args:
            payload:

        Returns:

        """
        if check_player(payload.player):
            print("Track stuck:", payload.threshold, payload.track.title)
            await self.__send_error_events(
                payload.player.guild.id,
                'Canzone bloccata, passando alla prossima',
            )
            #await self.__voice_state.play_next(payload.player.guild.id)

    @commands.Cog.listener()
    async def on_wavelink_track_exception(self, payload: wavelink.TrackExceptionEventPayload) -> None:
        """
        Event listener for the wavelink track exception event.

        Args:
            payload:

        Returns:

        """
        if check_player(payload.player):
            print("Track exception:", payload.exception, payload.track.title)
            await self.__send_error_events(
                payload.player.guild.id,
                'Errore durante la riproduzione della canzone, passando alla prossima',
            )
            #await self.__voice_state.play_next(payload.player.guild.id)

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload) -> None:
        """
        Event listener for the wavelink track start event

        Args:
            payload:

        Returns:

        """
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
        """
        Event listener for the wavelink track end event.

        Args:
            payload:

        Returns:

        """
        if check_player(payload.player):
            print('Fine canzone', payload.track.title, 'Motivo:', payload.reason)
            #await self.__voice_state.play_next(payload.player.guild.id)

    @commands.Cog.listener()
    async def on_wavelink_inactive_player(self, player: wavelink.Player):
        """
        Event listener for the wavelink inactive player event.

        Args:
            player:

        Returns:

        """
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

    async def __send_error_events(self, guild_id: int, mess: str) -> None:
        """
        Send an error message to the channel.

        Args:
            guild_id (int): The guild id.
            mess (str): The message to send.

        Returns:
            None
        """
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
    @app_commands.describe(
        auto_queue='Abilita la modalità auto-queue'
    )
    @app_commands.choices(
        auto_queue=[
            app_commands.Choice(name='Si', value=1),
        ]
    )
    @check_voice_channel()
    async def join(self, interaction: Interaction, auto_queue: app_commands.Choice[int] = 0):
        """
        Command to make the bot join the voice channel.

        Args:
            interaction:
            auto_queue:

        Returns:

        """
        await self.__voice_state.join(interaction, inactive_time=180, auto_queue=bool(auto_queue))
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
        """
        Command to make the bot leave the voice channel.

        Args:
            interaction:

        Returns:

        """
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
        """
        Command to play a song.

        Args:
            interaction:
            search:

        Returns:

        """
        tracks: wavelink.Search = await wavelink.Playable.search(search)
        if not tracks:
            raise TrackNotFound

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

    # --- CHECKS --- #

    def __send_error(self, interaction: Interaction, error: str):
        return interaction.response.send_message(
            embed=self.__embed.error(error),
            ephemeral=True,
            delete_after=5
        )

    # --- PLAYER ERROR HANDLING --- #

    async def __check_channel(self, interaction: Interaction, error: ext.commands.CommandError) -> bool:
        """
        Check the voice channel and send the error message.

        Args:
            interaction:
            error:

        Returns:

        """
        if isinstance(error, UserNotInVoiceChannel):
            await self.__send_error(interaction, 'Devi essere connesso a un canale vocale')
        elif isinstance(error, BotNotInVoiceChannel):
            await self.__send_error(interaction, 'Il bot non è connesso a un canale vocale')
        elif isinstance(error, UserNotInSameVoiceChannel):
            await self.__send_error(interaction, 'Devi essere nello stesso canale vocale del bot')
        elif isinstance(error, IllegalState):
            await self.__send_error(interaction, 'Comando non valido')
        else:
            return True
        return False

    @play.error
    async def play_error(self, interaction: Interaction, error: ext.commands.CommandError):
        """
        Error handler for the play command.

        Args:
            interaction:
            error:

        Returns:

        """
        if not await self.__check_channel(interaction, error):
            pass
        elif isinstance(error, TrackNotFound):
            await self.__send_error(interaction, 'Canzone non trovata')
        else:
            print(error)
            await self.__send_error(interaction, 'Errore sconosciuto')

    @leave.error
    async def leave_error(self, interaction: Interaction, error: ext.commands.CommandError):
        """
        Error handler for the leave command.

        Args:
            interaction:
            error:

        Returns:

        """
        if not await self.__check_channel(interaction, error):
            pass
        else:
            print(error)
            await self.__send_error(interaction, 'Errore sconosciuto')

    @join.error
    async def join_error(self, interaction: Interaction, error: ext.commands.CommandError):
        """
        Error handler for the join command.

        Args:
            interaction:
            error:

        Returns:

        """
        if isinstance(error, UserNotInVoiceChannel):
            await self.__send_error(interaction, 'Devi essere connesso a un canale vocale')
        elif isinstance(error, BotAlreadyInVoiceChannel):
            await self.__send_error(interaction, 'Il bot è già connesso a un canale vocale')
        else:
            print(error)
            await self.__send_error(interaction, 'Errore sconosciuto')


async def setup(bot: ext.commands.Bot):
    """
    Set up the Music cog.

    Args:
        bot:

    Returns:

    """
    await bot.add_cog(
        Music(bot),
        guilds=[
            Object(id=928785387239915540)
        ]
    )

import discord
from discord import Object, Interaction, app_commands, ext
from discord.ext import commands


from src.ui import QueueUI
from src.ui.SelectUI import SelectTrackView

from src.exceptions.Generic import Generic
from src.exceptions.PlayerExceptions import NoCurrentTrack, AlreadyPaused, AlreadyResumed, IllegalState
from src.exceptions.QueueException import QueueEmpty, AlreadyLoop, AlreadyLoopAll
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
    async def on_wavelink_track_stuck(self, payload: wavelink.TrackStuckEventPayload) -> None:
        await self.__send_error(
            payload,
            'Canzone bloccata, passando alla prossima',
            delete_after=5
        )
        await self.__VoiceState.play_next(payload.player.guild.id)

    @commands.Cog.listener()
    async def on_wavelink_track_exception(self, payload: wavelink.TrackExceptionEventPayload) -> None:
        ...

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload) -> None:
        if "first" not in dir(payload.track.extras):
            channel: discord.TextChannel = await self.__bot.fetch_channel(
                self.__VoiceState.get_channel_id(payload.player.guild.id)
            )

            message: discord.Message = await channel.send(
                embed=self.__embed.now_playing_with_player(payload.player)
            )

            self.__VoiceState.set_last_message(
                payload.player.guild.id,
                message
            )

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload) -> None:
        if payload.player.connected:
            await self.__VoiceState.clear_now_playing(payload.player.guild.id)
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
        await self.__VoiceState.clear_now_playing(interaction.guild_id)
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
        if not tracks:
            raise TrackNotFoundError
        if isinstance(tracks, list) and len(tracks) > 1:
            await interaction.response.send_message(
                'Seleziona una canzone...',
                view=SelectTrackView(
                    interaction,
                    self.__VoiceState,
                    tracks
                ),
                ephemeral=True
            )
        else:
            track_playing, tracks_queue = await self.__VoiceState.play(interaction, tracks)
            await self.__VoiceState.feedback_play_command(
                interaction,
                track_playing,
                tracks_queue
            )

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
        await self.__VoiceState.update_now_playing(interaction.guild_id)

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
        await self.__VoiceState.update_now_playing(interaction.guild_id)

    # --- --- --- --- --- ---#
    #                        #
    # --- QUEUE COMMANDS --- #
    #                        #
    # --- --- --- --- --- ---#

    @app_commands.command(
        name='reset',
        description='Resetta la coda delle canzoni'
    )
    @check_voice_channel()
    async def reset(self, interaction: Interaction):
        await self.__VoiceState.reset(interaction)
        await interaction.response.send_message(
            embed=self.__embed.send('Coda resettata'),
            ephemeral=True,
            delete_after=5
        )

    @app_commands.command(
        name='loop',
        description='Ripete la canzone attuale'
    )
    @check_voice_channel()
    async def loop(self, interaction: Interaction):
        loop = await self.__VoiceState.loop(interaction)
        await interaction.response.send_message(
            embed=self.__embed.send(f"Loop {"attivato" if loop else "disattivato"}" ),
            ephemeral=True,
            delete_after=5
        )
        await self.__VoiceState.update_now_playing(interaction.guild_id)

    @app_commands.command(
        name='loop_all',
        description='Ripete tutte le canzoni'
    )
    @check_voice_channel()
    async def loop_all(self, interaction: Interaction):
        loop = await self.__VoiceState.loop_all(interaction)
        await interaction.response.send_message(
            embed=self.__embed.send(f"Loop all {"attivato" if loop else "disattivato"}" ),
            ephemeral=True,
            delete_after=5
        )
        await self.__VoiceState.update_now_playing(interaction.guild_id)

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
        name='remove',
        description='Rimuove una canzone dalla coda'
    )
    @app_commands.describe(
        index='Indice della canzone da rimuovere'
    )
    @check_voice_channel()
    async def remove(self, interaction: Interaction, index: int):
        track = await self.__VoiceState.remove(interaction, index)
        await interaction.response.send_message(
            embed=self.__embed.send(f"Rimosso {track.title} dalla coda"),
            ephemeral=True,
            delete_after=5
        )

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
        tracks = await self.__VoiceState.swap(interaction, index1, index2)
        await interaction.response.send_message(
            embed=self.__embed.send(f"Scambiato {tracks[0].title} con {tracks[1].title}"),
            ephemeral=True,
            delete_after=5
        )

    @app_commands.command(
        name='queue',
        description='Mostra la coda delle canzoni'
    )
    @check_voice_channel()
    async def queue(self, interaction: Interaction):
        interaction_queue, followup_queues = await self.__VoiceState.queue(interaction)

        await interaction.response.send_message(
            embed=self.__embed.queue(interaction_queue, 1, len(followup_queues) + 1),
        )

        for i, queue in enumerate(followup_queues, 2):
            await interaction.channel.send(
                embed=self.__embed.queue(queue, i, len(followup_queues) + 1)
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

    @queue.error
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

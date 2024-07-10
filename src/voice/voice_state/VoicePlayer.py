import discord
import wavelink
from discord import Interaction
from discord.ext import commands

from src.ui.QueueUI import QueueView
from src.utils.embed import EmbedFactory
from src.voice.guild_data.GuildMusicData import GuildMusicData

from src.exceptions.PlayerExceptions import AlreadyPaused, AlreadyResumed, NoCurrentTrack, AlreadyLoop, AlreadyLoopAll, \
    QueueEmpty


class VoicePlayer:
    def __init__(self, bot: commands.Bot):
        self.__bot: commands.Bot = bot
        self.__embed = EmbedFactory()

    async def display_now_playing(self, guild_state: GuildMusicData, payload: wavelink.TrackStartEventPayload):
        channel: discord.TextChannel = await self.__bot.fetch_channel(
            guild_state.channel_id
        )
        await channel.send(
            embed=self.__embed.now_playing(payload.track)
        )

    @staticmethod
    async def leave(guild_state: GuildMusicData):
        await guild_state.player.disconnect(force=True)

    async def play(self, guild_state: GuildMusicData, interaction: Interaction, tracks: wavelink.Search) -> None:
        if not guild_state.player.current:
            await guild_state.player.play(tracks.pop(0))
            if isinstance(tracks, wavelink.Playlist) or len(tracks) > 1:
                await interaction.response.send_message(
                    embed=self.__embed.added_to_queue(tracks, interaction.user)
                )
                guild_state.player.queue.put(tracks)
            else:
                await interaction.response.send_message(
                    embed=self.__embed.added_to_queue([guild_state.player.current], interaction.user),
                    ephemeral=True,
                    delete_after=5
                )
        else:
            await interaction.response.send_message(
                embed=self.__embed.added_to_queue(tracks, interaction.user)
            )
            guild_state.player.queue.put(tracks)

    async def skip(self, guild_state: GuildMusicData):
        if not await guild_state.player.skip():
            raise NoCurrentTrack

    @staticmethod
    async def pause(guild_state: GuildMusicData):

        if not guild_state.player.current:
            raise NoCurrentTrack

        if guild_state.player.paused:
            raise AlreadyPaused

        await guild_state.player.pause(True)

    @staticmethod
    async def resume(guild_state: GuildMusicData):

        if not guild_state.player.current:
            raise NoCurrentTrack

        if not guild_state.player.paused:
            raise AlreadyResumed

        await guild_state.player.pause(False)

    async def loop(self, guild_state: GuildMusicData, interaction: Interaction):
        queue = guild_state.player.queue

        if not guild_state.player.current:
            raise NoCurrentTrack

        if queue.mode == "loop_all":
            raise AlreadyLoopAll

        if queue.mode == "normal":
            queue.mode = "loop"
            await interaction.response.send_message(
                embed=self.__embed.send("Loop attivito")
            )
        elif queue.mode == "loop":
            queue.mode = "normal"
            await interaction.response.send_message(
                embed=self.__embed.send("Loop disattivato")
            )

    async def loop_all(self, guild_state: GuildMusicData, interaction: Interaction):
        queue = guild_state.player.queue

        if not guild_state.player.current:
            raise NoCurrentTrack

        if queue.mode == "loop":
            raise AlreadyLoopAll

        if queue.mode == "normal":
            queue.mode = "loop_all"
            await interaction.response.send_message(
                embed=self.__embed.send("Loop All attivito")
            )
        elif queue.mode == "loop_all":
            queue.mode = "normal"
            await interaction.response.send_message(
                embed=self.__embed.send("Loop All disattivato")
            )

    @staticmethod
    async def shuffle(guild_state: GuildMusicData):
        queue = guild_state.player.queue

        if queue.is_empty:
            raise QueueEmpty

        queue.shuffle()

    @staticmethod
    async def reset(guild_state: GuildMusicData):
        queue = guild_state.player.queue

        if queue.is_empty:
            raise QueueEmpty

        queue.reset()

    async def remove(self, guild_state: GuildMusicData, interaction: Interaction, index: int):
        queue = guild_state.player.queue

        if queue.is_empty:
            raise QueueEmpty

        if index < 0 or index >= len(queue):
            raise IndexError

        track = queue.peek(index)
        queue.delete(index)

        await interaction.response.send_message(
            embed=self.__embed.send(f"Rimosso {track.title} dalla coda"),
            delete_after=5
        )

    async def swap(self, guild_state: GuildMusicData, interaction: Interaction, index1: int, index2: int):
        queue = guild_state.player.queue

        if queue.is_empty:
            raise QueueEmpty

        if index1 != index2 and (index1 < 0 or index1 >= len(queue) or index2 < 0 or index2 >= len(queue)):
            raise IndexError

        tracks = queue.peek(index1), queue.peek(index2)

        queue.swap(index1, index2)

        await interaction.response.send_message(
            embed=self.__embed.send(f"Scambiato {tracks[0].title} con {tracks[1].title}"),
            delete_after=5
        )

    async def queue(self, guild_state: GuildMusicData, interaction: Interaction):
        queue = guild_state.player.queue

        if queue.is_empty:
            raise QueueEmpty

        view = QueueView(interaction, queue)

        await interaction.response.send_message(
            embed=self.__embed.send("Queue"),
            view=view,
            ephemeral=True
        )

    @staticmethod
    async def play_next(guild_state: GuildMusicData):
        player: wavelink.Player = guild_state.player
        if not player.queue.is_empty:
            await player.play(player.queue.get())

    async def inactive_player(self, guild_state: GuildMusicData):
        await self.leave(guild_state)

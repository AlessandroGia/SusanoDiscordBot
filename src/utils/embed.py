from typing import Optional

import wavelink
import discord
from discord import User
from discord.ext import commands
from src.utils.utils import convert_time
from src.utils.utils import convert_time


class EmbedFactory:
    def __init__(self):
        self.__bot_name = "Susano"
        self.__icon_url = "https://webcdn.hirezstudios.com/smite/god-icons/susano.jpg"

    def error(self, error: str) -> discord.Embed:
        embed = discord.Embed(
            title=" ",
            description=f"***{error}***",
            color=discord.Color.red()
        )
        embed.set_author(
            name=self.__bot_name,
            icon_url=self.__icon_url
        )
        return embed

    def send(self, message: str) -> discord.Embed:
        embed = discord.Embed(
            title=" ",
            description=f"***{message}***",
            color=discord.Color.green()
        )
        embed.set_author(
            name=self.__bot_name,
            icon_url=self.__icon_url
        )
        return embed

    def queue(self, queue_str: str, page: int, num_pages: int) -> discord.Embed:

        embed = discord.Embed(
            title=f"Coda di Riproduzione - Pagina {page}",
            description=queue_str,
            color=discord.Color.blue()
        )
        embed.set_footer(
            text=f"Pagina {page} " + f"di {num_pages}" if num_pages > 1 else "",
        )
        embed.set_author(
            name=self.__bot_name,
            icon_url=self.__icon_url
        )
        return embed

    def now_playing_and_added_to_queue_with_player(self, tracks: wavelink.Search, player: wavelink.Player):
        embed = self.now_playing_with_player(player)
        embed.add_field(
            name="Aggiunte:",
            value=f"***{len(tracks)} {'tracce' if len(tracks) > 1 else 'traccia'}*** alla coda",
            inline=False
        )
        return embed

    def now_playing_and_added_to_queue(self, tracks: wavelink.Search, track: wavelink.Playable) -> discord.Embed:
        embed = self.now_playing(track)
        embed.add_field(
            name="Aggiunte:",
            value=f"***{len(tracks)} {'tracce' if len(tracks) > 1 else 'traccia'}*** alla coda",
            inline=False
        )
        return embed

    def now_playing_with_player(self, player: wavelink.Player) -> discord.Embed:

        state = "⏸️" if player.paused else "▶️"
        loop = "🔁" if player.queue.mode == wavelink.QueueMode.loop else "🔂" if player.queue.mode == wavelink.QueueMode.loop_all else ""
        embed = self.now_playing(player.current)

        embed.add_field(
            name="Player:",
            value=f"{state} {loop}",
            inline=False
        )

        return embed

    def finished_playing(self, track: wavelink.Playable) -> discord.Embed:
        embed = self.now_playing(track)

        # embed.add_field(
        #     name="Player:",
        #     value="⏹️",
        #     inline=False
        # )

        return embed

    def now_playing(self, track: wavelink.Playable) -> discord.Embed:

        embed = discord.Embed(
            title="Riproducendo",
            description=f"> [{track.title}]({track.uri})",
            color=discord.Color.blurple()
        )
        embed.set_thumbnail(url=track.artwork) if track.artwork else None
        embed.add_field(
            name="Autore:",
            value=f"***{track.author}***",
            inline=True
        ) if track.author else None
        embed.add_field(
            name="Playlist:",
            value=f"***{track.playlist.name}***",
        ) if track.playlist else None
        embed.add_field(
            name="Durata:",
            value=f"***{convert_time(track.length)}***",
            inline=True
        ) if track.length else None
        embed.set_author(
            name=self.__bot_name,
            icon_url=self.__icon_url
        )

        embed.set_footer(
            text=track.extras.requester_name,
            icon_url=track.extras.requester_avatar
        )

        return embed

    def added_to_queue(self, tracks: wavelink.Search, author: User) -> discord.Embed:

        if isinstance(tracks, wavelink.Playlist):
            title = "Aggiunto alla coda"
            description = f"> [{tracks.name}]({tracks.url})" if tracks.url else f"> {tracks.name}"
            thumbnail = tracks.artwork if tracks.artwork else None
            _author = f"***{tracks.author}***"
        else:
            title = "Aggiunte alla coda" if len(tracks) > 1 else "Aggiunta alla coda"
            description = f"> [{tracks[0].title}]({tracks[0].uri})" if len(tracks) == 1 else None
            thumbnail = tracks[0].artwork if len(tracks) == 1 and tracks[0].artwork else None
            _author = f"***{tracks[0].author}***"

        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.green()
        )

        embed.set_thumbnail(url=thumbnail)

        embed.add_field(
            name="Autore:",
            value=_author,
            inline=True
        ) if (isinstance(tracks, wavelink.Playlist) and tracks.author) or (len(tracks) == 1 and tracks[0].author) else None

        embed.add_field(
            name="Durata:",
            value=f"***{convert_time(tracks[0].length)}***",
            inline=True
        ) if not isinstance(tracks, wavelink.Playlist) and len(tracks) == 1 else None
        [
            embed.add_field(
                name=f"Traccia {index + 1}:",
                value=f"***[{track.title}]({track.uri})***",
                inline=False
            ) for index, track in enumerate(tracks)
        ] if not isinstance(tracks, wavelink.Playlist) and len(tracks) > 1 else None

        embed.add_field(
            name="Aggiunte:",
            value=f"***{len(tracks.tracks)} {'tracce' if len(tracks.tracks) > 1 else 'traccia'}***",
            inline=True
        ) if isinstance(tracks, wavelink.Playlist) else None

        embed.set_author(
            name=self.__bot_name,
            icon_url=self.__icon_url
        )
        embed.set_footer(
            text=author.name,
            icon_url=author.display_avatar
        )
        return embed
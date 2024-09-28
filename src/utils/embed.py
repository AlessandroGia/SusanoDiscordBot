from dis import disco
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

    def now_playing(self, track: wavelink.Playable) -> discord.Embed:

        embed = discord.Embed(
            title="🎶 In Riproduzione",
            description=f"> [{track.title}]({track.uri})",
            color=discord.Color.blurple()
        )
        embed.set_thumbnail(url=track.artwork) if track.artwork else None
        embed.add_field(
            name="👤 Autore:",
            value=f"***{track.author}***",
            inline=True
        ) if track.author else None
        embed.add_field(
            name="📀 Playlist:",
            value=f"***{track.playlist.name}***",
        ) if track.playlist else None
        embed.add_field(
            name="⏱️ Durata:",
            value=f"***{convert_time(track.length)}***",
            inline=True
        ) if track.length else None

        icon_url = None

        if track.source == "youtube":
            icon_url = "https://cdn3.iconfinder.com/data/icons/social-network-30/512/social-06-512.png"
        elif track.source == "spotify":
            icon_url = "https://storage.googleapis.com/pr-newsroom-wp/1/2023/05/Spotify_Primary_Logo_RGB_Green.png"

        embed.set_author(
            name=track.source.capitalize(),
            icon_url=icon_url
        )
        embed.set_footer(
            text=track.extras.requester_name if "requester_name" in dir(track.extras) else "🌟 Consigliata",
            icon_url=track.extras.requester_avatar if "requester_avatar" in dir(track.extras) else None
        )

        return embed

    def added_to_queue(self, tracks: wavelink.Search, author: User, skip_first_track: bool = False) -> discord.Embed:

        if isinstance(tracks, wavelink.Playlist):
            embed = self.__added_to_queue_playlist(tracks, skip_first_track)
        else:
            embed = self.__added_to_queue_list(tracks, skip_first_track)

        embed.set_author(
            name=self.__bot_name,
            icon_url=self.__icon_url
        )
        embed.set_footer(
            text=author.name,
            icon_url=author.display_avatar
        )
        return embed

    @staticmethod
    def __added_to_queue_playlist(tracks: wavelink.Playlist, skip_first_track: bool) -> discord.Embed:

        embed = discord.Embed(
            title="📀 Playlist aggiunta alla coda",
            description=f"> [{tracks.name}]({tracks.url})" if tracks.url else f"> {tracks.name}",
            color=discord.Color.green()
        )

        embed.set_thumbnail(url=tracks.artwork) if tracks.artwork else None

        embed.add_field(
            name="👤 Autore:",
            value=f"***{tracks.author}***",
            inline=True
        ) if tracks.author else None

        num_tracks = len(tracks.tracks) if not skip_first_track else len(tracks.tracks) - 1

        embed.add_field(
            name="🎵 Aggiunte:" if num_tracks > 1 else "🎵 Aggiunta:",
            value=f"***{num_tracks} {'tracce' if num_tracks > 1 else 'traccia'}***",
            inline=True
        )

        return embed

    @staticmethod
    def __added_to_queue_list(tracks: wavelink.Search, skip_first_track: bool) -> discord.Embed:

        if skip_first_track:
            tracks = tracks[1:]

        embed = discord.Embed(
            title="📋 Tracce aggiunte alla coda" if len(tracks) > 1 else "📋 Traccia aggiunta alla coda",
            description=f"> [{tracks[0].title}]({tracks[0].uri})" if len(tracks) == 1 else None,
            color=discord.Color.green()
        )

        embed.set_thumbnail(url=tracks[0].artwork) if len(tracks) == 1 and tracks[0].artwork else None

        embed.add_field(
            name="👤 Autore:",
            value=f"***{tracks[0].author}***",
            inline=True
        ) if len(tracks) == 1 and tracks[0].author else None

        embed.add_field(
            name="⏱️ Durata:",
            value=f"***{convert_time(tracks[0].length)}***",
            inline=True
        ) if len(tracks) == 1 else None

        [
            embed.add_field(
                name=f"🎵 Traccia {index}:",
                value=f"***[{track.title}]({track.uri})***",
                inline=False
            ) for index, track in enumerate(tracks, start=1)
        ] if len(tracks) > 1 else None

        return embed

class EmbedQueue:
    def __init__(self, num_tracks: int, max_page: int, track_per_page: int):
        self.num_tracks = num_tracks
        self.max_page = max_page
        self.track_per_page = track_per_page

    def queue(self, queue: list[wavelink.Playable], current_page: int) -> discord.Embed:
        embed = discord.Embed(
            title="📋 Coda",
            description=f"**{self.num_tracks} {'tracce' if self.num_tracks > 1 else 'traccia'} nella coda**",
            color=discord.Color.green()
        )

        for index, track in enumerate(queue[:25], start=(current_page - 1) * self.track_per_page + 1):
            embed.add_field(
                name=f"{index}. 🎵 {track.title}",
                value=f"**Autore**: {track.author} | **Durata**: {convert_time(track.length)}{' 🌟 Consigliata' if track.recommended else ''}" ,
                inline=False
            )

        embed.set_footer(
            text=f"Pagina {current_page}/{self.max_page}"
        ) if self.max_page > 1 else None

        return embed

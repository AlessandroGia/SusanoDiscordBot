import wavelink
import discord
from discord import User
from discord.ext import commands
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
            name="Durata:",
            value=f"***{convert_time(track.length)}***",
            inline=True
        ) if track.length else None
        embed.set_author(
            name=self.__bot_name,
            icon_url=self.__icon_url
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
"""
This module contains the SusanoMusicBot class, which is a custom
implementation of a Discord bot using the discord.py library.
"""

import logging
import os

from wavelink import AuthorizationFailedException, InvalidClientException, NodeException
from discord import Intents, Object, Status, Activity, ActivityType
from discord.ext import commands
import wavelink


from config import setup_logging, discord_token, lava_host, lava_password, lava_port


class SusanoMusicBot(commands.Bot):
    """
    A custom Discord bot class that handles bot initialization,
    node creation, cog loading, and event handling.
    """
    def __init__(self) -> None:
        setup_logging()
        super().__init__(
            command_prefix='!',
            intents=Intents.all(),
            status=Status.do_not_disturb,
            activity=Activity(
                type=ActivityType.listening,
                name='Broken music'
            )
        )

    @staticmethod
    def __create_node() -> wavelink.Node:
        """
        Creates a LavaLink node using the environment variables.
        :return:
        """
        return wavelink.Node(
            uri=f'http://{lava_host}:{lava_port}',
            password=lava_password,
        )

    async def __load_cogs(self) -> None:
        """
        Loads all cogs from the src/cogs directory.
        :return:
        """
        for filename in os.listdir(os.path.join(os.path.dirname(__file__), 'src', 'cogs')):
            if filename.endswith('.py') and filename != '__init__.py':
                await self.load_extension(f'src.cogs.{filename[:-3]}')

    async def __connect_nodes(self, nodes: wavelink.Node) -> None:
        """
        Connects the bot to the specified LavaLink nodes.
        :param nodes:
        :return:
        """
        if isinstance(nodes, wavelink.Node):
            nodes = [nodes]
        try:
            await wavelink.Pool.connect(
                nodes=nodes,
                client=self
            )
        except AuthorizationFailedException:
            logging.error('Failed to authenticate with nodes')
        except InvalidClientException:
            logging.error('Invalid client provided to connect to nodes')
        except NodeException:
            logging.error('Failed to connect to nodes')

    async def on_ready(self) -> None:
        """
        Event handler for when the bot is ready.
        :return:
        """
        await self.tree.sync(
            guild=Object(id=928785387239915540)
        )
        logging.info('Logged in as %s', self.user)

    async def setup_hook(self) -> None:
        """
        Initializes the bot by creating a node, connecting to the node, and loading cogs.
        :return:
        """
        node = self.__create_node()
        await self.__connect_nodes(node)
        await self.__load_cogs()


if __name__ == '__main__':
    bot = SusanoMusicBot()
    bot.run(discord_token)

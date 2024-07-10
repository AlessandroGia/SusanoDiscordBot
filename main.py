from config import setup_logging, discord_token, lava_host, lava_password, lava_port
from discord import Intents, Object, Status, Activity, ActivityType
from logging.handlers import TimedRotatingFileHandler
from discord.ext import commands
from dotenv import load_dotenv

import wavelink
import logging
import os


class SusanoMusicBot(commands.Bot):
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
        return wavelink.Node(
            uri=f'http://{lava_host}:{lava_port}',
            password=os.getenv('LAVA_PASSWORD'),
        )

    async def __load_cogs(self) -> None:
        for filename in os.listdir(os.path.join(os.path.dirname(__file__), 'src', 'cogs')):
            if filename.endswith('.py') and filename != '__init__.py':
                await self.load_extension(f'src.cogs.{filename[:-3]}')

    async def __connect_nodes(self, nodes: wavelink.Node) -> None:
        if isinstance(nodes, wavelink.Node):
            nodes = [nodes]
        try:
            await wavelink.Pool.connect(
                nodes=nodes,
                client=self
            )
        except Exception as e:
            logging.error(f'Error connecting to nodes: {e}')

    async def on_ready(self) -> None:
        await self.tree.sync(
            guild=Object(
                id=928785387239915540
            )
        )
        logging.info(f'Logged in as {self.user}')

    async def setup_hook(self) -> None:
        node = self.__create_node()
        await self.__connect_nodes(node)
        await self.__load_cogs()


if __name__ == '__main__':
    bot = SusanoMusicBot()
    bot.run(discord_token)

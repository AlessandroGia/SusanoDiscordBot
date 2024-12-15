
import wavelink
from discord.ui import Button, View, Item

from src.utils.embed import EmbedFactory, EmbedQueue

from src.music_ui.queue.items.buttons.directions import DirectionButton, Direction



class QueueView(View):
    def __init__(self, queue: wavelink.Queue, embed: EmbedQueue):
        super().__init__()
        self.__queue = queue

        self.embed = embed
        self.current_page = 1

        self.back_button = Direction(DirectionButton.BACK)
        self.forward_button = Direction(DirectionButton.FORWARD)

        if embed.max_page > 1:
            self.add_item(self.back_button)
            self.add_item(self.forward_button)

        self.check()


    def get_tracks_by_page(self, page: int):
        return self.__queue[(page - 1) * self.embed.track_per_page: page * self.embed.track_per_page]

    def check(self):
        self.back_button.disabled = self.current_page <= 1
        self.forward_button.disabled = self.current_page >= self.embed.max_page


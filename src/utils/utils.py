from src.exceptions.Generic import InvalidFormat
import re

regex = re.compile(
    "[0-9]*|((([0-1]?[0-9])|(2[0-3])):)?[0-5]?[0-9]:[0-5]?[0-9]"
)


def convert_time(ms: int) -> str:
    if int(ms) < (24 * 60 * 60 * 1000):
        s, ms = divmod(ms, 1000)
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        return f"{m:02d}:{s:02d}" if h == 0 else f"{h:02d}:{m:02d}:{s:02d}"
    else:
        return "∞"


def convert_time_to_ms(time: str) -> int:
    if not regex.fullmatch(time):
        raise InvalidFormat

    s = lambda x: int(x) * 1000
    m = lambda x: int(x) * 60 * 1000
    h = lambda x: int(x) * 60 * 60 * 1000

    time = time.split(":")

    if len(time) == 1:
        return s(time[0])

    if len(time) == 2:
        return m(time[0]) + s(time[1])

    return h(time[0]) + m(time[1]) + s(time[2])


def truncate_string(string: str, max_length: int) -> str:
    return string[:max_length - 4] + "..." if len(string) >= max_length else string


def check_player(player):
    return player and player.connected

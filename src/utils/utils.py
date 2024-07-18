

def convert_time(ms: int) -> str:
    if int(ms) < (24 * 60 * 60 * 1000):
        s, ms = divmod(ms, 1000)
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        return f"{m:02d}:{s:02d}" if h == 0 else f"{h:02d}:{m:02d}:{s:02d}"
    else:
        return "∞"


def truncate_string(string: str, max_length: int) -> str:
    return string[:max_length - 4] + "..." if len(string) >= max_length else string

from fake_useragent import UserAgent

_ua = UserAgent()


def get_user_agent() -> str:
    """Returns a random browser user agent string."""
    return _ua.random


def get_default_headers() -> dict[str, str]:
    """Returns default headers with a fake browser user agent."""
    return {"User-Agent": get_user_agent()}

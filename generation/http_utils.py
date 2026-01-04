from browserforge.headers import HeaderGenerator

# Generate consistent modern browser headers for this process
_header_generator = HeaderGenerator(browser="chrome")
_headers = dict(_header_generator.generate())


def get_user_agent() -> str:
    """Returns a consistent browser user agent string for this process."""
    return _headers.get("User-Agent", "")


def get_default_headers() -> dict[str, str]:
    """Returns default headers mimicking a real browser to avoid WAF blocks."""
    return _headers.copy()

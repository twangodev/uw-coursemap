from fake_headers import Headers

# Generate consistent browser headers for this process
_header_generator = Headers(browser="chrome", os="mac", headers=True)
_headers = _header_generator.generate()


def get_user_agent() -> str:
    """Returns a consistent browser user agent string for this process."""
    return _headers.get("User-Agent", "")


def get_default_headers() -> dict[str, str]:
    """Returns default headers mimicking a real browser to avoid WAF blocks."""
    return _headers

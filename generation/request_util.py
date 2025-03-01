from urllib.parse import urlparse

from urllib3 import Retry


def get_global_retry_strategy():
    return Retry(
        total=50,  # Total number of retries
        backoff_factor=1,  # Exponential backoff factor (e.g., 1, 2, 4 seconds)
        status_forcelist=[429, 500, 502, 503, 504],  # Retry on these HTTP status codes
        allowed_methods=["GET"]  # Methods to retry on (use allowed_methods instead of deprecated method_whitelist)
    )

def get_prefix(url: str) -> str:
    """
    Extracts and returns the prefix (scheme and network location) from a given URL.

    This function parses the input URL and constructs a prefix that includes the URL's
    scheme (e.g., 'http', 'https') and network location (domain), ensuring the result
    ends with a trailing slash. This can be useful for mounting adapters or reusing
    connections for all URLs within the same domain.

    Parameters:
        url (str): The URL from which to extract the prefix.

    Returns:
        str: The prefix in the format '<scheme>://<netloc>/'.

    Example:
        >>> get_prefix("https://example.com/path/to/resource")
        'https://example.com/'
    """
    parsed = urlparse(url)
    prefix = f"{parsed.scheme}://{parsed.netloc}/"
    return prefix

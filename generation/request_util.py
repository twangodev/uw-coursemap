from urllib3 import Retry


def get_global_retry_strategy():
    return Retry(
        total=50,  # Total number of retries
        backoff_factor=1,  # Exponential backoff factor (e.g., 1, 2, 4 seconds)
        status_forcelist=[429, 500, 502, 503, 504],  # Retry on these HTTP status codes
        allowed_methods=[
            "GET"
        ],  # Methods to retry on (use allowed_methods instead of deprecated method_whitelist)
    )

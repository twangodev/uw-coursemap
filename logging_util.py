import logging

def get_logging_level(level_name):
    if level_name is None:
        return None
    try:
        return getattr(logging, level_name.upper())
    except AttributeError:
        raise ValueError(f"Invalid logging level: {level_name}")


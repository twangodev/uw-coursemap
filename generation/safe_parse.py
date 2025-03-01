def safe_int(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        return None

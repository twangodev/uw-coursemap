from aiohttp_client_cache import SQLiteBackend

_aio_cache_config = {
    "cache_name": None,
    "expire_after": -1,
    "allowed_methods": ('GET', 'POST')
}

def set_aio_cache_location(location):
    _aio_cache_config["cache_name"] = location

def set_aio_cache_expiration(expire_after):
    _aio_cache_config["expire_after"] = expire_after

def get_aio_cache():
    if _aio_cache_config["cache_name"] is None:
        raise ValueError("AIO cache location not set")
    return SQLiteBackend(**_aio_cache_config)
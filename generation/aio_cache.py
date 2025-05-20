aio_backend_cache = None

def get_aio_cache():
    if aio_backend_cache is None:
        raise ValueError("aio_backend_cache is not initialized")
    return aio_backend_cache

def set_aio_cache(cache):
    global aio_backend_cache
    aio_backend_cache = cache

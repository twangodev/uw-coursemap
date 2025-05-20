from diskcache import Cache

import instructors

def memoize_functions(cache_dir):
    cache = Cache(cache_dir)

    instructors.match_name = cache.memoize()(instructors.match_name)

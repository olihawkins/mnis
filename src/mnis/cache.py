"""The cache of downloaded data and the function to clear it"""

# Cache -----------------------------------------------------------------------

cache: dict = {}
"""The cache of data downloaded from MNIS.

Each raw fetch function stores its results in the cache under one of the
cache keys in mnis.constants, and the functions that use those results take
them from the cache if they are there. This means the data for each query
is downloaded only once in a session.
"""


# Clear cache -----------------------------------------------------------------


def clear_cache() -> None:
    """Clear all data cached from MNIS.

    clear_cache empties the cache of data downloaded from MNIS. The cache
    lasts for the duration of a session, so data downloaded in a long
    running session does not reflect any changes made to MNIS after it was
    downloaded. Call this function to discard the cached data: subsequent
    calls to the fetch functions download the data again.
    """
    cache.clear()

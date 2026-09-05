"""Package settings and the functions to change them"""

# Imports ---------------------------------------------------------------------

from mnis.constants import API_TIMEOUT
from mnis.errors import timeout_error

# Settings --------------------------------------------------------------------

settings: dict = {"timeout": API_TIMEOUT}
"""The current value of each package setting.

Settings apply for the duration of a session. Use the functions in this
module to read and change them rather than modifying this dict directly.
"""

# Timeout ---------------------------------------------------------------------

def get_timeout() -> float:
    """Return the number of seconds to wait for a response from MNIS.

    :return: The current timeout in seconds.
    """
    return settings["timeout"]


def set_timeout(timeout: float) -> None:
    """Set the number of seconds to wait for a response from MNIS.

    set_timeout changes how long each request to the MNIS API waits for a
    response before giving up. The default is 20 seconds, which suits most
    connections. Raise it on a slow connection to stop requests timing out
    before the data arrives, or lower it on a fast one to fail sooner. The
    setting applies to every request made for the rest of the session.

    A request that times out is retried, so the time a failing request takes
    in total is longer than the timeout.

    :param timeout: The timeout in seconds. This must be a positive number.
    """
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)):
        raise ValueError(timeout_error(timeout))

    if timeout <= 0:
        raise ValueError(timeout_error(timeout))

    settings["timeout"] = timeout

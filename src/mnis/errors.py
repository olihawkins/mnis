"""Package errors"""

# Errors ----------------------------------------------------------------------

def missing_column_error(colname: str) -> str:
    """Report an error handling dataframes with missing columms.

    :param colname: The name of the column that could not be found.
    """
    return f"Could not find a column called {colname}"


def date_format_error(date_str: object) -> str:
    """Report an error parsing a date string.

    :param date_str: The date string that could not be parsed.
    """
    return (
        f"{date_str} is not a valid Date or "
        'date string: use format "YYYY-MM-DD"'
    )


def timeout_error(timeout: object) -> str:
    """Report an error setting the timeout.

    :param timeout: The value that could not be used as a timeout.
    """
    return f"{timeout!r} is not a valid timeout: use a positive number"


def retry_error(attempts: int, reason: str) -> str:
    """Report an error from repeated failed API calls.

    :param attempts: The number of attempts that were made.
    :param reason: The reason the final attempt failed.
    """
    return (
        f"The request to the API failed after {attempts} attempts. "
        f"The last attempt failed because: {reason}"
    )


def check_query_status(status: int) -> None:
    """Report an error from API call.

    :param status: The status from the API.
    """
    if status != 200:
        raise RuntimeError(
            f"The response from the API had the following status: {status}"
        )

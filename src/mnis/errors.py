"""Package errors"""


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


def check_query_status(status: int) -> None:
    """Report an error from API call.

    :param status: The status from the API.
    """
    if status != 200:
        raise RuntimeError(
            f"The response from the API had the following status: {status}"
        )

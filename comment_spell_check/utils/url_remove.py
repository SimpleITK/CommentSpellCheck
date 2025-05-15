"""Module to remove URLs from a string."""

import re


def remove_urls(text):
    """
    Removes URLs from a string using a regular expression.

    Args:
        text: The input string.

    Returns:
        The string with URLs removed.
    """
    url_pattern = re.compile(
        r"(?:https?:\/\/)?[\w.-]+\.[\w.-]+[^\s]*",
        re.IGNORECASE,
    )
    return url_pattern.sub("", text)




# Utility functions to check substrings in strings
def anyIn(string: str, *substrings):
    """
    Checks if any of the substrings are present in the given string.

    :param string: The string to search.
    :param substrings: Substrings to check for.
    :return: True if any substring is found, False otherwise.
    """
    return any(sub in string for sub in substrings)

def allIn(string: str, *substrings):
    """
    Checks if all of the substrings are present in the given string.

    :param string: The string to search.
    :param substrings: Substrings to check for.
    :return: True if all substrings are found, False otherwise.
    """
    return all(sub in string for sub in substrings)

def noneIn(string: str, *substrings):
    """
    Checks if none of the substrings are present in the given string.

    :param string: The string to search.
    :param substrings: Substrings to check for.
    :return: True if no substrings are found, False otherwise.
    """
    return not anyIn(string, *substrings)
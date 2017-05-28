"""Auxiliary classes and functions to support the model"""

from re import fullmatch
from distutils.util import strtobool


def s2b(value):
    """Return the boolean representation of a string.
    :param value: String with value True or False.
    """
    return bool(strtobool(value.lower()))


class Guid(str):
    """Object represents a GUID which is a string."""
    def __new__(cls, value):
        if fullmatch("[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}", value):
            return str.__new__(cls, value)
        else:
            raise ValueError("String doesn't look like a GUID.")


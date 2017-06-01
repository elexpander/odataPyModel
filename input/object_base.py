"""Base object class and other classes."""

from re import fullmatch, search
from datetime import datetime, date, time


class ObjectBase(object):

    def __repr__(self):
        """Returns string representation of the object in a single line"""
        output = '<ODATA ' + type(self).__name__ + ': {'
        for k, v in self.__dict__.items():
            if v is not None:
                output += k + ': ' + str(v) + ', '
        output += '}>'
        return output

    def __str__(self):
        """Returns string representation of the object in multiple lines."""
        output = '<ODATA ' + type(self).__name__ + ': {\n'
        for k, v in self.__dict__.items():
            if v is not None:
                output += '\t' + k + ': ' + str(repr(v)) + ',\n'
        output += '}>'
        return output

    def serialize(self):
        """Returns the serialized form of the object as a dict."""
        serialized = {}

        for prop in self.__dict__:
            if isinstance(self.__dict__[prop], ObjectBase):
                serialized[prop] = self.__dict__[prop].serialize()
            else:
                serialized[prop] = str(self.__dict__[prop])

        return serialized


class Guid(str):
    """Object represents a GUID which is a string."""
    def __new__(cls, value):
        if fullmatch("[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}", value):
            return str.__new__(cls, value)
        else:
            raise ValueError("String doesn't look like a GUID.")


class Date(date):
    """Representation of a date without time."""
    def __init__(self, value):
        """Initializes the date object.
        :param value: String representation of date in YYYY-MM-DD format.
        :return: date object."""
        m = search(r"(?P<year>[0-9]{4})-(?P<month>[0-9]{2})-(?P<day>[0-9]{2})", value)
        if not m:
            raise ValueError("Incorrect date format.")
        year = int(m.group('year'))
        month = int(m.group('month'))
        day = int(m.group('day'))
        self = date(year, month, day)


class Time(time):
    """Representation of a time of day. Optionally it can have seconds and fractional seconds.
    :param value: String representation of time in HH:MM[:SS[.microseconds]] format.
    :return: time object."""
    def __init__(self, value):
        m = search(r"(?P<hour>[0-9]{4}):(?P<min>[0-9]{2})(:(?P<sec>[0-9]{2})(.(?P<ms>[0-9]{0,6}))?)?", value)
        if not m:
            raise ValueError("Incorrect time format.")

        hour = int(m.group('hour'))
        min = int(m.group('min'))
        sec = int(m.group('sec')) if m.group('sec') else 0
        ms = int(m.group('ms')) if m.group('ms') else 0

        self = time(hour, min, sec, ms)


class DateTime(datetime):
    """Representation of a full date with time."""
    def __init__(self, value):
        m = search(r"((?P<zulu>Z)|(?P<tz>[+-][0-9]{2}:[0-9]{2}))", value)
        if not m:
            raise ValueError("Incorrect datetime format.")

        d = Date(value)
        t = Time(value)

        self = datetime.combine(d, t)


"""Auxiliary classes and functions to support the model"""

from re import fullmatch, search, match
from datetime import datetime, date, time


def detect_object_type(self, odata_context, odata_type=None):
    """Returns class corresponding to the odata context and type specified by parameters.
    :param odata_context: odata context.
    :param odata_type: odata type. Optional.
    :return: python class name"""

    # If we have odata type we don't need the context
    if odata_type:
        odata_type = odata_type.lstrip('#')
        if odata_type in ODATA_TYPE_TO_PYTHON:
            return ODATA_TYPE_TO_PYTHON[odata_type]
        else:
            raise ValueError("Unknown odata type: " + odata_type)

    try:
        # Remove leading part of URL and trailing /$entity
        t = odata_context.split('#')[1]
        t = t.replace("/$entity", "")
    except IndexError:
        raise ValueError("Unknown odata context: " + odata_context)

    # Find out what the context is
    if match(r"Collection\(", t):
        # It's a collection of object type
        odata_type = match(r"Collection\((?P<type>[0-9a-zA-Z_]+)\)", t).groupdict()['type']
        if odata_type in ODATA_TYPE_TO_PYTHON:
            return ODATA_TYPE_TO_PYTHON[odata_type]
        else:
            raise ValueError("Unknown odata context: " + odata_context)

    try:
        context_dic = match(r"(?P<root>[0-9a-zA-Z_]+)(?P<branch>[/\(].+)?", t).groupdict()
    except AttributeError:
        raise ValueError("Unknown odata context: " + odata_context)

    root, branch = context_dic['root'], context_dic['branch']
    if root in ODATA_TYPE_TO_PYTHON:
        # It's an object type
        if not branch:
            return ODATA_TYPE_TO_PYTHON[root]
        else:
            raise ValueError("Unknown odata context: " + odata_context)

    if root in ODATA_CONTAINER_TYPE:
        if not branch or match(r"\([^\(\)]+\)$", branch):
            # It's just a container
            return ODATA_TYPE_TO_PYTHON[ODATA_CONTAINER_TYPE[root]]
        else:

            try:
                branch_dict = match(r"/(?P<derived>[0-9a-zA-Z_]+)(?P<derived_branch>[/\(].+)?", branch).groupdict()
                derived, derived_branch = branch_dict['derived'], branch_dict['derived_branch']
                if derived in ODATA_TYPE_TO_PYTHON:
                    # It's a derived type
                    if not derived_branch or match(r"\([^\(\)]+\)$", derived_branch):
                        # It's just a derived type from a container
                        return ODATA_TYPE_TO_PYTHON[derived]

                    else:
                        prop = match(r"\(\S+\)/(?P<prop>[0-9a-zA-Z_]+)", derived_branch).groupdict()['prop']
                        if len(prop):
                            # It's a property of a derived type
                            return ODATA_TYPE_TO_PYTHON[ODATA_PROPERTY_TYPE[derived][prop]]

                raise ValueError("Unknown odata context: " + odata_context)
            except AttributeError:
                # It's not a derived type
                pass

            try:
                prop = match(r"\(\S+\)/(?P<prop>[0-9a-zA-Z_]+)", branch).groupdict()['prop']
                if len(prop):
                    # It's a property of a container type
                    return ODATA_TYPE_TO_PYTHON[ODATA_PROPERTY_TYPE[ODATA_CONTAINER_TYPE[root]][prop]]

            except AttributeError:
                pass

    # It must be something we didn't think about
    raise ValueError("Unknown odata context: " + odata_context)


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



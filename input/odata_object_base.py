"""Base object class and other classes."""
from re import fullmatch, search
from datetime import datetime, date, time


class OdataObjectBase(object):
    odata = ""
    valid_odata_properties = {}
    valid_properties = {}

    @classmethod
    def get_property_odata_name(cls, name):
        if name in cls.valid_properties:
            return cls.valid_properties[name]['odata_name']
        else:
            try:
                return cls.__bases__[0].get_property_odata_name(name)
            except AttributeError:
                raise ValueError("Property '{}' not valid.".format(name))

    @classmethod
    def property_is_collection(cls, name):
        if name in cls.valid_properties:
            return cls.valid_properties[name]['odata_type'].startswith("Collection")
        else:
            try:
                return cls.__bases__[0].property_is_collection(name)
            except AttributeError:
                raise ValueError("Property '{}' not valid.".format(name))

    def __repr__(self):
        """Returns string representation of the object in a single line"""
        output = '<ODATA ' + type(self).__name__ + ': {'
        for k, v in self.__dict__.items():
            if v is not None:
                output += k + ': ' + str(repr(v)) + ', '
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

    def set(self, **kwargs):
        """Set object attributes after checking that value type is correct for the attribute.
        :param kwargs: Key-value pairs passed to function: attribute name - attribute value.
        :type kwargs: Dictionary.
        """
        args = kwargs
        c = self.__class__

        while args and c != OdataObjectBase:
            inherited_args = {}

            for k, v in args.items():

                # Check if attribute belongs to the current class
                if k in c.valid_properties:

                    # Get paramter type name and find out if it's a list
                    pt_name = c.valid_properties[k]['python_type']
                    pt_name, is_list = (pt_name[1:], True) if pt_name.startswith("*") else (pt_name, False)

                    if is_list:
                        # If attribute is a list, we accept a list of objects or an object
                        # as long as they are the right type
                        if type(v).__name__ == pt_name:
                            # Assign a list of the object to the attribute
                            setattr(self, k, [v])
                        elif isinstance(v, list):
                            for i in v:
                                if type(i).__name__ != pt_name:
                                    raise ValueError("Parameter {} must be list of {}.".format(k, pt_name))
                            # Assign the object to the attribute
                            setattr(self, k, v)
                        else:
                            raise ValueError("Parameter {} must be list of {}.".format(k, pt_name))

                    else:
                        # Attribute must be a single object of the right type
                        if type(v).__name__ == pt_name:
                            setattr(self, k, v)
                        else:
                            raise ValueError("Parameter {} must be {}.".format(k, pt_name))

                else:
                    # getattr raises AttributeError if attribute doesn't exist
                    getattr(self, k)
                    # Attribute is inherited
                    inherited_args[k] = v

            # Next while loop will process inherited attributes and base class
            args = inherited_args
            c = c.__bases__[0]

    def serialized(self):
        """Returns the serialized form of the object as a dict."""
        odata_dict = {}

        for prop in self.__dict__:
            oname = self.get_property_odata_name(prop)

            if isinstance(self.__dict__[prop], OdataObjectBase):
                # if the property is an object, get its serialized form
                odata_dict[oname] = self.__dict__[prop].serialized()
            elif self.__dict__[prop] is not None:

                # if the property has a value, get its string representation
                odata_dict[oname] = self.__dict__[prop]

        return odata_dict


class Guid(str):
    """Object represents a GUID which is a string."""
    def __new__(cls, *value):
        if fullmatch("[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}", value):
            return str.__new__(value)
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

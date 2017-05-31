"""Base object class and other classes."""


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

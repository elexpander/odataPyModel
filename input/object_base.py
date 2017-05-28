"""Base object class and other classes."""


class ObjectBase(object):

    def __str__(self):
        """Returns the object content as a string.
        
        Returns:
            output: String representing object with its properties.
        """
        output = '<ODATA Object: ' + type(self).__name__ + ' {\n'
        for k, v in self.__dict__.items():
            value = str(v)
            output += '\t' + k + ': ' + value + ',\n'
        output += '}>'
        return output

    def serialize(self):
        """Returns the serialized form of the object as a dict.
        
        Returns:
            dict: The serialized form of the object
        """
        serialized = {}

        for prop in self.__dict__:
            if isinstance(self.__dict__[prop], ObjectBase):
                serialized[prop] = self.__dict__[prop].serialize()
            else:
                serialized[prop] = str(self.__dict__[prop])

        return serialized

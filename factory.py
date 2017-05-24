"""
Module to create Classes
"""
from metadata import EntitySet, Singleton, EnumType, ComplexType, EntityType, Metadata
from string import Template
import logging


class ClassFactory(object):

    def __init__(self):

        self.str_graph_object_base = """
class GraphObjectBase(object):

    def __str__(self):
        output = '<MSGRAPH Object: ' + type(self).__name__ + ' {\n'
        for k, v in self.__dict__.items():
            value = str(v)
            output += '\t' + k + ': ' + value + ',\n'
        output += '}'
        return output
"""

        self.str_class_def = """
class $class_name($super_class_name):"""

        self.str_init_method = """
    def __init__(self, **kwargs):
        super().__init__()
"""

        #for key, value in kwargs.items():
        #    if key in ()

    """
        graph_type { base
                     properties: { name
                                   type }
                     navigation_properties: { name
                                              type }
                     actions: { name
                                return_type
                                parameters { name
                                             type } }
                     functions: { name
                                  return_type
                                  parameters { name
                                               type } }
                   }
    """

    def create_enumtype(self, name, schema_type):

        str_class = """
    class $class_name(str):
        
        odata = '$odata_name'

        def __new__(cls, value):
            valid_values = $valid_values
            error_message = "Value is no valid for a $class_name"

            if value in valid_values:
                return str.__new__(cls, value)
            else:
                raise ValueError(error_message)
"""
        dic_values = {'class_name': name,
                      'odata_name': schema_type.odata_name,
                      'valid_values': schema_type.valid_values}

        str_class = Template(str_class).substitute(dic_values)
        return str_class

    def create_complextype(self, name, schema):
        odata_properties = {value['odata_name']: key for (key, value) in schema.properties.items()}

        attributes = "# Properties\n            "
        for p_name, p_item in schema.properties.items():
            attributes += "self." + p_name + " = "
            if p_item['python_type'].startswith('*'):
                attributes += "[" + p_item['python_type'][1:] + "(prop) for prop in properties[pp]]"
            else:
                attributes += p_item['python_type'] + "(properties[pp])"
            attributes += " if pp in properties else None\n            "

        attributes += "\n            # Navigation Properties\n            "
        for p_name, p_item in schema.navigation_properties.items():
            attributes += "self." + p_name + " = "
            if p_item['python_type'].startswith('*'):
                attributes += "[" + p_item['python_type'][1:] + "(prop) for prop in properties[pp]]"
            else:
                attributes += p_item['python_type'] + "(properties[pp])"
            attributes += " if pp in properties else None\n            "

        str_class = '''
    class $class_name(GraphObjectBase):

        odata = '$odata_name'
        valid_odata_properties = []
        valid_properties = $properties
        
        def __init__(self, properties=None, odata_properties=None):
            """Initialization of $odata_name instance
            Must call with at least one of the 2 available parameters.
            :param properties: dictionary of properties with their values.
            :param odata_properties: dictionary of properties in their original odata name
                                     with their values.
            """
            
            if odata_properties:
                # Convert properties' names to python format
                properties = [valid_odata_properties[key]: value for key, value in odata_properties.items() \
                              if key in valid_odata_properties]
                
            if not properties:
                raise ValueError("Missing properties.")
                
            super().__init__(properties)

            $attributes
'''

        dic_values = {'class_name': name,
                      'odata_name': schema.odata_name,
                      'python_properties': schema.properties,
                      'odata_properties': odata_properties,
                      'attributes': attributes}

        str_class = Template(str_class).substitute(dic_values)
        return str_class
    '''
    def action_name(self, param1, param2, paramN):

        # https://developer.microsoft.com/en-us/graph/docs/api-reference/beta/api/user_assignlicense
        POST / users / {id | userPrincipalName} / assignLicense

        POST
        https: // graph.microsoft.com / beta / me / assignLicense
        Content - type: application / json
        Content - length: 185

        {
            "addLicenses": [
                {
                    "disabledPlans": ["11b0131d-43c8-4bbb-b2c8-e80f9a50834a"],
                    "skuId": "skuId-value"
                }
            ],
            "removeLicenses": ["bea13e0c-3828-4daa-a392-28af7ff61a0f"]
        }
    '''



    def create_entitytype(self, name, schema):
        odata_properties = {value['odata_name']: key for (key, value) in schema.properties.items()}

        attributes = "# Properties\n            "
        for p_name, p_item in schema.properties.items():
            attributes += "self." + p_name + " = "
            if p_item['python_type'].startswith('*'):
                attributes += "[" + p_item['python_type'][1:] + "(prop) for prop in properties[pp]]"
            else:
                attributes += p_item['python_type'] + "(properties[pp])"
            attributes += " if pp in properties else None\n            "

        attributes += "\n            # Navigation Properties\n            "
        for p_name, p_item in schema.navigation_properties.items():
            attributes += "self." + p_name + " = "
            if p_item['python_type'].startswith('*'):
                attributes += "[" + p_item['python_type'][1:] + "(prop) for prop in properties[pp]]"
            else:
                attributes += p_item['python_type'] + "(properties[pp])"
            attributes += " if pp in properties else None\n            "

        str_class = '''
    class $class_name($base_class_name):
        """Class represents $odata_name objects."""
    
        odata = '$odata_name'
        valid_odata_properties = $odata_properties
        valid_properties = $python_properties
    
        def __init__(self, properties=None, odata_properties=None):
            """Initialization of $odata_name instance
            Must call with at least one of the 2 available parameters.
            :param properties: dictionary of properties with their values.
            :param odata_properties: dictionary of properties in their original odata name
                                     with their values.
            """
            
            if odata_properties:
                # Convert properties' names to python format
                properties = [valid_odata_properties[key]: value for key, value in odata_properties.items() \\
                              if key in valid_odata_properties]
                
            if not properties:
                raise ValueError("Missing properties.")
                
            super().__init__(properties)

            $attributes
'''

        dic_values = {'class_name': name,
                      'base_class_name': schema.base if schema.base else 'GraphObjectBase',
                      'odata_name': schema.odata_name,
                      'python_properties': str(schema.properties).replace('}, ', '},\n' + ' ' * 28),
                      'odata_properties': str(odata_properties).replace(', ', ',\n' + ' ' * 34),
                      'attributes': attributes}

        str_class = Template(str_class).substitute(dic_values)
        return str_class

    def create_class(self, name, schema):

        def save_class(filename, text):
            with open("model/" + filename + ".py", 'w') as f:
                f.write(text)

        print(name)
        print(schema)

        if isinstance(schema, EnumType):
            str_class = self.create_enumtype(name, schema)

        elif isinstance(schema, EntityType):
            str_class = self.create_entitytype(name, schema)

        elif isinstance(schema, ComplexType):
            str_class = self.create_complextype(name, schema)

        else:
            logging.warning("Class " + name + " is not a known EDM type.")
            return

        module_name = Metadata.camel_to_lowercase(name)
        save_class(module_name, str_class)







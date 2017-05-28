"""
Module to create Classes
"""
from metadata import Metadata
from string import Template
from shutil import copyfile


BASE_CLASS = "ObjectBase"
INPUT_PATH = "input"
OUTPUT_PATH = "output"
AUXILIARY_FILE = "auxiliary.py"


class ClassFactory(object):

    def __init__(self):

        self.classes = {}

    ######################################################################

    def add_enumtype(self, name, schema_type):

        str_class = """$license


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
                      'valid_values': schema_type.valid_values,
                      'license': '"""License"""'}

        self.classes[name] = Template(str_class).substitute(dic_values)

    ######################################################################

    def add_complextype(self, name, schema):
        imports = [self.get_import_line(BASE_CLASS)]

        odata_properties = {value['odata_name']: key for (key, value) in schema.properties.items()}

        attributes = "# Properties\n        "
        for p_name, p_item in schema.properties.items():

            # Find out if it's a list and get the type
            if p_item['python_type'].startswith('*'):
                is_list = True
                p_type = p_item['python_type'][1:]
            else:
                is_list = False
                p_type = p_item['python_type']

            if p_type == "bool":
                # Function to cast str to bool
                p_type = "s2b"

            # Collect necessary imports
            import_line = self.get_import_line(p_type)
            if import_line and import_line not in imports:
                imports.append(import_line)

            if is_list:
                attributes += "[" + p_type + "(prop) for prop in properties['" + p_name + "']]"
            else:
                attributes += p_type + "(properties['" + p_name + "'])"

            attributes += " if '" + p_name + "' in properties else None\n        "
        '''
        attributes += "\n        # Navigation Properties\n        "
        for p_name, p_item in schema.navigation_properties.items():
            attributes += "self." + p_name + " = "
            if p_item['python_type'].startswith('*'):
                attributes += "[" + p_item['python_type'][1:] + "(prop) for prop in properties['" + p_name + "']]"
            else:
                attributes += p_item['python_type'] + "(properties['" + p_name + "'])"
            attributes += " if '" + p_name + "' in properties else None\n            "
        '''
        str_class = '''$license
$imports

class $class_name($base_class_name):
    """Represents odata complex type object: $odata_name""" 

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
            properties = {$class_name.valid_odata_properties[key]: value for key, value in odata_properties.items() \\
                          if key in $class_name.valid_odata_properties}
            
        if not properties:
            raise ValueError("Missing properties.")
            
        super().__init__()

        $attributes
'''
        str_imports = "".join([line + "\n" for line in imports if isinstance(line, str)])

        dic_values = {'class_name': name,
                      'base_class_name': BASE_CLASS,
                      'imports': str_imports,
                      'odata_name': schema.odata_name,
                      'python_properties': str(schema.properties).replace('}, ', '},\n' + ' ' * 24),
                      'odata_properties': str(odata_properties).replace(', ', ',\n' + ' ' * 30),
                      'attributes': attributes,
                      'license': '"""License"""'}

        self.classes[name] = Template(str_class).substitute(dic_values)

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

    ######################################################################

    def add_entityset(self, name, schema):
        pass
    '''
    < EntitySet    Name = "users"    EntityType = "microsoft.graph.user" >
    < NavigationPropertyBinding    Path = "ownedDevices"    Target = "directoryObjects" / >
    < NavigationPropertyBinding    Path = "registeredDevices"    Target = "directoryObjects" / >
    < NavigationPropertyBinding    Path = "manager"    Target = "directoryObjects" / >
    < NavigationPropertyBinding    Path = "directReports"    Target = "directoryObjects" / >
    < NavigationPropertyBinding    Path = "memberOf"    Target = "directoryObjects" / >
    < NavigationPropertyBinding    Path = "createdObjects"    Target = "directoryObjects" / >
    < NavigationPropertyBinding    Path = "ownedObjects"    Target = "directoryObjects" / >
    < NavigationPropertyBinding    Path = "microsoft.graph.baseItem/createdByUser"    Target = "users" / >
    < NavigationPropertyBinding    Path = "microsoft.graph.baseItem/lastModifiedByUser"    Target = "users" / >
    < / EntitySet >
    '''

    def add_singleton(self, name, schema):
        pass

    ######################################################################

    def get_import_line(self, object_type):
        """Returns string with import line for the type."""
        if object_type in ("str", "int", "float", "bytes"):
            output = None

        elif object_type == "s2b":
            output = "from .auxiliary import s2b"

        elif object_type in ("time", "date", "datetime", "timedelta"):
            output = "from datetime import " + object_type

        elif object_type == "Guid":
            output = "from .auxiliary import Guid"

        else:
            type_file = Metadata.camel_to_lowercase(object_type)
            output = "from ." + type_file + " import " + object_type

        return output

    ######################################################################

    def add_entitytype(self, name, schema):

        base_class_name = schema.base if schema.base else BASE_CLASS
        imports = [self.get_import_line(base_class_name)]

        odata_properties = {value['odata_name']: key for (key, value) in schema.properties.items()}

        attributes = "# Properties\n        "
        for p_name, p_item in schema.properties.items():
            attributes += "self." + p_name + " = "

            # Find out if it's a list and get the type
            if p_item['python_type'].startswith('*'):
                is_list = True
                p_type = p_item['python_type'][1:]
            else:
                is_list = False
                p_type = p_item['python_type']

            if p_type == "bool":
                # Function to cast str to bool
                p_type = "s2b"

            # Collect necessary imports
            import_line = self.get_import_line(p_type)
            if import_line not in imports:
                imports.append(import_line)

            if is_list:
                attributes += "[" + p_type + "(prop) for prop in properties['" + p_name + "']]"
            else:
                attributes += p_type + "(properties['" + p_name + "'])"

            attributes += " if '" + p_name + "' in properties else None\n        "

        '''
        attributes += "\n        # Navigation Properties\n        "
        for p_name, p_item in schema.navigation_properties.items():
            attributes += "self." + p_name + " = "
            if p_item['python_type'].startswith('*'):
                attributes += "[" + p_item['python_type'][1:] + "(prop) for prop in properties['" + p_name + "']]"
            else:
                attributes += p_item['python_type'] + "(properties['" + p_name + "'])"
            attributes += " if '" + p_name + "' in properties else None\n        "
        '''
        str_class = '''$license
$imports

class $class_name($base_class_name):
    """Represents odata entity type object: $odata_name""" 

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
            properties = {$class_name.valid_odata_properties[key]: value for key, value in odata_properties.items() \\
                          if key in $class_name.valid_odata_properties}
            
        if not properties:
            raise ValueError("Missing properties.")

'''
        str_imports = "".join([line + "\n" for line in imports if isinstance(line, str)])

        if base_class_name != BASE_CLASS:
            str_class += '''        super().__init__(properties)\n\n'''
        str_class += '''        $attributes\n\n'''

        dic_values = {'class_name': name,
                      'base_class_name': base_class_name,
                      'imports': str_imports,
                      'odata_name': schema.odata_name,
                      'python_properties': str(schema.properties).replace('}, ', '},\n' + ' ' * 24),
                      'odata_properties': str(odata_properties).replace(', ', ',\n' + ' ' * 30),
                      'attributes': attributes,
                      'license': '"""License"""'}

        self.classes[name] = Template(str_class).substitute(dic_values)

    ######################################################################

    def save(self):
        str_package = '"""Package with all classes representing data model."""\n\n'

        for class_name, str_class in self.classes.items():
            file_name = Metadata.camel_to_lowercase(class_name)
            str_package += "from ." + file_name + " import " + class_name + "\n"
            with open(OUTPUT_PATH + "/" + file_name + ".py", 'w') as f:
                f.write(str_class)

        with open(OUTPUT_PATH + "/__init__.py", 'w') as f:
            f.write(str_package)

        base_class_file = Metadata.camel_to_lowercase(BASE_CLASS) + ".py"
        copyfile(INPUT_PATH + "/" + base_class_file, OUTPUT_PATH + "/" + base_class_file)
        copyfile(INPUT_PATH + "/" + AUXILIARY_FILE, OUTPUT_PATH + "/" + AUXILIARY_FILE)






"""
Module to create Classes
"""
from .metadata import *
from string import Template
from shutil import copyfile
import logging
import json


BASE_CLASS = "OdataObjectBase"
EXTENSION_FILE = "extension.py"
MODEL_FILENAME = "model.json"


class ClassFactory(object):

    def __init__(self, metadata_url, temp_loc, output_loc):

        """
        Loads classes from model file
        If model file doesn't exist, it generates it from the metadata.
        :param model_file: name of file with model in json format
        :param base_url: url of the metadata
        """
        self.input_location = "./input/"
        self.output_location = output_loc
        self.temp_location = temp_loc

        self.odata_types = {}
        self.odata_containers = {}
        self.odata_properties = {}
        self.classes = {}

        # Create model file from metadata
        self.metadata = Metadata(metadata_url, temp_loc)

        # Save model to json file for review
        with open(temp_loc + MODEL_FILENAME, 'w') as f:
            json.dump(self.metadata.classes, f, indent=4)

        '''
        with open("model_sets.json", 'w') as f:
            json.dump(metadata.sets, f, indent=4)

        with open("model_udm.json", 'w') as f:
            json.dump(metadata.odata_types, f, indent=4)
        '''
        self.load_classes()

    def load_classes(self):
        """Return dictionary with all Graph Classes
        """
        for name, graph_class in self.metadata.classes.items():

            if isinstance(graph_class, EntityType):
                self.add_entitytype(name, graph_class)

            elif isinstance(graph_class, ComplexType):
                self.add_complextype(name, graph_class)

            elif isinstance(graph_class, EnumType):
                self.add_enumtype(name, graph_class)

            else:
                logging.warning("Class " + name + " is not a known EDM type.")

        for name, graph_set in self.metadata.sets.items():
            if isinstance(graph_set, Singleton):
                self.add_singleton(name, graph_set)

            elif isinstance(graph_set, EntitySet):
                self.add_entityset(name, graph_set)

            else:
                logging.warning("Class " + name + " is not a known EDM type.")

        self.save()

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

        d_prop = {}
        for k, v in {np.odata_name: np.odata_type for np in schema.navigation_properties.values()}.items():
            d_prop[k] = v.replace("Collection(", "").rstrip(')')
        for k, v in {np.odata_name: np.odata_type for np in schema.properties.values()}.items():
            d_prop[k] = v.replace("Collection(", "").rstrip(')')
        self.odata_properties[schema['odata_name']] = d_prop

        imports = [self.get_import_line(BASE_CLASS)]

        odata_properties = {value['odata_name']: key for (key, value) in schema.properties.items()}

        attributes = "# Properties\n"
        for p_name, p_item in schema.properties.items():
            attributes += "        self." + p_name + " = "

            # Find out if it's a list and get the type
            if p_item['python_type'].startswith('*'):
                is_list = True
                p_type = p_item['python_type'][1:]
            else:
                is_list = False
                p_type = p_item['python_type']

            # Collect necessary imports
            import_line = self.get_import_line(p_type)
            if import_line and import_line not in imports:
                imports.append(import_line)

            if is_list:
                attributes += "[" + p_type + "(prop) for prop in properties['" + p_name + "']]"
            else:
                attributes += p_type + "(properties['" + p_name + "'])"

            attributes += " \\\n            if '" + p_name + "' in properties and properties['" + p_name + "'] is not None else None\n"

        str_class = '''$license
$imports

class $class_name($base_class_name):
    """Represents odata complex type object: $odata_name""" 

    odata = '$odata_name'
    valid_odata_properties = $odata_properties
    valid_properties = $python_properties
    
    def __init__(self, odata_properties={}, **kwargs):
        """Initialization of $odata_name instance
        :param odata_properties: dictionary of properties in their original odata name
                                 with their values.
        """  
        super().__init__()
'''
        str_class += '''        try:
            # Convert properties' names to python format
            properties = {$class_name.valid_odata_properties[key]: value for key, value in odata_properties.items() \\
                          if key in $class_name.valid_odata_properties}
        except AttributeError:
            raise ValueError("Positional parameter 'odata_properties' must be a dictionary.")\n'''

        str_class += "\n        $attributes\n"
        str_class += '''        if kwargs:\n            self.set(**kwargs)\n\n'''

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
        self.odata_containers[schema.odata_name] = schema.odata_entity_type.lstrip('*')

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
        self.odata_containers[schema.odata_name] = schema.odata_entity_type.lstrip('*')

    ######################################################################

    def get_import_line(self, object_type):
        """Returns string with import line for the type."""
        if object_type in ("str", "int", "float", "bool", "bytes"):
            output = None

        elif object_type in ("time", "date", "datetime", "timedelta"):
            output = "from datetime import " + object_type

        elif object_type == "Guid":
            output = "from .{} import Guid".format(Metadata.camel_to_lowercase(BASE_CLASS))

        else:
            type_file = Metadata.camel_to_lowercase(object_type)
            output = "from ." + type_file + " import " + object_type

        return output

    ######################################################################

    def add_entitytype(self, name, schema):

        d_prop = {}
        attributes = "# Properties\n"

        # Build ODATA_PROPERTY_TYPE dictionary
        for k, v in {np.odata_name: np.odata_type for np in schema.navigation_properties.values()}.items():
            d_prop[k] = v.replace("Collection(", "").rstrip(')')
        for k, v in {np.odata_name: np.odata_type for np in schema.properties.values()}.items():
            d_prop[k] = v.replace("Collection(", "").rstrip(')')
        self.odata_properties[schema['odata_name']] = d_prop

        base_class_name = schema.base if schema.base else BASE_CLASS
        imports = [self.get_import_line(base_class_name)]

        # Build value for valid_odata_properties
        odata_properties = {value['odata_name']: key for (key, value) in schema.properties.items()}

        # Build class attributes assigment code
        for p_name, p_item in schema.properties.items():
            attributes += "        self." + p_name + " = "

            # Find out if it's a list and get the type
            if p_item['python_type'].startswith('*'):
                is_list = True
                p_type = p_item['python_type'][1:]
            else:
                is_list = False
                p_type = p_item['python_type']

            # Collect necessary imports
            import_line = self.get_import_line(p_type)
            if import_line not in imports:
                imports.append(import_line)

            if is_list:
                attributes += "[" + p_type + "(prop) for prop in properties['" + p_name + "']]"
            else:
                attributes += p_type + "(properties['" + p_name + "'])"

            attributes += " \\\n            if '" + p_name + "' in properties and properties['" + p_name + "'] is not None else None\n"

        str_class = '''$license
$imports

class $class_name($base_class_name):
    """Represents odata entity type object: $odata_name""" 

    odata = '$odata_name'
    valid_odata_properties = $odata_properties
    valid_properties = $python_properties

    def __init__(self, odata_properties={}, **kwargs):
        """Initialization of $odata_name instance
        :param odata_properties: dictionary of properties in their original odata name
                                 with their values.
        """
'''
        str_imports = "".join([line + "\n" for line in imports if isinstance(line, str)])

        if base_class_name != BASE_CLASS:
            str_class += '''        super().__init__(odata_properties, **kwargs)\n\n'''

        str_class += '''        try:
            # Convert properties' names to python format
            properties = {$class_name.valid_odata_properties[key]: value for key, value in odata_properties.items() \\
                          if key in $class_name.valid_odata_properties}
        except AttributeError:
            raise ValueError("Positional parameter 'odata_properties' must be a dictionary.")\n'''

        str_class += '''\n        $attributes\n'''
        str_class += '''        if kwargs:\n            self.set(**kwargs)\n\n'''

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
        str_package = ""

        # object classes files
        for class_name, str_class in self.classes.items():
            file_name = Metadata.camel_to_lowercase(class_name)
            str_package += "from ." + file_name + " import " + class_name + "\n"
            with open(self.output_location + file_name + ".py", 'w') as f:
                f.write(str_class)

        # __init__.py
        copyfile(self.input_location + "__init__.py",self.output_location + "__init__.py")
        with open(self.output_location + "__init__.py", 'a') as f:
            f.write(str_package)

        # object base file
        base_class_file = Metadata.camel_to_lowercase(BASE_CLASS) + ".py"
        copyfile(self.input_location + base_class_file, self.output_location + base_class_file)

        # extension file
        copyfile(self.input_location + EXTENSION_FILE, self.output_location + EXTENSION_FILE)
        with open(self.output_location + EXTENSION_FILE, 'a') as f:

            f.write("ODATA_CONTAINER_TYPE = {")
            for k, v in self.odata_containers.items():
                f.write("'" + k + "': '" + v + "',\n                        ")
            f.write("}\n\n")

            f.write("ODATA_TYPE_TO_PYTHON = {")
            for k, v in self.odata_types.items():
                f.write("'" + k + "': " + v + ",\n                        ")
            f.write("}\n\n")

            f.write("ODATA_PROPERTY_TYPE = {")
            for obj, d in self.odata_properties.items():
                f.write("'" + obj + "': {\n")
                for p, t in d.items():
                    f.write("                           '" + p + "': '" + t + "',\n")
                f.write("                           },\n                       ")
            f.write("}\n\n")




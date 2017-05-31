import xml.etree.ElementTree as ET
from urllib.request import urlretrieve
from os.path import isfile
import logging
from keyword import iskeyword


class OdataFunction(dict):
    def __init__(self,
                 returns=None,
                 parameters=None):
        super().__init__()
        self['returns'] = returns
        self['parameters'] = parameters


class OdataProperty(dict):
    def __init__(self,
                 python_type,
                 odata_name,
                 odata_type):
        super().__init__()
        self['python_type'] = python_type
        self['odata_name'] = odata_name
        self['odata_type'] = odata_type

    @property
    def python_type(self):
        return self['python_type']

    @property
    def odata_name(self):
        return self['odata_name']

    @property
    def odata_type(self):
        return self['odata_type']


class EdmType(dict):
    def __init__(self, odata_name):
        super().__init__()
        self['edm_type'] = None
        self['odata_name'] = odata_name

    @property
    def edm_type(self):
        return self['edm_type']

    @property
    def odata_name(self):
        return self['odata_name']

    def __str__(self):
        output = '{'
        for key, value in self.items():
            output += "'" + key + "': '" + str(value) + "',\n"
        output += '}'
        return output


class EntitySet(EdmType):
    def __init__(self,
                 odata_name,
                 entity_type,
                 odata_entity_type,
                 navigation_properties=None):
        super().__init__(odata_name)
        self['edm_type'] = 'EntitySet'
        self['entity_type'] = entity_type
        self['odata_entity_type'] = odata_entity_type
        self['navigation_properties'] = navigation_properties

    @property
    def odata_entity_type(self):
        return self['odata_entity_type']


class Singleton(EntitySet):
    def __init__(self,
                 odata_name,
                 entity_type,
                 odata_entity_type,
                 navigation_properties=None):
        super().__init__(odata_name, entity_type, odata_entity_type, navigation_properties)
        self['edm_type'] = 'Singleton'


class EnumType(EdmType):
    def __init__(self, odata_name, values):
        super().__init__(odata_name)
        self['edm_type'] = "EnumType"
        self['valid_values'] = values

    @property
    def valid_values(self):
        return self['valid_values']


class ComplexType(EdmType):
    def __init__(self,
                 odata_name,
                 properties=None,
                 navigation_properties=None):
        super().__init__(odata_name)
        self['edm_type'] = "ComplexType"
        self['properties'] = properties
        self['navigation_properties'] = navigation_properties

    @property
    def properties(self):
        """
        Gets properties
        :return: boolean
        """
        return self['properties']

    @property
    def navigation_properties(self):
        """
        Gets navigation_properties
        :return: boolean
        """
        return self['navigation_properties']


class EntityType(ComplexType):
    """
        graph_type {
            base
            properties: {
                name
                type
            }
            navigation_properties: {
                name
                type
            }
            actions: { - POST request with parameters in body
                name
                return_type
                parameters {
                    name
                    type
                }
            }
            functions: { - GET request with parameters in url: reminderView(startDateTime=startDateTime-value,endDateTime=endDateTime-value)
                name
                return_type
                parameters {
                    name
                    type
                }
            }
        }
    """

    def __init__(self,
                 odata_name,
                 base_type=None,
                 key_property=None,
                 properties=None,
                 navigation_properties=None):
        super().__init__(odata_name, properties=properties, navigation_properties=navigation_properties)
        self['edm_type'] = "EntityType"
        self['key_property'] = key_property
        self['base'] = base_type

    @property
    def base(self):
        """
        Gets the base type
        :return: <string> base type
        """
        return self['base']

    @property
    def key_property(self):
        """
        Gets the key property
        :return: <string> with key property name
        """
        return self['key_property']

    def add_action(self, name, action_dic):
        """
        Adds a OdataFunction to the functions dictionary
        :param name: Name of function
        :param action_dic: OdataFunction object
        """
        if 'actions' not in self:
            self['actions'] = {name: action_dic}
        else:
            self['actions'].update({name: action_dic})

    def add_function(self, name, function_dic):
        """
        Adds a OdataFunction to the functions dictionary
        :param name: Name of function
        :param function_dic: OdataFunction object
        """
        if 'functions' not in self:
            self['functions'] = {name: function_dic}
        else:
            self['functions'].update({name: function_dic})


class Metadata(object):

    def __init__(self, metadata_url):
        super().__init__()

        # variables
        self._metadata_file = 'metadata.xml'
        self._xmlns = '{http://docs.oasis-open.org/odata/ns/edm}'
        self._namespace = ''
        self.class_prefix = 'Graph'
        self.sets = {}
        self.classes = {}
        self.odata_containers = {}
        self.odata_types = {'Edm.String': 'str',
                          'Edm.SByte': 'int',
                          'Edm.Int16': 'int',
                          'Edm.Int32': 'int',
                          'Edm.Int64': 'int',
                          'Edm.Decimal': 'float',
                          'Edm.Single': 'float',
                          'Edm.Double': 'float',
                          'Edm.Boolean': 'bool',
                          'Edm.TimeOfDay': 'str',
                          'Edm.Date': 'str',
                          'Edm.DateTimeOffset': 'str',
                          'Edm.Duration': 'str',
                          'Edm.Guid': 'Guid',
                          'Edm.Stream': 'bytes',
                          'Edm.Binary': 'bytes'}

        # functions
        def add_xmlns_to_tag(tag):
            """Return tag in XML namespace format: {http://url}tag
            """
            return self._xmlns + tag

        def add_namespace_to_tag(tag):
            """Return tag with in namespace format. 
            """
            return self._namespace + '.' + tag

        def pythonize_type(name):
            """
            Convert name into python class format
            :param name: string with name in odata format
            :return: string with name in ThisFormat
            """

            if name.startswith('Collection('):
                # remove Collection from name
                name = name[11:-1]
                is_list = True
            else:
                is_list = False

            if name.startswith(self._namespace):
                name = name.split('.')[-1]
                name = self.class_prefix + name[0].upper() + name[1:]

            elif name.startswith('Edm.'):
                # convert edm type to python
                name = self.odata_types[name]
            else:
                name = self.class_prefix + name[0].upper() + name[1:]

            if is_list:
                name = '*' + name
            return name

        def pythonize_attribute(name):
            """
            Convert name into python attribute format
            :param name: string with name in thisFormat
            :return: string with name in this_format
            """
            name = name[0].lower() + name[1:]
            name = ''.join(["_" + c.lower() if c.isupper() else c for c in name])

            while iskeyword(name):
                name = "_" + name

            return name

        def pythonize_context(name):
            """
            Convert odata context to python type
            :param name: context
            :return: python type
            """
            pass

        # begining of _init_
        if not isfile(self._metadata_file):
            # Download file
            urlretrieve(metadata_url, self._metadata_file)

        # Load schema XML file
        tree = ET.parse(self._metadata_file)
        schema = next(tree.iter(add_xmlns_to_tag('Schema')))

        # Load namespace prefix, normally microsoft.graph
        self._namespace = schema.attrib['Namespace']

        # Process EntityContainer
        entity_container = schema.find(add_xmlns_to_tag('EntityContainer'))

        # Process EntitySet
        for e_entityset in entity_container.findall(add_xmlns_to_tag('EntitySet')):

            # Get type name
            odata_entityset_name = e_entityset.attrib['Name']
            entityset_name = pythonize_attribute(odata_entityset_name)
            odata_entityset_type = e_entityset.attrib['EntityType']
            entityset_type = pythonize_type(odata_entityset_type)

            # Get navigation properties
            navigation_properties = {}
            for e_navprop in e_entityset.findall(add_xmlns_to_tag('NavigationPropertyBinding')):
                odata_prop_name = e_navprop.attrib['Path']
                odata_prop_type = e_navprop.attrib['Target']
                python_prop_name = pythonize_attribute(odata_prop_name)
                python_prop_type = pythonize_type(odata_prop_type)
                navigation_properties[python_prop_name] = OdataProperty(odata_name=odata_prop_name,
                                                                        odata_type=odata_prop_type,
                                                                        python_type=python_prop_type)
            entityset = EntitySet(odata_name=odata_entityset_name,
                                  entity_type=entityset_type,
                                  odata_entity_type=odata_entityset_type,
                                  navigation_properties=navigation_properties)

            # Add entityset to graph_type dictionary
            self.sets[entityset_name] = entityset
            self.odata_containers[entityset_name] = "*" + entityset_type

        # Process Singleton
        for e_singleton in entity_container.findall(add_xmlns_to_tag('Singleton')):

            # Get type name
            odata_singleton_name = e_singleton.attrib['Name']
            singleton_name = pythonize_attribute(odata_singleton_name)
            odata_singleton_type = e_singleton.attrib['Type']
            singleton_type = pythonize_type(odata_singleton_type)

            # Get navigation properties
            navigation_properties = {}
            for e_navprop in e_singleton.findall(add_xmlns_to_tag('NavigationPropertyBinding')):
                odata_prop_name = e_navprop.attrib['Path']
                odata_prop_type = e_navprop.attrib['Target']
                python_prop_name = pythonize_attribute(odata_prop_name)
                python_prop_type = pythonize_type(odata_prop_type)
                navigation_properties[python_prop_name] = OdataProperty(odata_name=odata_prop_name,
                                                                        odata_type=odata_prop_type,
                                                                        python_type=python_prop_type)
            singleton = Singleton(odata_name=odata_singleton_name,
                                  entity_type=singleton_type,
                                  odata_entity_type=odata_singleton_type,
                                  navigation_properties=navigation_properties)

            # Add singleton to dictionary
            self.sets[singleton_name] = singleton
            self.odata_containers[singleton_name] = singleton_type

        # Process EnumType
        for e_type in schema.findall(add_xmlns_to_tag('EnumType')):

            # Get type name
            odata_type_name = add_namespace_to_tag(e_type.attrib['Name'])
            type_name = pythonize_type(e_type.attrib['Name'])

            # Get values
            values = []
            for e_attrib in e_type.findall(add_xmlns_to_tag('Member')):
                values.append(e_attrib.attrib['Name'])

            # Add type to schema dictionary
            self.classes[type_name] = EnumType(odata_name=odata_type_name, values=values)
            self.odata_types[odata_type_name] = type_name

        # Process EntityType
        for e_type in schema.findall(add_xmlns_to_tag('EntityType')):

            # Get type name
            odata_type_name = add_namespace_to_tag(e_type.attrib['Name'])
            type_name = pythonize_type(e_type.attrib['Name'])

            # Get key if it exists
            try:
                e_key = e_type.find(add_xmlns_to_tag('Key'))
                e_key_ref = e_key.find(add_xmlns_to_tag('PropertyRef'))
                key = e_key_ref.attrib['Name']
            except AttributeError:
                key = None

            # Get type properties
            properties = {}
            for e_attrib in e_type.findall(add_xmlns_to_tag('Property')):
                # Add attribute to type dictionary
                odata_prop_name = e_attrib.attrib['Name']
                odata_prop_type = e_attrib.attrib['Type']
                python_prop_name = pythonize_attribute(odata_prop_name)
                python_prop_type = pythonize_type(odata_prop_type)
                properties[python_prop_name] = OdataProperty(odata_name=odata_prop_name,
                                                             odata_type=odata_prop_type,
                                                             python_type=python_prop_type)

            # Get type navigation properties
            navigation_properties = {}
            for e_attrib in e_type.findall(add_xmlns_to_tag('NavigationProperty')):
                # Add attribute to type dictionary
                odata_prop_name = e_attrib.attrib['Name']
                odata_prop_type = e_attrib.attrib['Type']
                python_prop_name = pythonize_attribute(odata_prop_name)
                python_prop_type = pythonize_type(odata_prop_type)
                navigation_properties[python_prop_name] = OdataProperty(odata_name=odata_prop_name,
                                                                        odata_type=odata_prop_type,
                                                                        python_type=python_prop_type)

            # Get entity base entity
            if 'BaseType' in e_type.attrib:
                base = pythonize_type(e_type.attrib['BaseType'])
            else:
                base = None

            # Create entity_type dictionary object
            entity_type = EntityType(odata_type_name,
                                     key_property=key,
                                     base_type=base,
                                     properties=properties,
                                     navigation_properties=navigation_properties)

            # Add entity_type to graph_type dictionary
            self.classes[type_name] = entity_type
            self.odata_types[odata_type_name] = type_name

        # Process ComplexType
        for e_type in schema.findall(add_xmlns_to_tag('ComplexType')):

            # Get type name
            odata_type_name = add_namespace_to_tag(e_type.attrib['Name'])
            type_name = pythonize_type(e_type.attrib['Name'])

            # Get type properties
            properties = {}
            for e_attrib in e_type.findall(add_xmlns_to_tag('Property')):
                # Add attribute to type dictionary
                odata_prop_name = e_attrib.attrib['Name']
                odata_prop_type = e_attrib.attrib['Type']
                python_prop_name = pythonize_attribute(odata_prop_name)
                python_prop_type = pythonize_type(odata_prop_type)
                properties[python_prop_name] = OdataProperty(odata_name=odata_prop_name,
                                                             odata_type=odata_prop_type,
                                                             python_type=python_prop_type)

            # Get type navigation properties
            navigation_properties = {}
            for e_attrib in e_type.findall(add_xmlns_to_tag('NavigationProperty')):
                # Add attribute to type dictionary
                odata_prop_name = e_attrib.attrib['Name']
                odata_prop_type = e_attrib.attrib['Type']
                python_prop_name = pythonize_attribute(odata_prop_name)
                python_prop_type = pythonize_type(odata_prop_type)
                navigation_properties[python_prop_name] = OdataProperty(odata_name=odata_prop_name,
                                                                        odata_type=odata_prop_type,
                                                                        python_type=python_prop_type)

            complex_type = ComplexType(odata_type_name,
                                       properties=properties,
                                       navigation_properties=navigation_properties)

            # Add type to schema dictionary
            self.classes[type_name] = complex_type
            self.odata_types[odata_type_name] = type_name

        # Process Actions
        for e_type in schema.findall(add_xmlns_to_tag('Action')):
            action_name = pythonize_attribute(e_type.attrib['Name'])
            parameters = {}
            binding = None

            for e_attrib in e_type.findall(add_xmlns_to_tag('Parameter')):
                if e_attrib.attrib['Name'] == 'bindingParameter':
                    binding = pythonize_type(e_attrib.attrib['Type'])
                else:
                    # Add attribute type to parameters dictionary
                    parameters[pythonize_attribute(e_attrib.attrib['Name'])] = pythonize_type(e_attrib.attrib['Type'])

            if binding:
                if binding.startswith("*"):
                    logging.info("Action {action} not supported, it binds to collection {binding}.".
                                 format(action=action_name, binding=binding))
                    continue

                # Load return_graph_type
                et_return_type = e_type.find(add_xmlns_to_tag('ReturnType'))
                try:
                    return_type = pythonize_type(et_return_type.attrib['Type'])
                except AttributeError:
                    return_type = None

                type_function = OdataFunction(returns=return_type,
                                              parameters=parameters)

                # Attach action to entity_type in graph_type dictionary
                try:
                    self.classes[binding].add_action(action_name, type_function)
                except KeyError:
                    raise KeyError("Key not found in dictionary trying to add action {name} to binding {binding}".
                                   format(name=action_name, binding=binding))
            else:
                logging.info("Action {name} not supported, no bindingParameter found.".
                             format(name=action_name))

        # Process Functions
        for e_type in schema.findall(add_xmlns_to_tag('Function')):
            function_name = pythonize_attribute(e_type.attrib['Name'])
            parameters = {}
            binding = None

            for e_attrib in e_type.findall(add_xmlns_to_tag('Parameter')):
                if e_attrib.attrib['Name'] == 'bindingParameter':
                    binding = pythonize_type(e_attrib.attrib['Type'])
                else:
                    # Add attribute type to parameters dictionary
                    parameters[e_attrib.attrib['Name']] = pythonize_type(e_attrib.attrib['Type'])

            if binding:
                if binding.startswith("*"):
                    logging.info("Function {name} not supported, it binds to collection {binding}.".
                                 format(name=function_name, binding=binding))
                    continue

                # Load return_graph_type
                et_return_type = e_type.find(add_xmlns_to_tag('ReturnType'))
                try:
                    return_type = pythonize_type(et_return_type.attrib['Type'])
                except AttributeError:
                    return_type = None

                type_function = OdataFunction(returns=return_type,
                                              parameters=parameters)

                # Attach function to entity_type in graph_type dictionary
                try:
                    self.classes[binding].add_function(function_name, type_function)
                except KeyError:
                    raise KeyError("Key not found in dictionary trying to add function {name} to binding {binding}".
                                   format(name=function_name, binding=binding))

            else:
                logging.info("Function {name} not supported, no bindingParameter found.".
                             format(name=function_name))

    @staticmethod
    def camel_to_lowercase(name):
        """
        Convert camel case name into lower case and words separated by underscores
        :param name: string with name in thisFormat
        :return: string with name in this_format
        """
        name = name[0].lower() + name[1:]
        name = ''.join(["_" + c.lower() if c.isupper() else c for c in name])

        while iskeyword(name):
            name = "_" + name

        return name

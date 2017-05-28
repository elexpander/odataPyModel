"""
    Declare class factory
    Load clasess in dictonary (classname, class)
"""

from metadata import *
from factory import ClassFactory
from os.path import isfile
import json


class GraphObjectBase(object):

    def __str__(self):
        output = '<MSGRAPH Object: ' + type(self).__name__ + ' {\n'
        for k, v in self.__dict__.items():
            value = str(v)
            output += '\t' + k + ': ' + value + ',\n'
        output += '}'
        return output


class GraphModel(object):

    graph_classes = {}

    def __init__(self, model_file, metadata_url):
        """
        Loads classes from model file
        If model file doesn't exist, it generates it from the metadata.
        :param model_file: name of file with model in json format
        :param base_url: url of the metadata
        """

        # Create model file from metadata
        metadata = Metadata(metadata_url)

        # Save model to json file for review
        #if not isfile(model_file):
        with open(model_file, 'w') as f:
            json.dump(metadata.classes, f, indent=4)

        # if not isfile(model_file):
        with open("model_sets.json", 'w') as f:
            json.dump(metadata.sets, f, indent=4)

        # if not isfile(model_file):
        with open("model_udm.json", 'w') as f:
            json.dump(metadata.edm_types, f, indent=4)

        self._load_classes(metadata)

    @staticmethod
    def get_class(name):
        return GraphModel.graph_classes[name]

    def _create_class(self,
                      name,
                      property_list,
                      navigation_property_list=None,
                      action_list=None,
                      function_list=None,
                      base_class=GraphObjectBase):

        def f__init__(self, properties):
            """
            Initialize instance of class
            :param self: 
            :param properties: dictionary with properties (name: value)
                               Properties may be other objects with their own properties
            :return: instance of class
            """
            if not base_class == GraphObjectBase:
                base_class.__init__(self, properties)

            for p_name, p_value in properties.items():
                if not p_name.startswith('@') and p_name in property_list:
                    setattr(self, p_name, p_value)

            """TypeError: Argument id not valid for GraphDirectoryRole
                hay que dar soporte de herencia
            """
        new_class = type(name, (base_class,), {"__init__": f__init__})
        return new_class

    def _load_classes(self, metadata):
        """Return dictionary with all Graph Classes
        """
        factory = ClassFactory()

        for name, graph_class in metadata.classes.items():

            if isinstance(graph_class, EntityType):
                factory.add_entitytype(name, graph_class)

            elif isinstance(graph_class, ComplexType):
                factory.add_complextype(name, graph_class)

            elif isinstance(graph_class, EnumType):
                factory.add_enumtype(name, graph_class)

            else:
                logging.warning("Class " + name + " is not a known EDM type.")

        for name, graph_set in metadata.sets.items():
            if isinstance(graph_set, EntitySet):
                factory.add_entityset(name, graph_set)

            elif isinstance(graph_set, Singleton):
                factory.add_singleton(name, graph_set)

            else:
                logging.warning("Class " + name + " is not a known EDM type.")

        factory.save()

    @staticmethod
    def get_python_tag(tag, context=None):
        """Return tag with Python Class format (GraphClassName)
        """
        if tag:
            pos = tag.find('}')
            if pos > 0:
                # tag is in namespace format
                new_tag = tag[pos+1:]

            elif len(tag.split('.')) == 3:
                # tag is in microsoft.graph format
                new_tag = tag.split('.')[-1]

            else:
                new_tag = tag

        elif context:

            if '$entity' in context:
                # Remove /$entity tag from context if it was there
                new_tag = context.replace('/$entity', '')

            elif '/' in context:
                new_tag = context.split('/')[-1]

            # Remove the plural 's'
            new_tag = new_tag.rstrip('s')

        else:
            raise ValueError('No value received.')

        return 'Graph' + new_tag[0].upper() + new_tag[1:]
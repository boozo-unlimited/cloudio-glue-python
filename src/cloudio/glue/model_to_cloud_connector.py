# -*- coding: utf-8 -*-

import inspect
import logging
from cloudio.endpoint.interface import CloudioAttributeListener


class Model2CloudConnector(CloudioAttributeListener):
    """Connects a class to cloud.iO and provides helper methods to update attributes in the cloud.

    Inheriting from this class adds the possibility to update changes to cloud.iO.
    In case the attributes have the 'write' constraint they are able to receive
    changes (@set commands) from cloud.iO.
    """

    log = logging.getLogger(__name__)

    def __init__(self, **kwargs):
        super(Model2CloudConnector, self).__init__(**kwargs)

        self._attribute_mapping = None
        self._cloudio_node = None

    def set_attribute_mapping(self, attribute_mapping):
        self._attribute_mapping = attribute_mapping
        if self._cloudio_node:
            self._setup_attribute_mapping()

    def set_cloudio_buddy(self, cloudio_node):
        """Sets the counterpart of the Model on the cloud side.

        :param cloudio_node:
        :type cloudio_node: CloudioNode
        """
        assert self._cloudio_node is None, 'Cloudio buddy can be set only once!'
        self._cloudio_node = cloudio_node

        if self._attribute_mapping:
            # Map write attributes
            self._setup_attribute_mapping()
            # Now cloud.iO node is ready
            self._on_cloudio_node_created()

    def _on_cloudio_node_created(self):
        """Called after cloud.iO node is connected to the model.

        Reimplement this method the perform actions to be done after
        cloud.iO node is created.
        """
        pass

    def create_cloud_io_node(self, cloudio_endpoint):
        """Creates the cloud.iO node for this object

        adds it to the cloud.iO endpoint and connects both objects together.

        :param cloudio_endpoint The endpoint to add the node to
        :type cloudio_endpoint CloudioEndpoint
        """
        from cloudio.endpoint.runtime import CloudioRuntimeNode
        from cloudio.endpoint.runtime import CloudioRuntimeObject

        if self._attribute_mapping is not None:
            # Create the node which will represent this object in the cloud
            cloudio_runtime_node = CloudioRuntimeNode()
            cloudio_runtime_node.declare_implemented_interface('NodeInterface')

            # Create cloud.iO attributes and add them to the corresponding cloud.iO object
            for model_attribute_name, cloudio_attribute_mapping in self._attribute_mapping.items():
                if 'topic' in cloudio_attribute_mapping:
                    # Convert from 'human readable topic' to 'location stack' representation
                    location_stack = self._location_stack_from_topic(cloudio_attribute_mapping['topic'])
                    # Get the cloudio object needed to add the attribute. Create object branch structure
                    # if needed
                    cloudio_runtime_object = self.create_cloudio_object(cloudio_runtime_node, location_stack.copy())

                    # Add attribute to object
                    cloudio_runtime_object.add_attribute(name=location_stack[0],
                                                         atype=cloudio_attribute_mapping['attributeType'])
                else:
                    cloudio_runtime_object = cloudio_runtime_node.find_object([cloudio_attribute_mapping['objectName'],
                                                                               'objects'])
                    if cloudio_runtime_object is None:
                        # Create object
                        cloudio_runtime_object = CloudioRuntimeObject()
                        # Add object to the node
                        cloudio_runtime_node.add_object(cloudio_attribute_mapping['objectName'], cloudio_runtime_object)

                    # Add attribute to object
                    cloudio_runtime_object.add_attribute(name=cloudio_attribute_mapping['attributeName'],
                                                         atype=cloudio_attribute_mapping['attributeType'])

            # Add node to endpoint
            cloudio_endpoint.add_node(self.__class__.__name__, cloudio_runtime_node)

            # Connect cloud.iO node to this object
            self.set_cloudio_buddy(cloudio_runtime_node)
        else:
            self.log.warning('Attribute \'_attribute_mapping\' needs to be initialized to create cloud.iO node!')

    def create_cloudio_object(self, cloudio_runtime_node_or_object, location_stack):
        """Creates and returns the object structure described in location stack.
        
        If the object structure is already present in the node, the last branch object is returned.

        :param cloudio_runtime_node_or_object The node/object in where to search for the cloudio object
        :type cloudio_runtime_node_or_object CloudioRuntimeNode or CloudioRuntimeObject
        :param location_stack The location stack
        :return list
        :rtype CloudioRuntimeObject
        """

        object_stack = location_stack[-2:]  # Get next branch information (last two elements)
        location_stack = location_stack[:-2]  # and remove it from location stack

        if object_stack[-1] == 'objects':  # Check last element in list
            cloudio_runtime_object = cloudio_runtime_node_or_object.find_object(object_stack.copy())
            if not cloudio_runtime_object:
                from cloudio.endpoint.runtime import CloudioRuntimeObject

                # Create object
                cloudio_runtime_object = CloudioRuntimeObject()
                # Add object to the node (or object)
                cloudio_runtime_node_or_object.add_object(object_stack[0], cloudio_runtime_object)

            # Recursively create/get objects
            return self.create_cloudio_object(cloudio_runtime_object, location_stack)
        return cloudio_runtime_node_or_object

    def _setup_attribute_mapping(self):
        assert self._attribute_mapping
        assert self._cloudio_node

        for model_attribute_name, cloudio_attribute_mapping in self._attribute_mapping.items():
            # Add listener to attributes that can be changed from the cloud (constraint: 'write')
            if 'write' in cloudio_attribute_mapping['constraints']:
                if 'topic' in cloudio_attribute_mapping:
                    # take new style

                    # Convert from 'human readable topic' to 'location stack' representation
                    location_stack = self._location_stack_from_topic(cloudio_attribute_mapping['topic'])
                else:
                    self.log.warning('Mapping entries \'objectName\' and \'attributeName\' will be replaced by '
                                     '\'topic\' in future releases! Consider updating your code!')
                    location_stack = [cloudio_attribute_mapping['attributeName'], 'attributes',
                                      cloudio_attribute_mapping['objectName'], 'objects']
                cloudio_attribute_object = self._cloudio_node.find_attribute(location_stack)

                if cloudio_attribute_object:
                    cloudio_attribute_object.add_listener(self)
                else:
                    if 'topic' in cloudio_attribute_mapping:
                        self.log.warning(
                            'Could not map to Cloud.iO attribute. Cloud.iO attribute \'%s\' not found!' %
                            cloudio_attribute_mapping['topic'])
                    else:
                        self.log.warning(
                            'Could not map to Cloud.iO attribute. Cloud.iO attribute \'%s/%s\' not found!' %
                            (cloudio_attribute_mapping['objectName'], cloudio_attribute_mapping['attributeName']))

    def _location_stack_from_topic(self, topic, take_raw_topic=False):
        """Converts attribute topic from 'human readable topic' to 'location stack' representation.

        :return A list containing the location stack
        :rtype list

        Example:
            topic: 'afe.core.properties.user-pwm-enable' gets converted to
            location_stack: ['user-pwm-enable', 'attributes', 'properties', 'objects', 'core', 'objects']
        """
        assert isinstance(topic, str)

        topic_levels = topic.split('.')
        # Remove first entry if it is the name of the cloud.iO node
        if not take_raw_topic and self._cloudio_node and topic_levels[0] == self._cloudio_node.get_name():
            topic_levels = topic_levels[1:]

        # Add entries 'objects' and 'attributes' as needed
        expanded_topic_levels = []
        for index, topic_level in enumerate(topic_levels):
            if index < len(topic_levels) - 1:
                expanded_topic_levels.append('objects')
            else:
                expanded_topic_levels.append('attributes')
            expanded_topic_levels.append(topic_level)

        # Reverse topic_level entries
        location_stack = expanded_topic_levels[::-1]
        return location_stack

    def attribute_has_changed(self, cloudio_attr, from_cloud: bool):
        """Implementation of CloudioAttributeListener interface

        This method is called if an attribute change comes from the cloud.
        """
        found_model_attribute = False
        model_attribute_name = None

        # Get the corresponding mapping
        for mod_attr_name, cl_att_mapping in self._attribute_mapping.items():
            if 'topic' in cl_att_mapping:
                if 'write' in cl_att_mapping['constraints']:
                    location_stack = self._location_stack_from_topic(cl_att_mapping['topic'])

                    if cloudio_attr.get_name() in location_stack[0] and \
                            cloudio_attr.get_parent().get_name() in location_stack[2]:
                        model_attribute_name = mod_attr_name
                        # cloudio_attribute_mapping = cl_att_mapping
                        break

            else:
                if cl_att_mapping['objectName'] == cloudio_attr.get_parent().get_name() and \
                        cl_att_mapping['attributeName'] == cloudio_attr.get_name() and \
                        'write' in cl_att_mapping['constraints']:
                    model_attribute_name = mod_attr_name
                    # cloudio_attribute_mapping = cl_att_mapping
                    break

        # Leave if nothing found
        if model_attribute_name is None:
            return found_model_attribute

        # Strategy:
        # 1. Try to call method 'on_attribute_set_from_cloud(attribute_name, cloudio_attr)'
        # 2. Search method with 'set_<attribute-name>_from_cloud(value)
        # 3. Search method with same name
        # 4. Search setter method of attribute
        # 5. Search the attribute and access it directly

        # Try call method 'on_attribute_set_from_cloud(attribute_name, cloudio_attr)'
        if not found_model_attribute:
            general_callback_method_name = 'on_attribute_set_from_cloud'
            if hasattr(self, general_callback_method_name):
                method = getattr(self, general_callback_method_name)
                if inspect.ismethod(method):
                    try:  # Try to call the method. Maybe it fails because of wrong number of parameters
                        method(model_attribute_name, cloudio_attr)
                        found_model_attribute = True
                    except TypeError as type_error:
                        self.log.error('Exception : %s' % type_error)

        # Search method with 'set_<attribute-name>_from_cloud(value)
        if not found_model_attribute:
            specific_callback_method_name = 'on_' + model_attribute_name + '_set_from_cloud'
            if hasattr(self, specific_callback_method_name):
                method = getattr(self, specific_callback_method_name)
                if inspect.ismethod(method):
                    try:  # Try to call the method. Maybe it fails because of wrong number of parameters
                        method(cloudio_attr.get_value())
                        found_model_attribute = True
                    except TypeError as type_error:
                        self.log.error('Exception : %s' % type_error)

        # Check if provided name is already a method
        if not found_model_attribute:
            if hasattr(self, model_attribute_name):
                method = getattr(self, model_attribute_name)
                # Try to directly access it
                if inspect.ismethod(method):
                    try:  # Try to call the method. Maybe it fails because of wrong number of parameters
                        method(cloudio_attr.get_value())  # Call method and pass value by parameter
                        found_model_attribute = True
                    except Exception:
                        pass

        # Try to set attribute using setter method
        if not found_model_attribute:
            # Try to find a setter method
            if model_attribute_name[0:3] == 'set':
                set_method_name = model_attribute_name
            else:
                set_method_name = 'set' + model_attribute_name[0].upper() + model_attribute_name[1:]
            if hasattr(self, set_method_name):
                method = getattr(self, set_method_name)
                if inspect.ismethod(method):
                    method(cloudio_attr.get_value())  # Call method with an pass value py parameter
                    found_model_attribute = True

        # Try to set attribute by name
        if not found_model_attribute:
            if hasattr(self, model_attribute_name):
                if hasattr(self, model_attribute_name):
                    attr = getattr(self, model_attribute_name)
                    # It should not be a method
                    if not inspect.ismethod(attr):
                        setattr(self, model_attribute_name, cloudio_attr.get_value())
                        found_model_attribute = True

        if not found_model_attribute:
            self.log.info('Did not find attribute for \'%s\'!' % cloudio_attr.get_name())
        else:
            self.log.info('Cloud.iO @set attribute \'' + model_attribute_name + '\' to ' +
                          str(cloudio_attr.get_value()))

        return found_model_attribute

    def _update_cloudio_attribute(self, model_attribute_name, model_attribute_value, force=False):
        """Updates value of the attribute on the cloud.

        Only one thread should be responsible to call this method, means this
        method is not thread-safe.

        It might not be a good idea to call this method using the thread serving the MQTT
        client connection!
        """
        assert not inspect.ismethod(model_attribute_value), 'Value must be of standard type!'

        if (self.has_valid_data() or force) and self._cloudio_node:
            if model_attribute_name in self._attribute_mapping:
                # Get cloudio mapping for the model attribute
                cloudio_attribute_mapping = self._attribute_mapping[model_attribute_name]

                if 'topic' in cloudio_attribute_mapping and cloudio_attribute_mapping['topic']:
                    location_stack = self._location_stack_from_topic(cloudio_attribute_mapping['topic'])
                else:
                    if 'attributeName' in cloudio_attribute_mapping:
                        # Construct the location stack (inverse topic structure)
                        location_stack = [cloudio_attribute_mapping['attributeName'], 'attributes',
                                          cloudio_attribute_mapping['objectName'], 'objects']
                    else:
                        location_stack = []

                # Leave if location_stack could not be constructed
                if not location_stack:
                    return

                if 'toCloudioValueConverter' in cloudio_attribute_mapping:
                    model_attribute_value = cloudio_attribute_mapping['toCloudioValueConverter'](model_attribute_value)

                cloudio_attribute_object = None
                # Get cloud.iO attribute
                try:
                    cloudio_attribute_object = self._cloudio_node.find_attribute(location_stack)
                except KeyError as e:
                    self.log.warning('Did not find cloud.iO object/attribute %s!' % e)

                if cloudio_attribute_object:
                    # Update only if force is true or model attribute value is different than that in the cloud
                    if force is True or model_attribute_value != cloudio_attribute_object.get_value():
                        cloudio_attribute_object.set_value(model_attribute_value)  # Set the new value on the cloud
                else:
                    self.log.warning('Did not find cloud.iO attribute for \'{}\' model attribute!'.
                                     format(model_attribute_name))
            else:
                self.log.warning('Did not find cloud.iO mapping for model attribute \'{}\'!'.
                                 format(model_attribute_name))

    def _update_cloudio_attributes(self, model=None, force=True):
        """Updates all cloud.iO attributes which where changed in model.

        In case the parameter force is set to true, the update to the cloud is forced.
        """
        if self.has_valid_data() and self._cloudio_node:
            model = model if model is not None else self

            for modelAttributeName, cloudioAttributeMapping in self._attribute_mapping.items():
                # Only update attributes with 'read' or 'static' constraints
                if 'read' in cloudioAttributeMapping['constraints'] or 'static' in \
                        cloudioAttributeMapping['constraints']:
                    try:
                        attribute_value = getattr(model, modelAttributeName)
                        # Update attribute in the cloud
                        self._update_cloudio_attribute(modelAttributeName, attribute_value, force)
                    except Exception:
                        self.log.warning('Attribute \'%s\' in model not found!' % modelAttributeName)

    def _force_update_of_cloudio_attributes(self, model=None):
        """Forces updated of cloud.iO attributes.

        It is made only to get a fluent graph on Grafana. May should become a feature of cloud.iO
        micro-services.
        """
        self._update_cloudio_attributes(model=model, force=True)

    def has_valid_data(self):
        """Returns true if model object has valid data.

        Reimplement this method in derived class to change the behavior

        :return Default implementation returns always true.
        """
        return True

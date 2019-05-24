# -*- coding: utf-8 -*-


from six import iteritems
import os
import inspect
import logging


from cloudio.interface.attribute_listener import AttributeListener

version = ''
# Get cloudio-glue-python version info from init file
with open(os.path.dirname(os.path.realpath(__file__)) + '/__init__.py') as vf:
    content = vf.readlines()
    for line in content:
        if '__version__' in line:
            values = line.split('=')
            version = values[1]
            version = version.strip('\n')
            version = version.strip('\r')
            version = version.replace('\'', '')
            version = version.strip(' ')
            break

# Enable logging
logging.basicConfig(format='%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.DEBUG)
logging.getLogger(__name__).setLevel(logging.INFO)  # DEBUG, INFO, WARNING, ERROR, CRITICAL
logging.getLogger(__name__).info('cloudio-glue-python version: %s' % version)

# Links:
# - http://stackoverflow.com/questions/5189699/how-can-i-make-a-class-property-in-python
# - http://www.artima.com/weblogs/viewpost.jsp?thread=240845
# - https://www.codementor.io/python/tutorial/advanced-use-python-decorators-class-function
# - http://krzysztofzuraw.com/blog/2016/python-class-decorators.html
#
class cloudio_attribute(object):
    """Decorator class adding the possibility to auto-update a model attribute to the cloud.iO whenever it changes.

    The model attribute's name corresponds to the method which gets decorated with this
    decorator (similar to the @property decorator).
    """
    def __init__(self, fget, fset=None):
        self._fget = fget
        self._fset = fset

    def __get__(self, obj, the_type=None):
        """
        :return: A value
        """
        try:
            # Try if fget method is an other descriptor
            return self._fget.__get__(obj, the_type)()
        except:
            pass

        try:
            return self._fget.__get__(obj)
        except:
            # Call real fget method
            return self._fget(obj)      # TODO: Check when this case arrives!

    def __set__(self, obj, value):

        try:
            # Try if fget method is an other descriptor
            ret_value = self._fget.__set__(obj, value)
        except:
            if not self._fset:
                raise AttributeError('can\'t set attribute')
            # Use setter method to assign new value
            ret_value = self._fset.__get__(obj)(value)

        # Update value on the cloud
        # Give as second parameter the value using the fget.__get__ property and
        # not the value parameter. It may be different.
    #        obj._updateCloudioAttribute(self._fget.__name__, self._fget.__get__(obj)())
        obj._updateCloudioAttribute(self._fget.__name__, self.__get__(obj))
        return ret_value

    def setter(self, fset):
        """Explicitly sets the setter method for the attribute.
        """
        # Check if fget method is an other descriptor
        if hasattr(self._fget, 'setter'):
            # Give the fset method to it. fset needs to be hierarchically seen a leaf method
            self._fget.setter(fset)
            self._fset = self._fget     # Not sure if this is really necessary
        else:
            self._fset = fset
        return self

    @property
    def __name__(self):
        return self._fget.__name__


class Model2CloudConnector(AttributeListener):
    """Connects a class to cloud.iO and provides helper methods to update attributes in the cloud.

    Inheriting from this class adds the possibility to update changes to cloud.iO.
    In case the attributes have the 'write' constraint they are able to receive
    changes (@set commands) from cloud.iO.
    """

    log = logging.getLogger(__name__)

    def __init__(self, **kwargs):
        super(Model2CloudConnector, self).__init__(**kwargs)

        self._attributeMapping = None
        self._cloudioNode = None

    def setAttributeMapping(self, attributeMapping):
        self._attributeMapping = attributeMapping
        if self._cloudioNode:
            self._setupAttributeMapping()

    def setCloudioBuddy(self, cloudioNode):
        """Sets the counterpart of the Model on the cloud side.

        :param cloudioNode:
        :type cloudioNode: CloudioNode
        """
        assert self._cloudioNode is None, 'Cloudio buddy can be set only once!'
        self._cloudioNode = cloudioNode

        if self._attributeMapping:
            # Map write attributes
            self._setupAttributeMapping()
            # Now cloud.iO node is ready
            self._onCloudioNodeCreated()

    def _onCloudioNodeCreated(self):
        """Called after cloud.iO node is connected to the model.

        Reimplement this method the perform actions to be done after
        cloud.iO node is created.
        """
        pass

    def createCloudIoNode(self, cloudioEndpoint):
        """Creates the cloud.iO node for this object

        adds it to the cloud.iO endpoint and connects both objects together.

        :param cloudioEndpoint The endpoint to add the node to
        :type cloudioEndpoint CloudioEndpoint
        """
        from cloudio.cloudio_runtime_node import CloudioRuntimeNode
        from cloudio.cloudio_runtime_object import CloudioRuntimeObject

        if self._attributeMapping is not None:
            # Create the node which will represent this object in the cloud
            cloudioRuntimeNode = CloudioRuntimeNode()
            cloudioRuntimeNode.declareImplementedInterface(u'NodeInterface')

            # Create cloud.iO attributes and add them to the corresponding cloud.iO object
            for modelAttributeName, cloudioAttributeMapping in iteritems(self._attributeMapping):
                cloudio_runtime_object = cloudioRuntimeNode.findObject([cloudioAttributeMapping['objectName'],
                                                                        'objects'])

                if cloudio_runtime_object is None:
                    # Create object
                    cloudio_runtime_object = CloudioRuntimeObject()
                    # Add object to the node
                    cloudioRuntimeNode.addObject(cloudioAttributeMapping['objectName'], cloudio_runtime_object)

                # Add attribute to object
                cloudio_runtime_object.addAttribute(name=cloudioAttributeMapping['attributeName'],
                                                    type=cloudioAttributeMapping['attributeType'])

            # Add node to endpoint
            cloudioEndpoint.addNode(self.__class__.__name__, cloudioRuntimeNode)

            # Connect cloud.iO node to this object
            self.setCloudioBuddy(cloudioRuntimeNode)
        else:
            self.log.warning(u'Attribute \'_attributeMapping\' needs to be initialized to create cloud.iO node!')
            
    def create_cloudio_object(self, cloudio_runtime_node_or_object, location_stack):
        """Creates and returns the object structure described in location stack.
        
        If the object structure is already present in the node, the last branch object is returned.

        :param cloudio_runtime_node_or_object The node/object in where to search for the cloudio object
        :type cloudio_runtime_node_or_object CloudioRuntimeNode or CloudioRuntimeObject
        :param location_stack The location stack
        :return list
        :rtype CloudioRuntimeObject
        """

        object_stack = location_stack[-2:]           # Get next branch information (last two elements)
        location_stack = location_stack[:-2]        # and remove it from location stack
        
        if object_stack[-1] == 'objects':   # Check last element in list
            cloudio_runtime_object = cloudio_runtime_node_or_object.findObject(object_stack.copy())
            if not cloudio_runtime_object:
                from cloudio.cloudio_runtime_object import CloudioRuntimeObject

                # Create object
                cloudio_runtime_object = CloudioRuntimeObject()
                 # Add object to the node (or object)
                cloudio_runtime_node_or_object.addObject(object_stack[0], cloudio_runtime_object)

            # Recursively create/get objects
            return self.create_cloudio_object(cloudio_runtime_object, location_stack)
        return cloudio_runtime_node_or_object

    def _setupAttributeMapping(self):
        assert self._attributeMapping
        assert self._cloudioNode

        for modelAttributeName, cloudioAttributeMapping in iteritems(self._attributeMapping):
            # Add listener to attributes that can be changed from the cloud (constraint: 'write')
            if 'write' in cloudioAttributeMapping['constraints']:
                if 'topic' in cloudioAttributeMapping:
                    # take new style

                    # Convert from 'human readable topic' to 'location stack' representation
                    location_stack = self._location_stack_from_topic(cloudioAttributeMapping['topic'])
                else:
                    self.log.warning('Mapping entries \'objectName\' and \'attributeName\' will be replaced by '
                                     '\'topic\' in future releases! Consider updating your code!')
                    location_stack = [cloudioAttributeMapping['attributeName'], 'attributes',
                                      cloudioAttributeMapping['objectName'], 'objects']
                cloudio_attribute_object = self._cloudioNode.findAttribute(location_stack)

                if cloudio_attribute_object:
                    cloudio_attribute_object.addListener(self)
                else:
                    self.log.warning('Could not map to Cloud.iO attribute. Cloud.iO attribute \'%s/%s\' not found!' %
                                     (cloudioAttributeMapping['objectName'], cloudioAttributeMapping['attributeName']))

    def _location_stack_from_topic(self, topic, take_raw_topic=False):
        """Converts attribute topic from 'human readable topic' to 'location stack' representation.

        Example:
            topic: 'afe.core.properties.user-pwm-enable' gets converted to
            location_stack: ['user-pwm-enable', 'attributes', 'properties', 'objects', 'core', 'objects']
        """
        assert isinstance(topic, str)

        topic_levels = topic.split('.')
        # Remove first entry if it is the name of the cloud.iO node
        if not take_raw_topic and topic_levels[0] == self._cloudioNode.getName():
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

    def attributeHasChanged(self, cloudioAttribute):
        """Implementation of AttributeListener interface

        This method is called if an attribute change comes from the cloud.
        """
        found_model_attribute = False
        model_attribute_name = None
        cloudio_attribute_mapping = None

        # Get the corresponding mapping
        for modAttrName, clAttMapping in iteritems(self._attributeMapping):
            if 'topic' in clAttMapping:
                if 'write' in clAttMapping['constraints']:
                    location_stack = self._location_stack_from_topic(clAttMapping['topic'])

                    if cloudioAttribute.getName() in location_stack[0] and \
                            cloudioAttribute.getParent().getName() in location_stack[2]:
                        model_attribute_name = modAttrName
                        cloudio_attribute_mapping = clAttMapping
                        break

            else:
                if clAttMapping['objectName'] == cloudioAttribute.getParent().getName() and \
                   clAttMapping['attributeName'] == cloudioAttribute.getName() and \
                        'write' in clAttMapping['constraints']:
                    model_attribute_name = modAttrName
                    cloudio_attribute_mapping = clAttMapping
                    break

        # Leave if nothing found
        if model_attribute_name is None:
            return found_model_attribute

        # Strategy:
        # 1. Try to call method 'on_attribute_set_from_cloud(attribute_name, cloudio_attribute)'
        # 2. Search method with 'set_<attribute-name>_from_cloud(value)
        # 3. Search method with same name
        # 4. Search setter method of attribute
        # 5. Search the attribute and access it directly

        # Try call method 'on_attribute_set_from_cloud(attribute_name, cloudio_attribute)'
        if not found_model_attribute:
            general_callback_method_name = 'on_attribute_set_from_cloud'
            if hasattr(self, general_callback_method_name):
                method = getattr(self, general_callback_method_name)
                if inspect.ismethod(method):
                    try:  # Try to call the method. Maybe it fails because of wrong number of parameters
                        method(model_attribute_name, cloudioAttribute)
                        found_model_attribute = True
                    except TypeError as type_error:
                        self.log.error(u'Exception : %s' % type_error)

        # Search method with 'set_<attribute-name>_from_cloud(value)
        if not found_model_attribute:
            specific_callback_method_name = 'on_' + model_attribute_name + '_set_from_cloud'
            if hasattr(self, specific_callback_method_name):
                method = getattr(self, specific_callback_method_name)
                if inspect.ismethod(method):
                    try:  # Try to call the method. Maybe it fails because of wrong number of parameters
                        method(cloudioAttribute.getValue())
                        found_model_attribute = True
                    except TypeError as type_error:
                        self.log.error(u'Exception : %s' % type_error)

        # Check if provided name is already a method
        if not found_model_attribute:
            if hasattr(self, model_attribute_name):
                method = getattr(self, model_attribute_name)
                # Try to directly access it
                if inspect.ismethod(method):
                    try:  # Try to call the method. Maybe it fails because of wrong number of parameters
                        method(cloudioAttribute.getValue())  # Call method and pass value by parameter
                        found_model_attribute = True
                    except: pass

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
                    method(cloudioAttribute.getValue())     # Call method with an pass value py parameter
                    found_model_attribute = True

        # Try to set attribute by name
        if not found_model_attribute:
            if hasattr(self, model_attribute_name):
                if hasattr(self, model_attribute_name):
                    attr = getattr(self, model_attribute_name)
                    # It should not be a method
                    if not inspect.ismethod(attr):
                        setattr(self, model_attribute_name, cloudioAttribute.getValue())
                        found_model_attribute = True

        if not found_model_attribute:
            self.log.info('Did not find attribute for \'%s\'!' % cloudioAttribute.getName())
        else:
            self.log.info('Cloud.iO @set attribute \'' + model_attribute_name + '\' to ' +
                          str(cloudioAttribute.getValue()))

        return found_model_attribute

    def _updateCloudioAttribute(self, modelAttributeName, modelAttributeValue, force=False):
        """Updates value of the attribute on the cloud.

        Only one thread should be responsible to call this method, means this
        method is not thread-safe.

        It might not be a good idea to call this method using the thread serving the MQTT
        client connection!
        """
        assert not inspect.ismethod(modelAttributeValue), 'Value must be of standard type!'

        if (self.hasValidData() or force) and self._cloudioNode:
            if modelAttributeName in self._attributeMapping:
                # Get cloudio mapping for the model attribute
                cloudio_attribute_mapping = self._attributeMapping[modelAttributeName]

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
                    modelAttributeValue = cloudio_attribute_mapping['toCloudioValueConverter'](modelAttributeValue)

                cloudio_attribute_object = None
                # Get cloud.iO attribute
                try:
                    cloudio_attribute_object = self._cloudioNode.findAttribute(location_stack)
                except KeyError as e:
                    self.log.warning('Did not find cloud.iO object/attribute %s!' % e)

                if cloudio_attribute_object:
                    # Update only if force is true or model attribute value is different than that in the cloud
                    if force is True or modelAttributeValue != cloudio_attribute_object.getValue():
                        cloudio_attribute_object.setValue(modelAttributeValue)    # Set the new value on the cloud
                else:
                    self.log.warning('Did not find cloud.iO attribute for \'%s\' model attribute!' % modelAttributeName)
            else:
                self.log.warning('Did not find cloud.iO mapping for model attribute \'%s\'!' % modelAttributeName)

    def _updateCloudioAttributes(self, model=None, force=True):
        """Updates all cloud.iO attributes which where changed in model.

        In case the parameter force is set to true, the update to the cloud is forced.
        """
        if self.hasValidData() and self._cloudioNode:
            model = model if model is not None else self

            for modelAttributeName, cloudioAttributeMapping in iteritems(self._attributeMapping):
                # Only update attributes with 'read' or 'static' constraints
                if 'read' in cloudioAttributeMapping['constraints'] or 'static' in \
                        cloudioAttributeMapping['constraints']:
                    try:
                        attributeValue = getattr(model, modelAttributeName)
                        # Update attribute in the cloud
                        self._updateCloudioAttribute(modelAttributeName, attributeValue, force)
                    except Exception as e:
                        self.log.warning('Attribute \'%s\' in model not found!' % modelAttributeName)

    def _forceUpdateOfCloudioAttributes(self, model=None):
        """Forces updated of cloud.iO attributes.

        It is made only to get a fluent graph on Grafana. May should become a feature of cloud.iO
        micro-services.
        """
        self._updateCloudioAttributes(model=model, force=True)

    def hasValidData(self):
        """Returns true if model object has valid data.

        Reimplement this method in derived class to change the behavior

        :return Default implementation returns always true.
        """
        return True

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

    def __get__(self, obj, type=None):
        """
        :return: A value
        """
        try:
            # Try if fget method is an other descriptor
            return self._fget.__get__(obj, type)()
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
            retValue = self._fget.__set__(obj, value)
        except:
            if not self._fset:
                raise AttributeError('can\'t set attribute')
            # Use setter method to assign new value
            retValue = self._fset.__get__(obj)(value)

        # Update value on the cloud
        # Give as second parameter the value using the fget.__get__ property and
        # not the value parameter. It may be different.
    #        obj._updateCloudioAttribute(self._fget.__name__, self._fget.__get__(obj)())
        obj._updateCloudioAttribute(self._fget.__name__, self.__get__(obj))
        return retValue

    def setter(self, fset):
        """Explicitly sets the setter method for the attribute.
        """
        # Check if fget method is an other descriptor
        if hasattr(self._fget, 'setter'):
            # Give the fset method to it. fset needs to be hierarchically seen a leaf method
            self._fget.setter(fset)
            self._fset = self._fget     # Not sure if this is really necessary
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
                cloudioRuntimeObject = cloudioRuntimeNode.findObject([cloudioAttributeMapping['objectName'], 'objects'])

                if cloudioRuntimeObject is None:
                    # Create object
                    cloudioRuntimeObject = CloudioRuntimeObject()
                    # Add object to the node
                    cloudioRuntimeNode.addObject(cloudioAttributeMapping['objectName'], cloudioRuntimeObject)

                # Add attribute to object
                cloudioRuntimeObject.addAttribute(name=cloudioAttributeMapping['attributeName'],
                                                  type=cloudioAttributeMapping['attributeType'])

            # Add node to endpoint
            cloudioEndpoint.addNode(self.__class__.__name__, cloudioRuntimeNode)

            # Connect cloud.iO node to this object
            self.setCloudioBuddy(cloudioRuntimeNode)
        else:
            self.log.warning(u'Attribute \'_attributeMapping\' needs to be initialized to create cloud.iO node!')

    def _setupAttributeMapping(self):
        assert self._attributeMapping
        assert self._cloudioNode

        for modelAttributeName, cloudioAttributeMapping in iteritems(self._attributeMapping):
            # Add listener to attributes that can be changed from the cloud (constraint: 'write')
            if 'write' in cloudioAttributeMapping['constraints']:
                if 'topic' in cloudioAttributeMapping:
                    # take new style
                    topic_levels = cloudioAttributeMapping['topic'].split('.')
                    # Remove first entry if it is the name o the cloud.iO node
                    if topic_levels[0] == self._cloudioNode.getName():
                        topic_levels = topic_levels[1:]

                    # Add entries 'objects' and 'attributes' as needed
                    expanded_topic_levels = []
                    for index, topic_level in enumerate(topic_levels):
                        if index < len(topic_levels) - 1:
                            expanded_topic_levels.append('objects')
                        else:
                            expanded_topic_levels.append('attributes')
                        expanded_topic_levels.append(topic_level)

                    # Reverse topicLevel entries
                    location_stack = expanded_topic_levels[::-1]
                else:
                    self.log.warning('Mapping entries \'objectName\' and \'attributeName\' will be replaced by \'topic\''
                                     ' in future releases! Consider updating your code!')
                    location_stack = [cloudioAttributeMapping['attributeName'], 'attributes',
                                     cloudioAttributeMapping['objectName'], 'objects']
                cloudioAttribute = self._cloudioNode.findAttribute(location_stack)

                if cloudioAttribute:
                    cloudioAttribute.addListener(self)
                else:
                    self.log.warning('Could not map to Cloud.iO attribute. Cloud.iO attribute \'%s/%s\' not found!' %
                                     (cloudioAttributeMapping['objectName'], cloudioAttributeMapping['attributeName']))

    def _location_stack_from_topic(self, topic, take_raw_topic=False):
        """Converts attribute topic from 'human readable topic' to 'location stack' representation.
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
        foundModelAttribute = False
        modelAttributeName = None
        cloudioAttributeMapping = None

        # Get the corresponding mapping
        for modAttrName, clAttMapping in iteritems(self._attributeMapping):
            if clAttMapping['objectName'] == cloudioAttribute.getParent().getName() and \
               clAttMapping['attributeName'] == cloudioAttribute.getName() and \
                            'write' in clAttMapping['constraints']:
                modelAttributeName = modAttrName
                cloudioAttributeMapping = clAttMapping
                break

        # Leave if nothing found
        if modelAttributeName is None:
            return foundModelAttribute

        # Strategy:
        # 1. Search method with same name
        # 2. Search setter method of attribute
        # 3. Search the attribute and access it directly

        # Check if provided name is already a method
        if not foundModelAttribute:
            if hasattr(self, modelAttributeName):
                method = getattr(self, modelAttributeName)
                # Try to directly access it
                if inspect.ismethod(method):
                    try:  # Try to call the method. Maybe it fails because of wrong number of parameters
                        method(cloudioAttribute.getValue())  # Call method with an pass value py parameter
                        foundModelAttribute = True
                    except: pass

        # Try to set attribute using setter method
        if not foundModelAttribute:
            # Try to find a setter method
            if modelAttributeName[0:3] == 'set':
                setMethodName = modelAttributeName
            else:
                setMethodName = 'set' + modelAttributeName[0].upper() + modelAttributeName[1:]
            if hasattr(self, setMethodName):
                method = getattr(self, setMethodName)
                if inspect.ismethod(method):
                    method(cloudioAttribute.getValue()) # Call method with an pass value py parameter
                    foundModelAttribute = True

        # Try to set attribute by name
        if hasattr(self, modelAttributeName):
            if hasattr(self, modelAttributeName):
                attr = getattr(self, modelAttributeName)
                # It should not be a method
                if not inspect.ismethod(attr):
                    setattr(self, modelAttributeName, cloudioAttribute.getValue())
                    foundModelAttribute = True

        if not foundModelAttribute:
            self.log.info('Did not find attribute for \'%s\'!' % cloudioAttribute.getName())
        else:
            self.log.info('Cloud.iO @set attribute \'' + modelAttributeName + '\' to ' + str(cloudioAttribute.getValue()))

        return foundModelAttribute

    def _updateCloudioAttribute(self, modelAttributeName, modelAttributeValue, force=False):
        """Updates value of the attribute on the cloud.
        """
        assert not inspect.ismethod(modelAttributeValue), 'Value must be of standard type!'

        if (self.hasValidData() or force) and self._cloudioNode:
            if modelAttributeName in self._attributeMapping:
                # Get cloudio mapping for the model attribute
                cloudioAttributeMapping = self._attributeMapping[modelAttributeName]

                # Construct the location stack (inverse topic structure)
                locationStack = [cloudioAttributeMapping['attributeName'], 'attributes',
                                 cloudioAttributeMapping['objectName'], 'objects']

                if 'toCloudioValueConverter' in cloudioAttributeMapping:
                    modelAttributeValue = cloudioAttributeMapping['toCloudioValueConverter'](modelAttributeValue)

                # Get cloud.iO attribute
                cloudioAttribute = self._cloudioNode.findAttribute(locationStack)
                if cloudioAttribute:
                    # Update only if force is true or model attribute value is different than that in the cloud
                    if force is True or modelAttributeValue != cloudioAttribute.getValue():
                        cloudioAttribute.setValue(modelAttributeValue)    # Set the new value on the cloud
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
                if 'read' in cloudioAttributeMapping['constraints'] or 'static' in cloudioAttributeMapping['constraints']:
                    try:
                        attributeValue = getattr(model, modelAttributeName)
                        # Update attribute in the cloud
                        self._updateCloudioAttribute(modelAttributeName, attributeValue, force)
                    except Exception as e:
                        self.log.warning('Attribute \'%s\' in model not found!' % modelAttributeName)
                        pass


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
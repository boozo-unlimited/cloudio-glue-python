# Cloud.iO Glue

## Introduction
This package is an extension to the 
[cloudio-endpoint-python](https://github.com/cloudio-project/cloudio-endpoint-python/tree/master/src/cloudio) 
package providing features not present in the 
[java-endpoint](https://github.com/cloudio-project/cloudio-endpoint-java)
implementation.
It supports the developer with the Model2CloudConnector class and the 
'cloudio_attribute' decorator.

The fast and simple solution to connect an object to the cloud is to inherit 
the class from CloudioNode and automatically all attributes get
synchronized to the cloud. The drawback here is that the developer does not
have the choise to prohibit the synchonization of some attributes.

There is where the Model2CloudConnector class comes in. Inheriting from this
class allows to specify which attribute should be synchronized to the cloud
using the `attribute mapping` feature.

## Model2CloudConnector Class
The Model2CloudConnector class allows to synchonize some attributes of a class.
Which attributes to synchonize is done with an attribute mapping.

To use the Model2CloudConnector class you need to inherit from it and then
specify which of the attributes to synchronize using the setAttributeMapping()
method. 

### Attribute Mapping
Here is an example on how to bring attributes (or properties) x and y of the
ComputerMouse class to the cloud:

```python
    class ComputerMouse(Model2CloudConnector):

        def __init__(self):

            self._x = 0
            self._y = 0

            # Define the attributes which are going to be mapped to the cloud.iO
            self.setAttributeMapping({'x': {'objectName': 'position', 'attributeName': 'x', 'attributeType': float,
                                            'constraints': ('read',)},  # ('read', 'write')
                                      'y': {'objectName': 'position', 'attributeName': 'y', 'attributeType': float,
                                            'constraints': ('read',)},
                                    })

        @property
        def x(self): return self._x

        @x.setter
        def x(self, value): self._x = value
        
        @property
        def y(self): return self._y

        @y.setter
        def y(self, value): self._y = value
```

### Attribute Access Policy
For each attribute the access policy can be specified. Following values can be given
 - read
 - write

or both. 

The **read** access policy allows to read the attribute from the cloud. Giving the
**write** access policy allows to change the attribute via the cloud.

## cloudio_attribute Decorator
An attribute can be automatically synchronized to the cloud by assigning
the `cloudio_attribute` decorator to the property.

To assign for example the decorator to the x property change the code above as follows. Remove
the @property decorator and replace it with the @cloudio_attribute decorator.

The example below shows the @cloudio_attribute decorator applied to the x and y property:

```python
    class ComputerMouse(Model2CloudConnector)

        def __init__()

            self._x = 0
            self._y = 0

            # Define the attributes which are going to be mapped to the cloud.iO
            self.setAttributeMapping({'x': {'objectName': 'position', 'attributeName': 'x', 'attributeType': float,
                                            'constraints': ('read',)},  # ('read', 'write')
                                      'y': {'objectName': 'position', 'attributeName': 'y', 'attributeType': float,
                                            'constraints': ('read',)},
                                    })

        @cloudio_attribute
        def x(self): return self._x

        @x.setter
        def x(self, value): self._x = value
        
        @cloudio_attribute
        def y(self): return self._y

        @y.setter
        def y(self, value): self._y = value
```

Now every time the x or y property gets changed, the value is automatically updated to the cloud.


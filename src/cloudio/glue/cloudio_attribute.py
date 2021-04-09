# -*- coding: utf-8 -*-

import inspect
import logging
import traceback


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
            # Try if fget method is another descriptor
            return self._fget.__get__(obj, the_type)()
        except TypeError:
            pass

        return self._fget.__get__(obj)

    def __set__(self, obj, value):
        """Assigns value to decorated attribute.

        :param obj: The composite instance containing the attribute
        :param value: The value to assign to the attribute
        :return: Value returned by the setter method.
        """

        try:
            # Try if fget method is another descriptor
            ret_value = self._fget.__set__(obj, value)
        except Exception:
            if not self._fset:
                raise AttributeError('Can\'t set attribute. No setter provided!')
            # Use setter method to assign new value
            ret_value = self._fset.__get__(obj)(value)

        try:
            # Update value on the cloud by calling method '_update_cloudio_attribute'
            # which must be provided by the instance having the cloudio_attribute
            # decorated attribute.
            #
            # Give as second parameter the value using the fget.__get__ property and
            # not the value parameter. It may be different.
            #        obj._update_cloudio_attribute(self._fget.__name__, self._fget.__get__(obj)())
            obj._update_cloudio_attribute(self.__name__, self.__get__(obj))
        except (AttributeError, TypeError):
            traceback.print_exc()
            callback_name = '_update_cloudio_attribute'

            if not hasattr(obj, callback_name):
                logging.error(f'Method \'{callback_name}\' not provided!')
            else:
                attr = getattr(obj, callback_name)
                # It should be a method
                if not inspect.ismethod(attr):
                    logging.error(f'\'{callback_name}\' must be a method!')
        return ret_value

    def setter(self, fset):
        """Explicitly sets the setter method for the attribute.
        """
        # Check if fget method is another descriptor
        if hasattr(self._fget, 'setter'):
            # Give the fset method to it. fset needs to be hierarchically seen a leaf method
            self._fget.setter(fset)
            self._fset = fset
        else:
            self._fset = fset
        return self

    @property
    def __name__(self):
        try:
            return self._fget.__name__
        except AttributeError:
            # @property does not have an attribute '__name__'. We need to go
            # deeper to reach the name of the decorated method
            return self._fget.fget.__name__

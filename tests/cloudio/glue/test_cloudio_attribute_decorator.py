#!/usr/bin/env python
# -*- coding: utf-8 -*-


import logging
import unittest

from tests.cloudio.glue.paths import update_working_directory

update_working_directory()  # Needed when: 'pipenv run python -m unittest tests/cloudio/glue/{this_file}.py'


class TestCloudioAttributeDecorator(unittest.TestCase):
    """Tests @cloudio_attriubte decorator.
    """

    log = logging.getLogger(__name__)

    # @unittest.skip('because adding a new test')
    def test_cloudio_attribute_getter(self):
        from cloudio.glue import cloudio_attribute

        # Class having a property decorated with '@cloudio_attribute'
        class Endpoint(object):

            def __init__(self):
                super(Endpoint, self).__init__()
                self._an_attribute = 10
                self._enable = True
                self._name = 'glacier'
                self._speed = 1000.0

            @cloudio_attribute
            def an_attribute(self):
                return self._an_attribute

            @cloudio_attribute
            @property
            def enable(self):
                return self._enable

            # Construct below is not working (@cloudio_attribute needs to come before @property)
            @property
            @cloudio_attribute
            def name(self):
                return self._name

            # Another way to construct a cloudio_attribute
            def _get_speed(self):
                return self._speed

            speed = cloudio_attribute(_get_speed)

            @cloudio_attribute
            def raises_exception(self):
                raise Exception()

            @cloudio_attribute
            @property
            def raises_exception_too(self):
                raise Exception()

        ep = Endpoint()

        self.assertTrue(ep.an_attribute == 10)
        self.assertTrue(ep.enable is True)

        with self.assertRaises(TypeError):
            if ep.name == 'glacier':
                pass

        self.assertTrue(ep.speed == 1000.0)

        # Check Exception handling
        with self.assertRaises(Exception):
            result = ep.raises_exception

        with self.assertRaises(Exception):
            result = ep.raises_exception_too

    # @unittest.skip('because adding a new test')
    def test_cloudio_attribute_setter_no_cloudio_callback(self):
        from cloudio.glue import cloudio_attribute

        # Class having a property decorated with '@cloudio_attribute'
        class Endpoint(object):

            def __init__(self):
                super(Endpoint, self).__init__()
                self._an_attribute = 10

            @cloudio_attribute
            def an_attribute(self):
                return self._an_attribute

            @an_attribute.setter
            def an_attribute(self, value):
                self._an_attribute = value

            def get_hook(self):
                return 0

            hook = cloudio_attribute(get_hook)

        ep = Endpoint()

        self.assertTrue(ep.an_attribute == ep._an_attribute)
        with self.assertLogs() as log:
            ep.an_attribute = 21
            self.assertEqual(log.output, ["ERROR:root:Method '_update_cloudio_attribute' not provided!"])

        with self.assertRaises(AttributeError):
            ep.hook = 10

    # @unittest.skip('because adding a new test')
    def test_cloudio_attribute_setter_with_bad_cloudio_callback(self):
        from cloudio.glue import cloudio_attribute

        # Class having a property decorated with '@cloudio_attribute'
        class BadEndpoint(object):

            def __init__(self):
                super(BadEndpoint, self).__init__()
                self._update_cloudio_attribute = 'not a method'

            @cloudio_attribute
            def silly(self):
                return 'silly'

            @silly.setter
            def silly(self, value):
                pass

        ep = BadEndpoint()
        ep.silly = False

    # @unittest.skip('because adding a new test')
    def test_cloudio_attribute_setter_with_cloudio_callback(self):
        from cloudio.glue import cloudio_attribute

        # Class having a property decorated with '@cloudio_attribute'
        class Endpoint(object):

            def __init__(self):
                super(Endpoint, self).__init__()
                self._star = 'patrick'

                self.model_attribute_name = None
                self.model_attribute_value = None

            def _update_cloudio_attribute(self, model_attribute_name, model_attribute_value):
                self.model_attribute_name = model_attribute_name
                self.model_attribute_value = model_attribute_value

            @cloudio_attribute
            def star(self):
                return self._star

            @star.setter
            def star(self, value):
                self._star = value

        ep = Endpoint()

        self.assertEqual(ep.star, 'patrick')
        ep.star = 'sun'
        self.assertEqual(ep.star, 'sun')
        self.assertEqual(ep.model_attribute_name, 'star')
        self.assertEqual(ep.model_attribute_value, 'sun')

    def test_cloudio_attribute_explicit_setter(self):
        from cloudio.glue import cloudio_attribute

        # Class having a property decorated with '@cloudio_attribute'
        class Endpoint(object):

            def __init__(self):
                super(Endpoint, self).__init__()
                self._enable = False

                self.model_attribute_name = None
                self.model_attribute_value = None

            def _update_cloudio_attribute(self, model_attribute_name, model_attribute_value):
                self.model_attribute_name = model_attribute_name
                self.model_attribute_value = model_attribute_value

            @cloudio_attribute
            @property
            def enable(self):
                return self._enable

            @enable.setter
            def enable(self, value):
                self._enable = value

        ep = Endpoint()

        ep.enable = True
        self.assertEqual(ep.enable, True)
        self.assertEqual(ep.model_attribute_name, 'enable')
        self.assertEqual(ep.model_attribute_value, True)

        ep.enable = False
        self.assertEqual(ep.enable, False)
        self.assertEqual(ep.model_attribute_name, 'enable')
        self.assertEqual(ep.model_attribute_value, False)


if __name__ == '__main__':
    # Enable logging
    logging.basicConfig(format='%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.INFO)

    unittest.main()

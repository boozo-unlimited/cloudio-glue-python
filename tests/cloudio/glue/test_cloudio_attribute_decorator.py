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

        ep = Endpoint()

        self.assertTrue(ep.an_attribute == 10)
        self.assertTrue(ep.enable is True)

        with self.assertRaises(TypeError):
            ep.name == 'glacier'

        self.assertTrue(ep.speed == 1000.0)


if __name__ == '__main__':
    # Enable logging
    logging.basicConfig(format='%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.INFO)

    unittest.main()

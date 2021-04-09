#!/usr/bin/env python
# -*- coding: utf-8 -*-


import logging
import unittest

from tests.cloudio.glue.paths import update_working_directory

update_working_directory()  # Needed when: 'pipenv run python -m unittest tests/cloudio/glue/{this_file}.py'

VACUUM_CLEANER_NAME = 'VacuumCleanerEndpoint'


class TestCloudioGlueVersion(unittest.TestCase):
    """Tests package version.
    """

    log = logging.getLogger(__name__)

    def test_version_01(self):
        from cloudio import glue

        print(glue.version)

        self.assertTrue(isinstance(glue.version, str))
        self.assertIsNot(glue.version, '')
        self.assertTrue(len(glue.version.split('.')) == 3)  # Want to see 'x.y.z'

    def test_version_02(self):
        from cloudio.glue import version

        print(version)

        self.assertTrue(isinstance(version, str))
        self.assertIsNot(version, '')
        self.assertTrue(len(version.split('.')) == 3)  # Want to see 'x.y.z'

    def test_version_03(self):
        import cloudio.glue.version as version

        self.assertTrue(isinstance(version, str))
        self.assertIsNot(version, '')
        self.assertTrue(len(version.split('.')) == 3)  # Want to see 'x.y.z'


class TestCloudioGlueVersionMain(unittest.TestCase):
    """Test call version.py.

    - https://medium.com/opsops/how-to-test-if-name-main-1928367290cb
    - https://stackoverflow.com/questions/5850268/how-to-test-or-mock-if-name-main-contents
    """

    log = logging.getLogger(__name__)

    def setUp(self):
        self.version = __import__('cloudio.glue.version', globals(), locals(), [''], 0)

    def tearDown(self):
        import sys
        del sys.modules[self.version.__name__]

    def test_version_04(self):
        print('Calling version.py\'s main():')
        self.version.main()


if __name__ == '__main__':
    # Enable logging
    logging.basicConfig(format='%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.INFO)

    unittest.main()

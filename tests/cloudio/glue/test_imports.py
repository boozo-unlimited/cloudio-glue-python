#!/usr/bin/env python
# -*- coding: utf-8 -*-


import logging
import unittest
from tests.cloudio.glue.paths import update_working_directory

update_working_directory()  # Needed when: 'pipenv run python -m unittest tests/cloudio/glue/{this_file}.py'


class TestCloudioImports(unittest.TestCase):
    """Tests package version.
    """

    log = logging.getLogger(__name__)

    def test_import_base(self):
        import src                      # Call src/__init__.py
        import cloudio.glue
        import cloudio.glue.version as version

        print(version)

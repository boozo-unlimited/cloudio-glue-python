# -*- coding: utf-8 -*-

# Tell python that there are more sub-packages present, physically located elsewhere.
# See: https://stackoverflow.com/questions/8936884/python-import-path-packages-with-the-same-name-in-different-folders
import pkgutil

__path__ = pkgutil.extend_path(__path__, __name__)

import logging
from .version import __version__
from .cloudio_attribute import cloudio_attribute
from .model_to_cloud_connector import Model2CloudConnector

# Enable logging
logging.basicConfig(format='%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.DEBUG)
logging.getLogger(__name__).setLevel(logging.INFO)  # DEBUG, INFO, WARNING, ERROR, CRITICAL
logging.getLogger(__name__).info(f'cloudio-glue-python version: {__version__}')

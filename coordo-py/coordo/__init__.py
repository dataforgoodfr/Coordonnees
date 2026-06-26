# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

import warnings
import logging

LOG_LEVEL = logging.INFO
LOGGING_FORMAT = '%(asctime)s [%(levelname)s] %(message)s'
DATE_FORMAT = '%Y-%m-%d %H-%M-%S'

logging.basicConfig(
    level=LOG_LEVEL, 
    format=LOGGING_FORMAT, 
    datefmt=DATE_FORMAT
)


# ignore warnings due to shadowing of Pydantic's "schema" field in "Resource"
REGEX_TO_IGNORE = (
    'Field name "schema" in "Resource" shadows an attribute in parent "(Base)?Model"'
)
warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    module="dplib",
    message=REGEX_TO_IGNORE,
)

warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    module="coordo",
    message=REGEX_TO_IGNORE,
)

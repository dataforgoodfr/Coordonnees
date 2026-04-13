# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

import warnings
from enum import Enum


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


class LoadingStrategy(str, Enum):
    raise_error = "raise_error"
    overwrite = "overwrite"
    append = "append"
    append_strict = "append_strict"

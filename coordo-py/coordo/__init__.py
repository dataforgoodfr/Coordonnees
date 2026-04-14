# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

import warnings


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


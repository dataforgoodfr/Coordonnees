# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

import pandas as pd

from coordo.loaders.loader import Loader


def test_dataframe_to_records_replaces_invalid_unicode():
    df = pd.DataFrame(
        {
            "name": pd.Series(["forêt 🦉\udcc0"], dtype=object),
            "number": [1],
        }
    )

    assert Loader._dataframe_to_records(df) == [{"name": "forêt 🦉?", "number": 1}]


def test_dataframe_to_records_replaces_invalid_utf8_bytes():
    df = pd.DataFrame(
        {"value": pd.Series([b"\xc0\xaf"], dtype=object)}
    )

    assert Loader._dataframe_to_records(df) == [{"value": "��"}]

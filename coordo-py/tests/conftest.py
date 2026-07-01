# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

import pytest 
from pathlib import Path

DATA_DIR = Path("tests/test_data")
CLI_TEST_DATA_DIR = DATA_DIR / "cli"


@pytest.fixture
def input_files():
    input_dir = CLI_TEST_DATA_DIR / "input"
    return {f.name: str(f) for f in input_dir.iterdir()}


@pytest.fixture
def output_files():
    output_dir = CLI_TEST_DATA_DIR / "output"
    return {f.name: str(f) for f in output_dir.iterdir()}

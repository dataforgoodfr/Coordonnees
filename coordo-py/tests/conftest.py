# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

import pytest 
from pathlib import Path

DATA_DIR = Path("tests/test_data")
INVENTORY_DIR = DATA_DIR / "inventory"

@pytest.fixture
def inventory_package():
    return "catalog/inventory"

@pytest.fixture
def inventory_inquiry():
    return INVENTORY_DIR / "inquiry.xlsx"

@pytest.fixture
def inventory_data():
    return INVENTORY_DIR / "data.xlsx"

@pytest.fixture
def inventory_file():
    return INVENTORY_DIR / "file.csv"
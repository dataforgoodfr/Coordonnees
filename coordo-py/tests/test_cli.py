# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

import shutil
from typer.testing import CliRunner
from coordo.cli.main import app 
import logging


logger = logging.getLogger(__name__)


runner = CliRunner()

def run(command: list):
    result = runner.invoke(app, command)
    assert result.exit_code == 0

def test_add_data_to_package(inventory_package, inventory_inquiry, inventory_data, inventory_file):
    """
    Test the following workflow:
    - Load data from a kobotoolbox inquiry 
    - Remove the foreign key pointing to it
    - Remove it
    - Add it again
    - Load a file into the package
    - Remove it
    - Add it again
    - Add a foreign key between two fields.
    - Remove the foreign key.
    - Add the foreign key again.
    """
    try:
        run(["add", "kobotoolbox", inventory_inquiry, inventory_data, "--package", inventory_package])
        run(["remove", "foreignkey", "reg.parent_id", "inventaire_id._id", "--package", inventory_package])
        run(["remove", "foreignkey", "ind.parent_id", "inventaire_id._id", "--package", inventory_package])
        run(["remove", "foreignkey", 'tsbf_001.parent_id', "inventaire_id._id", "--package", inventory_package])
        run(["remove", "foreignkey", 'barba_001.parent_id', "inventaire_id._id", "--package", inventory_package])
        run(["remove", "foreignkey", 'barbb_001.parent_id', "inventaire_id._id", "--package", inventory_package])
        run(["remove", "foreignkey", 'barbc_001.parent_id', "inventaire_id._id", "--package", inventory_package])
        run(["remove", "foreignkey", 'barbd_001.parent_id', "inventaire_id._id", "--package", inventory_package])
        run(["remove", "kobotoolbox", inventory_inquiry, inventory_data, "--package", inventory_package])
        run(["add", "kobotoolbox", inventory_inquiry, inventory_data, "--package", inventory_package])
        run(["add", "file", inventory_file, "--package", inventory_package])
        run(["remove", "file", inventory_file, "--package", inventory_package])
        run(["add", "file", inventory_file, "--package", inventory_package])
        run(["add", "foreignkey", "ind.ess_arb", "file.ess_arb", "--package", inventory_package])
        run(["remove", "foreignkey", "ind.ess_arb", "file.ess_arb", "--package", inventory_package])
    finally:
        logger.info(f"Removing package '{inventory_package}'")
        shutil.rmtree(inventory_package)
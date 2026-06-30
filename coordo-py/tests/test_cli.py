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

def run_all_and_delete_catalog(commands: list[list], inventory_package: str):
    try:
        for command in commands:
            command += ["--package", inventory_package]
            run(command)
    finally:
        logger.info(f"Removing package '{inventory_package}'")
        shutil.rmtree(inventory_package)


def test_add_remove_kobotoolbox(inventory_package, inventory_inquiry, inventory_data, inventory_file):
    """
    Test the following workflow:
    - Load data from a kobotoolbox inquiry 
    - Remove the foreign key pointing to it
    - Remove it
    - Add it again
    """
    run_all_and_delete_catalog([
        ["add", "kobotoolbox", inventory_inquiry, inventory_data],
        ["remove", "foreignkey", "reg.parent_id", "inventaire_id._id"],
        ["remove", "foreignkey", "ind.parent_id", "inventaire_id._id"],
        ["remove", "foreignkey", 'tsbf_001.parent_id', "inventaire_id._id"],
        ["remove", "foreignkey", 'barba_001.parent_id', "inventaire_id._id"],
        ["remove", "foreignkey", 'barbb_001.parent_id', "inventaire_id._id"],
        ["remove", "foreignkey", 'barbc_001.parent_id', "inventaire_id._id"],
        ["remove", "foreignkey", 'barbd_001.parent_id', "inventaire_id._id"],
        ["remove", "kobotoolbox", inventory_inquiry, inventory_data],
        ["add", "kobotoolbox", inventory_inquiry, inventory_data]
    ], inventory_package)


def test_add_remove_file(inventory_package, inventory_inquiry, inventory_data, inventory_file):
    """
    Test the following workflow:
    - Load data from a kobotoolbox inquiry 
    - Load a file
    - Remove it
    - Add it again
    - Add a foreign key between two fields.
    - Remove the foreign key.
    - Add the foreign key again.
    """
    run_all_and_delete_catalog([
        ["add", "kobotoolbox", inventory_inquiry, inventory_data],
        ["add", "file", inventory_file],
        ["remove", "file", inventory_file],
        ["add", "file", inventory_file]
    ], inventory_package)


def test_add_kobotoolbox_file_foreignkey(inventory_package, inventory_inquiry, inventory_data, inventory_file):
    """
    Test the following workflow:
    - Load data from a kobotoolbox inquiry 
    - Load a file
    - Add a foreign key between two fields.
    - Remove the foreign key.
    - Add the foreign key again.
    """
    run_all_and_delete_catalog([
        ["add", "kobotoolbox", inventory_inquiry, inventory_data],
        ["add", "file", inventory_file],
        ["add", "foreignkey", "ind.ess_arb", "file.ess_arb"],
        ["remove", "foreignkey", "ind.ess_arb", "file.ess_arb"],
        ["add", "foreignkey", "ind.ess_arb", "file.ess_arb"]
    ], inventory_package)


def test_append_file_data(inventory_package, inventory_inquiry, inventory_data, inventory_file):
    """
    Test the following workflow:
    - Load a file
    - Append data from second file
    """
    run_all_and_delete_catalog([
        ["add", "file", inventory_file],
        ["append", "file", inventory_file]
    ], inventory_package)
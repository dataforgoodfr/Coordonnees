# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

import shutil
import subprocess

from typer.testing import CliRunner
from coordo.cli.main import app 
import logging


logger = logging.getLogger(__name__)


runner = CliRunner()

def run(command: list):
    result = runner.invoke(app, command)
    assert result.exit_code == 0, f"Command '{' '.join(command)}' failed: {result.stdout}"


def check_files_are_identical(file1: str, file2: str):
    result = subprocess.run(["diff", file1, file2], capture_output=True, text=True)
    assert result.returncode == 0, f"Files {file1} and {file2} are not identical: {result.stdout}"


def run_all(commands: list[list[str]], expected_datapackage: str):
    catalog_dir = "catalog/test_cli"
    try:
        for command in commands:
            command += ["--package", catalog_dir]
            run(command)
        # check that the datapackage was created as expected
        check_files_are_identical(f"{catalog_dir}/datapackage.json", expected_datapackage)
    finally:
        logger.info(f"Removing package '{catalog_dir}'")
        shutil.rmtree(catalog_dir)


def test_001_add_remove_kobotoolbox(input_files: dict[str, str], output_files: dict[str, str]):
    """
    Test the following workflow:
    - Load data from a kobotoolbox inquiry 
    - Remove the foreign key pointing to it
    - Remove it
    - Add it again
    """
    run_all([
        ["add", "kobotoolbox", input_files["kobotoolbox_inquiry.xlsx"], input_files["kobotoolbox_data.xlsx"]],
        ["remove", "foreignkey", "reg.parent_id", "inventaire_id._id"],
        ["remove", "foreignkey", "ind.parent_id", "inventaire_id._id"],
        ["remove", "foreignkey", 'tsbf_001.parent_id', "inventaire_id._id"],
        ["remove", "foreignkey", 'barba_001.parent_id', "inventaire_id._id"],
        ["remove", "foreignkey", 'barbb_001.parent_id', "inventaire_id._id"],
        ["remove", "foreignkey", 'barbc_001.parent_id', "inventaire_id._id"],
        ["remove", "foreignkey", 'barbd_001.parent_id', "inventaire_id._id"],
        ["remove", "kobotoolbox", input_files["kobotoolbox_inquiry.xlsx"], input_files["kobotoolbox_data.xlsx"]],
        ["add", "kobotoolbox", input_files["kobotoolbox_inquiry.xlsx"], input_files["kobotoolbox_data.xlsx"]]
    ], expected_datapackage=output_files["001.datapackage.json"])


def test_002_add_remove_file(input_files: dict[str, str], output_files: dict[str, str]):
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
    run_all([
        ["add", "kobotoolbox", input_files["kobotoolbox_inquiry.xlsx"], input_files["kobotoolbox_data.xlsx"]],
        ["add", "file", input_files["external_data.csv"]],
        ["remove", "file", input_files["external_data.csv"]],
        ["add", "file", input_files["external_data.csv"]]
    ], expected_datapackage=output_files["002.datapackage.json"])


def test_003_add_kobotoolbox_file_foreignkey(input_files: dict[str, str], output_files: dict[str, str]):
    """
    Test the following workflow:
    - Load data from a kobotoolbox inquiry 
    - Load a file
    - Add a foreign key between two fields.
    - Remove the foreign key.
    - Add the foreign key again.
    """
    run_all([
        ["add", "kobotoolbox", input_files["kobotoolbox_inquiry.xlsx"], input_files["kobotoolbox_data.xlsx"]],
        ["add", "file", input_files["external_data.csv"]],
        ["add", "foreignkey", "ind.ess_arb", "external_data.ess_arb"],
        ["remove", "foreignkey", "ind.ess_arb", "external_data.ess_arb"],
        ["add", "foreignkey", "ind.ess_arb", "external_data.ess_arb"]
    ], expected_datapackage=output_files["003.datapackage.json"])


def test_004_append_replace_delete_file_data(input_files: dict[str, str], output_files: dict[str, str]):
    """
    Test the following workflow:
    - Load a file
    - Append data from second file
    """
    run_all([
        ["add", "file", input_files["external_data.csv"]],
        ["append", "file", input_files["external_data.csv"]],
        ["replace", "file", input_files["external_data.csv"]],
        ["delete", "file", input_files["external_data.csv"]]
    ], expected_datapackage=output_files["004.datapackage.json"])
# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

import shutil
import subprocess

import pandas as pd
from typer.testing import CliRunner
from coordo.cli.main import app
import logging


logger = logging.getLogger(__name__)


runner = CliRunner()

CATALOG_DIR = "catalog/test_cli"


def run(command: list):
    result = runner.invoke(app, command)
    assert result.exit_code == 0, (
        f"Command '{' '.join(command)}' failed: {result.stdout}"
    )


def check_files_are_identical(file1: str, file2: str):
    result = subprocess.run(["diff", file1, file2], capture_output=True, text=True)
    assert result.returncode == 0, (
        f"Files {file1} and {file2} are not identical: {result.stdout}"
    )


def run_all(commands: list[list[str]]):
    for command in commands:
        command += ["--package", CATALOG_DIR]
        run(command)


def test_001_add_remove_kobotoolbox(
    input_files: dict[str, str], output_files: dict[str, str]
):
    """
    Test the following workflow:
    - Load data from a kobotoolbox inquiry
    - Remove the foreign key pointing to it
    - Remove it
    - Add it again
    """
    try:
        run_all(
            [
                [
                    "add",
                    "kobotoolbox",
                    input_files["kobotoolbox_data.xlsx"],
                    "--form",
                    input_files["kobotoolbox_inquiry.xlsx"],
                ],
                ["remove", "foreignkey", "reg.parent_id", "inventaire_id._id"],
                ["remove", "foreignkey", "ind.parent_id", "inventaire_id._id"],
                ["remove", "foreignkey", "tsbf_001.parent_id", "inventaire_id._id"],
                ["remove", "foreignkey", "barba_001.parent_id", "inventaire_id._id"],
                ["remove", "foreignkey", "barbb_001.parent_id", "inventaire_id._id"],
                ["remove", "foreignkey", "barbc_001.parent_id", "inventaire_id._id"],
                ["remove", "foreignkey", "barbd_001.parent_id", "inventaire_id._id"],
                [
                    "remove",
                    "kobotoolbox",
                    input_files["kobotoolbox_data.xlsx"],
                    "--form",
                    input_files["kobotoolbox_inquiry.xlsx"],
                ],
                [
                    "add",
                    "kobotoolbox",
                    input_files["kobotoolbox_data.xlsx"],
                    "--form",
                    input_files["kobotoolbox_inquiry.xlsx"],
                ],
            ]
        )
        # check that the datapackage was created as expected
        check_files_are_identical(
            f"{CATALOG_DIR}/datapackage.json", output_files["001.datapackage.json"]
        )
    finally:
        logger.info(f"Removing package '{CATALOG_DIR}'")
        shutil.rmtree(CATALOG_DIR)


def test_002_add_remove_file(input_files: dict[str, str], output_files: dict[str, str]):
    """
    Test the following workflow:
    - Load data from a kobotoolbox inquiry
    - Load a file
    - Remove it
    - Add it again
    """
    try:
        run_all(
            [
                [
                    "add",
                    "kobotoolbox",
                    input_files["kobotoolbox_data.xlsx"],
                    "--form",
                    input_files["kobotoolbox_inquiry.xlsx"],
                ],
                ["add", "file", input_files["external_data.csv"]],
                ["remove", "file", input_files["external_data.csv"]],
                ["add", "file", input_files["external_data.csv"]],
                ["remove", "resource", "external_data"],
                ["add", "file", input_files["external_data.csv"]],
            ]
        )
        # check that the datapackage was created as expected
        check_files_are_identical(
            f"{CATALOG_DIR}/datapackage.json", output_files["002.datapackage.json"]
        )
    finally:
        logger.info(f"Removing package '{CATALOG_DIR}'")
        shutil.rmtree(CATALOG_DIR)


def test_003_add_kobotoolbox_file_foreignkey(
    input_files: dict[str, str], output_files: dict[str, str]
):
    """
    Test the following workflow:
    - Load data from a kobotoolbox inquiry
    - Load a file
    - Add a foreign key between two fields.
    - Remove the foreign key.
    - Add the foreign key again.
    """
    try:
        run_all(
            [
                [
                    "add",
                    "kobotoolbox",
                    input_files["kobotoolbox_data.xlsx"],
                    "--form",
                    input_files["kobotoolbox_inquiry.xlsx"],
                ],
                ["add", "file", input_files["external_data.csv"]],
                ["add", "foreignkey", "ind.ess_arb", "external_data.ess_arb"],
                ["remove", "foreignkey", "ind.ess_arb", "external_data.ess_arb"],
                ["add", "foreignkey", "ind.ess_arb", "external_data.ess_arb"],
            ]
        )
        # check that the datapackage was created as expected
        check_files_are_identical(
            f"{CATALOG_DIR}/datapackage.json", output_files["003.datapackage.json"]
        )
    finally:
        logger.info(f"Removing package '{CATALOG_DIR}'")
        shutil.rmtree(CATALOG_DIR)


def test_004_append_replace_delete_file_data(
    input_files: dict[str, str], output_files: dict[str, str]
):
    """
    Test the following workflow:
    - Load a file
    - Append data from the same file
    - Replace data from the same file
    - Delete data
    - Append data from second file
    - Replace data with data in second file
    - Delete resource
    """
    try:
        run_all(
            [
                ["add", "file", input_files["external_data.csv"]],
                ["append", "file", input_files["external_data.csv"]],
                ["replace", "file", input_files["external_data.csv"]],
                [
                    "append",
                    "file",
                    input_files["external_data2.csv"],
                    "--resource",
                    "external_data",
                ],
                [
                    "replace",
                    "file",
                    input_files["external_data2.csv"],
                    "--resource",
                    "external_data",
                ],
                ["delete", "resource", "external_data"],
            ]
        )
        # check that the datapackage was created as expected
        check_files_are_identical(
            f"{CATALOG_DIR}/datapackage.json", output_files["004.datapackage.json"]
        )
    finally:
        logger.info(f"Removing package '{CATALOG_DIR}'")
        shutil.rmtree(CATALOG_DIR)


def test_005_add_remove_delete_excel_file(
    input_files: dict[str, str], output_files: dict[str, str]
):
    """
    Test the following workflow:
    - Add file
    - Remove resouces linked to Excel file
    - Add file again
    - Delete data from file
    - Append data from the same file
    - Replace data with data from the ame file
    - Delete data
    """
    try:
        run_all(
            [
                ["add", "file", input_files["external_data.xlsx"]],
                ["remove", "file", input_files["external_data.xlsx"]],
                ["add", "file", input_files["external_data.xlsx"]],
                ["replace", "file", input_files["external_data.xlsx"]],
                ["append", "file", input_files["external_data.xlsx"]],
                ["delete", "resource", "bio_samp"],
            ]
        )
        # check that the datapackage was created as expected
        check_files_are_identical(
            f"{CATALOG_DIR}/datapackage.json", output_files["005.datapackage.json"]
        )
        # check that output parquet file has the expected number of rows
        file = f"{CATALOG_DIR}/bio_pop.parquet"
        logger.info(f"Checking number of rows in {file}")
        df = pd.read_parquet(file)
        assert len(df) == 4
    finally:
        logger.info(f"Removing package '{CATALOG_DIR}'")
        shutil.rmtree(CATALOG_DIR)


def test_006_append_multisheet_excel_file_to_unique_resource(
    input_files: dict[str, str], output_files: dict[str, str]
):
    """
    Test the following workflow:
    - Load a file
    - Append data from the same file, and force the target resource
    - Should raise an error because forcing the target resource
      when the input file is an Excel file is not permitted
    """
    try:
        run_all(
            [
                ["add", "file", input_files["external_data.xlsx"]],
                ["append", "file", input_files["external_data.xlsx"], "-r", "bio_samp"],
            ]
        )
    except AssertionError:
        logger.info("Expected AssertionError was raised")
    else:
        raise RuntimeError("Expected AssertionError but no exception was raised")
    finally:
        logger.info(f"Removing package '{CATALOG_DIR}'")
        shutil.rmtree(CATALOG_DIR)


def test_007_add_append_kobotoolbox(
    input_files: dict[str, str], output_files: dict[str, str]
):
    """
    Test the following workflow:
    - Load data from a kobotoolbox inquiry
    - Replace data from the same kobootoolbox data
    - Append data from the same kobootoolbox data
    - Delete data
    """
    try:
        run_all(
            [
                [
                    "add",
                    "kobotoolbox",
                    input_files["kobotoolbox_data.xlsx"],
                    "--form",
                    input_files["kobotoolbox_inquiry.xlsx"],
                ],
                [
                    "replace",
                    "kobotoolbox",
                    input_files["kobotoolbox_data.xlsx"],
                ],
                [
                    "append",
                    "kobotoolbox",
                    input_files["kobotoolbox_data.xlsx"],
                ],
            ]
        )
        # check that the datapackage was created as expected
        check_files_are_identical(
            f"{CATALOG_DIR}/datapackage.json", output_files["007.datapackage.json"]
        )
        # check that output parquet file has the expected number of rows
        file = f"{CATALOG_DIR}/barba_001.parquet"
        logger.info(f"Checking number of rows in {file}")
        df = pd.read_parquet(file)
        assert len(df) == 138
    finally:
        logger.info(f"Removing package '{CATALOG_DIR}'")
        shutil.rmtree(CATALOG_DIR)

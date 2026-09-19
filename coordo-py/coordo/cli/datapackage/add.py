# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

import typer

from coordo.loaders import (
    KoboToolboxLoader,
    Loader,
    get_file_loader,
)

from .annotations import DecimalSep, FilePath, Package, Sep, XlsData, XlsForm

app = typer.Typer()


@app.command()
def kobotoolbox(xlsform: XlsForm, xlsdata: XlsData, package: Package):
    KoboToolboxLoader(package, xlsdata, xlsform).add()


@app.command()
def file(
    path: FilePath,
    package: Package,
    sep: Sep = None,
    decimal_sep: DecimalSep = None,
):
    """
    Add a file to a datapackage.
    """
    get_file_loader(package, path, sep=sep, decimal_sep=decimal_sep).add()


@app.command()
def foreignkey(
    package: Package, resource: str, foreign_resource: str, pairs: list[str]
):
    """
    Add a foreign key constraint between two resources.
    """
    Loader.add_foreign_key(package, resource, foreign_resource, pairs)

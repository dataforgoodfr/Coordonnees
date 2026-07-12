# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

import typer

from coordo.loaders import (
    Loader,
    KoboToolboxLoader,
    get_file_loader,
)
from .annotations import Package, From, To, XlsForm, XlsData, FilePath, Sep, DecimalSep


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
def foreignkey(from_: From, to: To, package: Package):
    """
    Add a foreign key constraint between two resources.
    """
    Loader.add_foreign_key(package, from_, to)

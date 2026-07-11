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
    KoboToolboxLoader(package, xlsdata, xlsform).remove()


@app.command()
def file(
    path: FilePath,
    package: Package,
    sep: Sep = None,
    decimal_sep: DecimalSep = None,
):
    get_file_loader(package, path, sep=sep, decimal_sep=decimal_sep).remove()


@app.command()
def resource(resource_name: str, package: Package):
    """
    Remove a resource from the package by its name.
    """
    Loader.remove_one_resource(package, resource_name)


@app.command()
def foreignkey(from_: From, to: To, package: Package):
    """
    Remove a foreign key constraint from a resource.
    """
    Loader.remove_foreign_key(package, from_, to)

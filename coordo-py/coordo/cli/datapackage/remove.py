# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

import typer
from coordo.loaders import (
    KoboToolboxLoader,
    Loader,
    get_file_loader,
)

from .annotations import DecimalSep, FilePath, From, Package, Sep, To, XlsData, XlsForm

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
def foreignkey(package: Package, resource: str, foreign_resource: str):
    """
    Remove a foreign key constraint from a resource.
    """
    Loader.remove_foreign_key(package, resource, foreign_resource)

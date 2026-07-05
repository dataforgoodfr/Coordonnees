# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

import typer

from coordo.loaders import (
    Loader,
    KoboToolboxLoader,
    get_file_loader,
)
from coordo.datapackage import DataPackage
from .annotations import Package, From, To, XlsForm, XlsData, FilePath, Sep, DecimalSep


app = typer.Typer()


@app.command()
def kobotoolbox(xlsform: XlsForm, xlsdata: XlsData, package: Package):
    KoboToolboxLoader(package, xlsform, xlsdata).remove()


@app.command()
def file(
    path: FilePath,
    package: Package,
    sep: Sep = None,
    decimal_sep: DecimalSep = None,
):
    get_file_loader(package, path, sep=sep, decimal_sep=decimal_sep).remove()


@app.command()
def resource(
    resource_name: str,
    package: Package,
):
    """
    Remove a resource from the package by its name.
    """
    Loader.remove_one_resource(package, resource_name)


@app.command()
def foreignkey(from_: From, to: To, package: Package):
    """
    Remove a foreign key constraint from a resource.
    """
    dp = DataPackage.from_path(package)
    resource, field = from_.split(".")
    foreign_resource, foreign_field = to.split(".")
    dp.get_resource(
        resource,
    ).remove_foreignkey(
        fields=[field],
        foreign_fields=[foreign_field],
        foreign_resource=foreign_resource,
    )
    dp.save()

# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

import typer

from coordo.loaders import (
    KoboToolboxLoader,
    get_file_loader,
)
from coordo.datapackage import DataPackage
from .annotations import Package, From, To, XlsForm, XlsData, FilePath, Sep, DecimalSep


app = typer.Typer()


@app.command()
def kobotoolbox(xlsform: XlsForm, xlsdata: XlsData, package: Package):
    KoboToolboxLoader(package, xlsform, xlsdata).add()


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
    dp = DataPackage.from_path(package)
    resource, field = from_.split(".")
    foreign_resource, foreign_field = to.split(".")
    dp.get_resource(
        resource,
    ).add_foreignkey(
        fields=[field],
        foreign_fields=[foreign_field],
        foreign_resource=foreign_resource,
    )
    dp.save()

# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

import typer

from coordo.loaders import Loader, KoboToolboxLoader, Separator, get_file_loader, get_supplementary_params
from coordo.datapackage import DataPackage
from .annotations import Package, ResourceName, From, To, XlsForm, XlsData, FilePath, Sep, DecimalSep


app = typer.Typer()


@app.command()
def kobotoolbox(xlsform: XlsForm, xlsdata: XlsData, package: Package):
    KoboToolboxLoader(package, xlsform, xlsdata).remove()


@app.command()
def file(
    path: FilePath, 
    package: Package, 
    sep: Sep = Separator.COMMA, 
    decimal_sep: DecimalSep = Separator.DOT
):
    params = get_supplementary_params()
    file_loader_cls = get_file_loader(path, params)
    file_loader_cls(package, path, **params).remove()


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
    
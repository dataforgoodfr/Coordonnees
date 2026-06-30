# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

import typer

from coordo.loaders import KoboToolboxLoader, Separator, get_file_loader, get_supplementary_params
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
    sep: Sep = Separator.COMMA, 
    decimal_sep: DecimalSep = Separator.DOT
):
    params = get_supplementary_params()
    file_loader_cls = get_file_loader(path, params)
    file_loader_cls(package, path, **params).add()


@app.command()
def foreignkey(from_: From, to: To, package: Package):
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

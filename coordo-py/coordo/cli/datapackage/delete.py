# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

import typer

from coordo.loaders import Loader, Separator, UpdateMethod, get_file_loader, get_supplementary_params
from .annotations import Package, FilePath, Sep, DecimalSep


app = typer.Typer()


@app.command()
def file(
    path: FilePath, 
    package: Package, 
    sep: Sep = Separator.COMMA, 
    decimal_sep: DecimalSep = Separator.DOT
):
    """
    Delete data from a datapackage resource. By default, the resource name is inferred from the file name.
    """
    params = get_supplementary_params()
    file_loader_cls = get_file_loader(path, params)
    file_loader_cls(package, path, **params).update(method=UpdateMethod.DELETE)


@app.command()
def resource(
    resource_name: str, 
    package: Package, 
):
    """
    Delete data from a resource.
    """
    Loader.delete_one_resource(package, resource_name)

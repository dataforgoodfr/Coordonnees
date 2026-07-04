# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

import typer

from coordo.loaders import KoboToolboxLoader, Loader, get_file_loader
from .annotations import Package, FilePath, XlsForm, XlsData


app = typer.Typer()


@app.command()
def kobotoolbox(xlsform: XlsForm, xlsdata: XlsData, package: Package):
    KoboToolboxLoader(package, xlsform, xlsdata).delete()


@app.command()
def file(
    path: FilePath, 
    package: Package
):
    """
    Delete data from the resource(s) contained in the file.
    """
    file_loader_cls = get_file_loader(path, {})
    file_loader_cls(package, path).delete()


@app.command()
def resource(
    resource_name: str, 
    package: Package, 
):
    """
    Delete data from a resource.
    """
    Loader.delete_one_resource(package, resource_name)

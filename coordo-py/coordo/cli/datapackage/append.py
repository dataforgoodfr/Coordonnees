# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

import typer

from coordo.loaders import KoboToolboxLoader, get_file_loader
from .annotations import (
    Package,
    ResourceName,
    FilePath,
    Sep,
    DecimalSep,
    XlsData,
)


app = typer.Typer()


@app.command()
def kobotoolbox(xlsdata: XlsData, package: Package):
    """
    Append data to the datapackage Kobotoolbox resources.
    """
    KoboToolboxLoader(package, xlsdata).append()


@app.command()
def file(
    path: FilePath,
    package: Package,
    resource_name: ResourceName = None,
    sep: Sep = None,
    decimal_sep: DecimalSep = None,
):
    """
    Append data from a file to a datapackage resource. By default, the resource name is inferred from the file name.
    """
    get_file_loader(package, path, sep=sep, decimal_sep=decimal_sep).append(
        resource_name
    )

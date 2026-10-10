# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

import typer

from coordo.loaders import KoboToolboxLoader, get_file_loader

from .annotations import (
    DecimalSep,
    FilePath,
    Package,
    ResourceName,
    Sep,
    XlsData,
)
from .results import ensure_success

app = typer.Typer()


@app.command()
def kobotoolbox(xlsdata: XlsData, package: Package):
    """
    Append data to the datapackage Kobotoolbox resources.
    """
    ensure_success(KoboToolboxLoader(package, xlsdata).append())


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
    ensure_success(
        get_file_loader(package, path, sep=sep, decimal_sep=decimal_sep).append(
            resource_name
        )
    )

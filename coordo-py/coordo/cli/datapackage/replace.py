# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

import typer

from coordo.loaders import (
    KoboToolboxLoader,
    get_file_loader,
)
from .annotations import (
    Package,
    ResourceName,
    FilePath,
    Sep,
    DecimalSep,
    XlsForm,
    XlsData,
)


app = typer.Typer()


@app.command()
def kobotoolbox(
    xlsform: XlsForm,
    xlsdata: XlsData,
    package: Package,
):
    """
    Replace data of datapackage resources by data parsed from Kobotoolbox XLS form and XLS data files.
    """
    KoboToolboxLoader(package, xlsform, xlsdata).replace()


@app.command()
def file(
    path: FilePath,
    package: Package,
    resource_name: ResourceName = None,
    sep: Sep = None,
    decimal_sep: DecimalSep = None,
):
    """
    Replace data in a datapackage resource from a file. By default, the resource name is inferred from the file name.
    """
    get_file_loader(package, path, sep=sep, decimal_sep=decimal_sep).replace(
        resource_name
    )

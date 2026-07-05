# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

import typer

from coordo.loaders import Loader
from .annotations import Package


app = typer.Typer()


@app.command()
def resource(
    resource_name: str,
    package: Package,
):
    """
    Delete data from a specific resource.
    """
    Loader.delete_data_from_resource(package, resource_name)

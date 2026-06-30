# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

import typer

from coordo.loaders import Separator, UpdateMethod, get_file_loader, get_supplementary_params
from .annotations import Package, ResourceName, FilePath, Sep, DecimalSep


app = typer.Typer()


@app.command()
def file(
    path: FilePath, 
    package: Package, 
    resource: ResourceName = None,
    sep: Sep = Separator.COMMA, 
    decimal_sep: DecimalSep = Separator.DOT
):
    params = get_supplementary_params()
    file_loader_cls = get_file_loader(path, params)
    file_loader_cls(package, path, **params).update(resource_name=resource, method=UpdateMethod.REPLACE)

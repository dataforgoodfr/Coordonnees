# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path
from typing import Annotated

import typer

# general arguments
Package = Annotated[
    Path, typer.Option("--package", "-p", help="Path to the package directory")
]
ResourceName = Annotated[
    str | None,
    typer.Option(
        "--resource",
        "-r",
        help="Name of the resource (if not provided, the file name will be used)",
    ),
]
From = Annotated[str, typer.Argument(help="Foreign key source")]
To = Annotated[str, typer.Argument(help="Foreign key target")]

# kobotoolbox arguments
XlsForm = Annotated[Path, typer.Option("--form", "-f", help="Path to the XLS form")]
OptionalXlsForm = Annotated[
    Path | None, typer.Option("--form", "-f", help="Path to the XLS form")
]
XlsData = Annotated[Path, typer.Argument(help="Path to the XLS data")]

# file arguments
FilePath = Annotated[Path, typer.Argument(help="Path to the file")]
Sep = Annotated[
    str | None, typer.Option("--separator", "-s", help="Separator for the file")
]
DecimalSep = Annotated[
    str | None,
    typer.Option("--decimal-separator", "-d", help="Decimal separator for the file"),
]

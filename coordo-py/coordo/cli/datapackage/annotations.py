# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path
from typing import Annotated

import typer

from coordo.loaders import Separator

# general arguments
Package = Annotated[Path, typer.Option(help="Path to the package directory")]
From = Annotated[str, "Foreign key source"]
To = Annotated[str, "Foreign key target"]

# kobotoolbox arguments
XlsForm = Annotated[Path, typer.Argument(help="Path to the XLS form")]
XlsData = Annotated[Path, typer.Argument(help="Path to the XLS data")]

# file arguments
FilePath = Annotated[Path, typer.Argument(help="Path to the file")]
Sep = Annotated[Separator, typer.Option(help="Separator for the file")]
DecimalSep = Annotated[Separator, typer.Option(help="Decimal separator for the file")]
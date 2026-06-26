# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path
from typing import Type

from .loader import Separator, Loader
from .file_loader import FileLoader
from .kobotoolbox_loader import KoboToolboxLoader
from .csv_file_loader import CSVFileLoader
from .excel_file_loader import ExcelFileLoader


__all__ = ["Separator", "Loader", "FileLoader", "KoboToolboxLoader", "CSVFileLoader", "ExcelFileLoader"]

def get_file_loader(params: dict) -> Type[FileLoader]:
    """
    Returns the appropriate file loader class based on the file extension.
    Check that the file exists and that the extension is supported.
    Also checks that the parameters provided are valid for the loader.
    """
    path = params["path"]
    supplementary_kwargs = {k: v for k, v in params.items() if k not in ["package", "path"]}
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if path.suffix in ExcelFileLoader.EXTENSIONS:
        check_params_are_attributes(ExcelFileLoader, supplementary_kwargs)
        return ExcelFileLoader
    elif path.suffix in CSVFileLoader.EXTENSIONS:
        check_params_are_attributes(CSVFileLoader, supplementary_kwargs)
        return CSVFileLoader
    else:
        raise ValueError(f"Unsupported file extension: {path.suffix}")


def check_params_are_attributes(cls: Type[Loader], kwargs: dict):
    static_attributes = get_static_attributes(cls)
    for attr in kwargs:
        assert attr in static_attributes, f"Unrecognized argument {attr} for class {cls.__name__}"


def get_static_attributes(cls: Type[Loader]) -> list:
    return list(vars(cls)["__static_attributes__"])
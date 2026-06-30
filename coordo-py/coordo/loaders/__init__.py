# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path
from typing import Type

from .loader import Separator, Loader, UpdateMethod
from .file import FileLoader
from .kobotoolbox import KoboToolboxLoader
from .csv_file import CSVFileLoader
from .excel_file import ExcelFileLoader


__all__ = [
    "Separator", 
    "Loader", 
    "UpdateMethod", 
    "FileLoader", 
    "KoboToolboxLoader", 
    "CSVFileLoader", 
    "ExcelFileLoader"
]

def get_file_loader(path: Path, supplementary_params: dict) -> Type[FileLoader]:
    """
    Returns the appropriate file loader class based on the file extension.
    Check that the file exists and that the extension is supported.
    Also checks that the parameters provided are valid for the loader.
    """
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if path.suffix in ExcelFileLoader.EXTENSIONS:
        check_params_are_attributes(ExcelFileLoader, supplementary_params)
        return ExcelFileLoader
    elif path.suffix in CSVFileLoader.EXTENSIONS:
        check_params_are_attributes(CSVFileLoader, supplementary_params)
        return CSVFileLoader
    else:
        check_params_are_attributes(FileLoader, supplementary_params)
        return FileLoader


def get_supplementary_params() -> dict:
    return {k: v for k, v in locals().items() if k not in ["package", "path", "resource_name"]}


def check_params_are_attributes(cls: Type[Loader], kwargs: dict):
    static_attributes = get_static_attributes(cls)
    for attr in kwargs:
        assert attr in static_attributes, f"Unrecognized argument {attr} for class {cls.__name__}"


def get_static_attributes(cls: Type[Loader]) -> list:
    """
    Returns the static instance attributes (defined in __init__) of the loader class.
    There is no direct way to get the static attributes of a class in Python,
    so we use the `__static_attributes__`, which should work.
    """
    return list(vars(cls)["__static_attributes__"])
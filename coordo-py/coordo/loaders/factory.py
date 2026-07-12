# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path
from typing import Type
import inspect
import logging

from .loader import Loader
from .file_loader import FileLoader
from .csv_file_loader import CSVFileLoader
from .excel_file_loader import ExcelFileLoader

logger = logging.getLogger(__name__)


def get_file_loader(package: Path, path: Path, **params) -> FileLoader:
    # get class to instantiate, according to the extension of the provided path
    file_loader_cls = get_file_loader_class(path)
    # filter params
    filtered_params = filter_params(file_loader_cls, params)
    # instantiate class with provided arguments and return instance
    return file_loader_cls(package, path, **filtered_params)


def get_file_loader_class(path: Path) -> Type[FileLoader]:
    """
    Returns the appropriate file loader class based on the file extension.
    """
    if path.suffix in ExcelFileLoader.EXTENSIONS:
        return ExcelFileLoader
    elif path.suffix in CSVFileLoader.EXTENSIONS:
        return CSVFileLoader
    else:
        return FileLoader


def filter_params(cls: Type[Loader], params: dict):
    sig = inspect.signature(cls.__init__)
    valid_params = set(sig.parameters) - {"self"}
    filtrered_params = {}
    for k, v in params.items():
        if v is None:
            continue
        if k not in valid_params:
            logger.warning(
                f"Unrecognized argument {k} for class {cls.__name__}. This argument is ignored."
            )
            continue
        filtrered_params[k] = params[k]
    return filtrered_params

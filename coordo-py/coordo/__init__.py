import warnings
from enum import Enum
from typing import Annotated
import typer

# ignore warnings due to shadowing of Pydantic's "schema" field in "Resource"
REGEX_TO_IGNORE = (
    'Field name "schema" in "Resource" shadows an attribute in parent "(Base)?Model"'
)
warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    module="dplib",
    message=REGEX_TO_IGNORE,
)

warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    module="coordo",
    message=REGEX_TO_IGNORE,
)


class LoadingStrategy(str, Enum):
    raise_error = "raise_error"
    overwrite = "overwrite"
    merge = "merge"
    
StrategyType = Annotated[
    LoadingStrategy, 
    typer.Option(help="Strategy to use in case of already existing resource")
]
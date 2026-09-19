# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0
# ruff: noqa: UP007,TC010

# Not all definitions have been imported from common/maplibre-style-spec-v8.ts
# Please add them when needed

from typing import (
    Any,
    Generic,
    Literal,
    NotRequired,
    TypedDict,
    TypeVar,
    Union,
)

from geojson import GeoJSON

T = TypeVar("T")

ColorSpecification = str
PaddingSpecification = Union[float, list[float]]
NumberArraySpecification = Union[float, list[float]]
ColorArraySpecification = Union[str, list[str]]
VariableAnchorOffsetCollectionSpecification = list[str | tuple[float, float]]
SpriteSpecification = Union[str, list[dict[str, str]]]
FormattedSpecification = str
ResolvedImageSpecification = str
PromoteIdSpecification = Union[dict[str, str], str]
ExpressionInputType = Union[str, float, bool]
CollatorExpression = TypedDict(
    "CollatorExpression",
    {
        "case-sensitive": NotRequired[Union[bool, "ExpressionSpecification"]],
        "diacritic-sensitive": Union[bool, "ExpressionSpecification"],
        "locale": NotRequired[Union[str, "ExpressionSpecification"]],
    },
)
CollatorExpressionSpecification = tuple[Literal["collator"], CollatorExpression]

InterpolationSpecification = (
    tuple[Literal["linear"]]
    | tuple[Literal["exponential"], float]
    | tuple[Literal["cubic-bezier"], float, float, float, float]
)
ProjectionDefinition = tuple[str, str, float]
ProjectionDefinitionSpecification = Union[
    str,
    ProjectionDefinition,
    "PropertyValueSpecification[ProjectionDefinition]",
]

ExpressionSpecification = (
    tuple[Literal["array"], "ExpressionSpecification"]
    | tuple[
        Literal["array"],
        Literal["string", "number", "boolean"],
        "ExpressionSpecification",
    ]
    | tuple[
        Literal["array"],
        Literal["string", "number", "boolean"],
        float,
        "ExpressionSpecification",
    ]
    | tuple[
        Literal["boolean"],
        Union[Any, "ExpressionSpecification"],
        *tuple[Union[Any, "ExpressionSpecification"], ...],
    ]
    | CollatorExpressionSpecification
    | tuple[
        Literal["format"],
        *tuple[
            str
            | tuple[Literal["image"], "ExpressionSpecification"]
            | "ExpressionSpecification"
            | dict[
                str,
                Union[float, "ExpressionSpecification", ColorSpecification, Literal["bottom", "center", "top"]],
            ],
            ...,
        ],
    ]
    | tuple[Literal["image"], Union[str, "ExpressionSpecification"]]
    | tuple[Literal["literal"], Any]
    | tuple[
        Literal["number"],
        Union[Any, "ExpressionSpecification"],
        *tuple[Union[Any, "ExpressionSpecification"], ...],
    ]
    | tuple[
        Literal["number-format"],
        Union[float, "ExpressionSpecification"],
        dict[str, Union[str, float, "ExpressionSpecification"]],
    ]
    | tuple[
        Literal["object"],
        Union[Any, "ExpressionSpecification"],
        *tuple[Union[Any, "ExpressionSpecification"], ...],
    ]
    | tuple[
        Literal["string"],
        Union[Any, "ExpressionSpecification"],
        *tuple[Union[Any, "ExpressionSpecification"], ...],
    ]
    | tuple[Literal["to-boolean"], Union[Any, "ExpressionSpecification"]]
    | tuple[
        Literal["to-color"],
        Union[Any, "ExpressionSpecification"],
        *tuple[Union[Any, "ExpressionSpecification"], ...],
    ]
    | tuple[
        Literal["to-number"],
        Union[Any, "ExpressionSpecification"],
        *tuple[Union[Any, "ExpressionSpecification"], ...],
    ]
    | tuple[Literal["to-string"], Union[Any, "ExpressionSpecification"]]
    | tuple[Literal["typeof"], Union[Any, "ExpressionSpecification"]]
    | tuple[Literal["accumulated"]]
    | tuple[Literal["feature-state"], Union[str, "ExpressionSpecification"]]
    | tuple[Literal["geometry-type"]]
    | tuple[Literal["id"]]
    | tuple[Literal["line-progress"]]
    | tuple[Literal["properties"]]
    | tuple[
        Literal["at"],
        Union[float, "ExpressionSpecification"],
        "ExpressionSpecification",
    ]
    | tuple[
        Literal["get"],
        Union[str, "ExpressionSpecification"],
        # NotRequired["ExpressionSpecification"],
    ]
    | tuple[Literal["global-state"], str]
    | tuple[
        Literal["has"],
        Union[str, "ExpressionSpecification"],
        NotRequired["ExpressionSpecification"],
    ]
    | tuple[
        Literal["in"],
        Union[None, ExpressionInputType, "ExpressionSpecification"],
        Union[str, "ExpressionSpecification"],
    ]
    | tuple[
        Literal["index-of"],
        Union[None, ExpressionInputType, "ExpressionSpecification"],
        Union[str, "ExpressionSpecification"],
        NotRequired[Union[float, "ExpressionSpecification"]],
    ]
    | tuple[Literal["length"], Union[str, "ExpressionSpecification"]]
    | tuple[
        Literal["slice"],
        Union[str, "ExpressionSpecification"],
        Union[float, "ExpressionSpecification"],
        NotRequired[Union[float, "ExpressionSpecification"]],
    ]
    | tuple[Literal["!"], Union[bool, "ExpressionSpecification"]]
    | tuple[
        Literal["!="],
        Union[None, ExpressionInputType, "ExpressionSpecification"],
        Union[None, ExpressionInputType, "ExpressionSpecification"],
        NotRequired["CollatorExpressionSpecification"],
    ]
    | tuple[
        Literal["<"],
        Union[str, float, "ExpressionSpecification"],
        Union[str, float, "ExpressionSpecification"],
        NotRequired["CollatorExpressionSpecification"],
    ]
    | tuple[
        Literal["<="],
        Union[str, float, "ExpressionSpecification"],
        Union[str, float, "ExpressionSpecification"],
    ]
    | tuple[
        Literal["<="],
        Union[str, float, "ExpressionSpecification"],
        Union[str, float, "ExpressionSpecification"],
        "CollatorExpressionSpecification",
    ]
    | tuple[
        Literal["=="],
        Union[None, ExpressionInputType, "ExpressionSpecification"],
        Union[None, ExpressionInputType, "ExpressionSpecification"],
    ]
    | tuple[
        Literal["=="],
        Union[None, ExpressionInputType, "ExpressionSpecification"],
        Union[None, ExpressionInputType, "ExpressionSpecification"],
        "CollatorExpressionSpecification",
    ]
    | tuple[
        Literal[">"],
        Union[str, float, "ExpressionSpecification"],
        Union[str, float, "ExpressionSpecification"],
        NotRequired["CollatorExpressionSpecification"],
    ]
    | tuple[
        Literal[">="],
        Union[str, float, "ExpressionSpecification"],
        Union[str, float, "ExpressionSpecification"],
        NotRequired["CollatorExpressionSpecification"],
    ]
    | tuple[Literal["all"], *tuple[Union[bool, "ExpressionSpecification"], ...]]
    | tuple[Literal["any"], *tuple[Union[bool, "ExpressionSpecification"], ...]]
    | tuple[
        Literal["case"],
        Union[bool, "ExpressionSpecification"],
        Union[None, ExpressionInputType, "ExpressionSpecification"],
        *tuple[
            Union[bool, None, ExpressionInputType, "ExpressionSpecification"],
            ...,
        ],
        Union[None, ExpressionInputType, "ExpressionSpecification"],
    ]
    | tuple[
        Literal["coalesce"],
        *tuple[Union[ExpressionInputType, "ExpressionSpecification"], ...],
    ]
    | tuple[
        Literal["match"],
        Union[str, float, "ExpressionSpecification"],
        str | float | list[str] | list[float],
        Union[None, ExpressionInputType, "ExpressionSpecification"],
        *tuple[
            Union[
                str,
                float,
                list[str],
                list[float],
                None,
                ExpressionInputType,
                "ExpressionSpecification",
            ],
            ...,
        ],
        Union[None, ExpressionInputType, "ExpressionSpecification"],
    ]
    | tuple[Literal["within"], Any]
    | tuple[
        Literal["interpolate"],
        InterpolationSpecification,
        Union[float, "ExpressionSpecification"],
        *tuple[
            Union[
                float,
                ColorSpecification,
                "ExpressionSpecification",
                ProjectionDefinitionSpecification,
            ],
            ...,
        ],
    ]
    | tuple[
        Literal["interpolate-hcl"],
        InterpolationSpecification,
        Union[float, "ExpressionSpecification"],
        *tuple[
            Union[float, ColorSpecification, "ExpressionSpecification"],
            ...,
        ],
    ]
    | tuple[
        Literal["interpolate-lab"],
        InterpolationSpecification,
        Union[float, "ExpressionSpecification"],
        *tuple[
            Union[float, ColorSpecification, "ExpressionSpecification"],
            ...,
        ],
    ]
    | tuple[
        Literal["step"],
        Union[float, "ExpressionSpecification"],
        Union[ExpressionInputType, "ExpressionSpecification"],
        *tuple[
            Union[float, ExpressionInputType, "ExpressionSpecification"],
            ...,
        ],
    ]
    | tuple[
        Literal["let"],
        str,
        Union[ExpressionInputType, "ExpressionSpecification"],
        *tuple[Union[str, ExpressionInputType, "ExpressionSpecification"], ...],
    ]
    | tuple[Literal["var"], str]
    | tuple[
        Literal["concat"],
        *tuple[Union[ExpressionInputType, "ExpressionSpecification"], ...],
    ]
    | tuple[Literal["downcase"], Union[str, "ExpressionSpecification"]]
    | tuple[Literal["is-supported-script"], Union[str, "ExpressionSpecification"]]
    | tuple[Literal["resolved-locale"], CollatorExpressionSpecification]
    | tuple[Literal["upcase"], Union[str, "ExpressionSpecification"]]
    | tuple[
        Literal["rgb"],
        Union[float, "ExpressionSpecification"],
        Union[float, "ExpressionSpecification"],
        Union[float, "ExpressionSpecification"],
    ]
    | tuple[
        Literal["rgba"],
        Union[float, "ExpressionSpecification"],
        Union[float, "ExpressionSpecification"],
        Union[float, "ExpressionSpecification"],
        Union[float, "ExpressionSpecification"],
    ]
    | tuple[Literal["to-rgba"], Union[ColorSpecification, "ExpressionSpecification"]]
    | tuple[
        Literal["-"],
        Union[float, "ExpressionSpecification"],
        NotRequired[Union[float, "ExpressionSpecification"]],
    ]
    | tuple[
        Literal["*"],
        Union[float, "ExpressionSpecification"],
        Union[float, "ExpressionSpecification"],
        *tuple[Union[float, "ExpressionSpecification"], ...],
    ]
    | tuple[
        Literal["/"],
        Union[float, "ExpressionSpecification"],
        Union[float, "ExpressionSpecification"],
    ]
    | tuple[
        Literal["%"],
        Union[float, "ExpressionSpecification"],
        Union[float, "ExpressionSpecification"],
    ]
    | tuple[
        Literal["^"],
        Union[float, "ExpressionSpecification"],
        Union[float, "ExpressionSpecification"],
    ]
    | tuple[Literal["+"], *tuple[Union[float, "ExpressionSpecification"], ...]]
    | tuple[Literal["abs"], Union[float, "ExpressionSpecification"]]
    | tuple[Literal["acos"], Union[float, "ExpressionSpecification"]]
    | tuple[Literal["asin"], Union[float, "ExpressionSpecification"]]
    | tuple[Literal["atan"], Union[float, "ExpressionSpecification"]]
    | tuple[Literal["ceil"], Union[float, "ExpressionSpecification"]]
    | tuple[Literal["cos"], Union[float, "ExpressionSpecification"]]
    | tuple[Literal["distance"], Any]
    | tuple[Literal["e"]]
    | tuple[Literal["floor"], Union[float, "ExpressionSpecification"]]
    | tuple[Literal["ln"], Union[float, "ExpressionSpecification"]]
    | tuple[Literal["ln2"]]
    | tuple[Literal["log10"], Union[float, "ExpressionSpecification"]]
    | tuple[Literal["log2"], Union[float, "ExpressionSpecification"]]
    | tuple[
        Literal["max"],
        Union[float, "ExpressionSpecification"],
        *tuple[Union[float, "ExpressionSpecification"], ...],
    ]
    | tuple[
        Literal["min"],
        Union[float, "ExpressionSpecification"],
        *tuple[Union[float, "ExpressionSpecification"], ...],
    ]
    | tuple[Literal["pi"]]
    | tuple[Literal["round"], Union[float, "ExpressionSpecification"]]
    | tuple[Literal["sin"], Union[float, "ExpressionSpecification"]]
    | tuple[Literal["sqrt"], Union[float, "ExpressionSpecification"]]
    | tuple[Literal["tan"], Union[float, "ExpressionSpecification"]]
    | tuple[Literal["zoom"]]
    | tuple[Literal["heatmap-density"]]
    | tuple[Literal["elevation"]]
    | tuple[Literal["global-state"], str]
)

ExpressionFilterSpecification = Union[bool, "ExpressionSpecification"]

LegacyFilterSpecification = (
    tuple[Literal["has"], str]
    | tuple[Literal["!has"], str]
    | tuple[Literal["=="], str, str | float | bool]
    | tuple[Literal["!="], str, str | float | bool]
    | tuple[Literal[">"], str, str | float | bool]
    | tuple[Literal[">="], str, str | float | bool]
    | tuple[Literal["<"], str, str | float | bool]
    | tuple[Literal["<="], str, str | float | bool]
    | tuple[Literal["in"], str, *tuple[str | float | bool, ...]]
    | tuple[Literal["!in"], str, *tuple[str | float | bool, ...]]
    | tuple[Literal["all"], *tuple["LegacyFilterSpecification", ...]]
    | tuple[Literal["any"], *tuple["LegacyFilterSpecification", ...]]
    | tuple[Literal["none"], *tuple["LegacyFilterSpecification", ...]]
)

FilterSpecification = Union[ExpressionFilterSpecification, LegacyFilterSpecification]

VisibilitySpecification = Union[Literal["visible", "none"], "ExpressionSpecification"]


class TransitionSpecification(TypedDict):
    duration: NotRequired[float]
    delay: NotRequired[float]


class ExponentialCameraFunctionSpecification(TypedDict, Generic[T]):
    type: Literal["exponential"]
    stops: list[tuple[float, T]]


class IntervalCameraFunctionSpecification(TypedDict, Generic[T]):
    type: Literal["interval"]
    stops: list[tuple[float, T]]


CameraFunctionSpecification = (
    ExponentialCameraFunctionSpecification[T] | IntervalCameraFunctionSpecification[T]
)


class ExponentialSourceFunctionSpecification(TypedDict, Generic[T]):
    type: Literal["exponential"]
    stops: list[tuple[float, T]]
    property: str
    default: NotRequired[T]


class IntervalSourceFunctionSpecification(TypedDict, Generic[T]):
    type: Literal["interval"]
    stops: list[tuple[float, T]]
    property: str
    default: NotRequired[T]


class CategoricalSourceFunctionSpecification(TypedDict, Generic[T]):
    type: Literal["categorical"]
    stops: list[tuple[str | float | bool, T]]
    property: str
    default: NotRequired[T]


class IdentitySourceFunctionSpecification(TypedDict, Generic[T]):
    type: Literal["identity"]
    property: str
    default: NotRequired[T]


SourceFunctionSpecification = (
    ExponentialSourceFunctionSpecification[T]
    | IntervalSourceFunctionSpecification[T]
    | CategoricalSourceFunctionSpecification[T]
    | IdentitySourceFunctionSpecification[T]
)


class ZoomValueDict(TypedDict):
    zoom: float
    value: float


class ExponentialCompositeFunctionSpecification(TypedDict, Generic[T]):
    type: Literal["exponential"]
    stops: list[tuple[ZoomValueDict, T]]
    property: str
    default: NotRequired[T]


class IntervalCompositeFunctionSpecification(TypedDict, Generic[T]):
    type: Literal["interval"]
    stops: list[tuple[ZoomValueDict, T]]
    property: str
    default: NotRequired[T]


class CategoricalCompositeFunctionSpecification(TypedDict, Generic[T]):
    type: Literal["categorical"]
    stops: list[tuple[ZoomValueDict | float | bool, T]]
    property: str
    default: NotRequired[T]


CompositeFunctionSpecification = (
    ExponentialCompositeFunctionSpecification[T]
    | IntervalCompositeFunctionSpecification[T]
    | CategoricalCompositeFunctionSpecification[T]
)


PropertyValueSpecification = Union[
    T,
    CameraFunctionSpecification[T],
    "ExpressionSpecification",
]

DataDrivenPropertyValueSpecification = Union[
    T,
    CameraFunctionSpecification[T],
    SourceFunctionSpecification[T],
    CompositeFunctionSpecification[T],
    "ExpressionSpecification",
]


SymbolLayerSpecification = TypedDict(
    "SymbolLayerSpecification",
    {
        "id": str,
        "type": Literal["symbol"],
        "metadata": NotRequired[Any],
        "source": str,
        "source-layer": NotRequired[str],
        "minzoom": NotRequired[float],
        "maxzoom": NotRequired[float],
        "filter": NotRequired[FilterSpecification],
        "layout": NotRequired[dict[str, Any]],
        "paint": NotRequired[dict[str, Any]],
    },
)


class VectorSource(TypedDict):
    type: Literal["vector"]
    url: NotRequired[str]
    tiles: NotRequired[list[str]]
    bounds: NotRequired[tuple[float, float, float, float]]
    scheme: NotRequired[Literal["xyz", "tms"]]
    minzoom: NotRequired[float]
    maxzoom: NotRequired[float]
    attribution: NotRequired[str]
    promoteId: NotRequired[dict[str, str] | str]
    volatile: NotRequired[bool]
    encoding: NotRequired[Literal["mvt", "mlt"]]


class RasterSource(TypedDict):
    type: Literal["raster"]
    url: NotRequired[str]
    tiles: NotRequired[list[str]]
    bounds: NotRequired[tuple[float, float, float, float]]
    minzoom: NotRequired[float]
    maxzoom: NotRequired[float]
    tileSize: NotRequired[float]
    scheme: NotRequired[Literal["xyz", "tms"]]
    attribution: NotRequired[str]
    promoteId: NotRequired[str | dict[str, str]]
    volatile: NotRequired[bool]


class RasterDEMSource(TypedDict):
    type: Literal["raster-dem"]
    url: NotRequired[str]
    tiles: NotRequired[list[str]]
    bounds: NotRequired[tuple[float, float, float, float]]
    minzoom: NotRequired[float]
    maxzoom: NotRequired[float]
    tileSize: NotRequired[float]
    scheme: NotRequired[Literal["xyz", "tms"]]
    attribution: NotRequired[str]
    encoding: Literal["terrarium", "mapbox", "custom"]
    promoteId: dict[str, str] | NotRequired[str]
    redFactor: NotRequired[float]
    blueFactor: NotRequired[float]
    greenFactor: NotRequired[float]
    baseShift: NotRequired[float]
    volatile: NotRequired[float]


class GeoJSONSource(TypedDict):
    type: Literal["geojson"]
    data: GeoJSON | str
    maxzoom: NotRequired[float]
    attribution: NotRequired[str]
    buffer: NotRequired[float]
    filter: NotRequired[FilterSpecification]
    tolerance: NotRequired[float]
    cluster: NotRequired[bool]
    clusterRadius: NotRequired[float]
    clusterMaxZoom: NotRequired[float]
    clusterMinPoints: NotRequired[float]
    clusterProperties: NotRequired[Any]
    lineMetrics: NotRequired[bool]
    generateId: NotRequired[bool]
    promoteId: NotRequired[dict[str, str] | str]


# export type VideoSourceSpecification = {
#   /**
#    * The data type of the video source.
#    */
# type: "video";
#   /**
#    * URLs to video content in order of preferred format.
#    */
#   urls: Array<string>;
#   /**
#    * Corners of video specified in longitude, latitude pairs.
#    */
#   coordinates: [
#     [number, number],
#     [number, number],
#     [number, number],
#     [number, number],
#   ];
# };

# export type ImageSourceSpecification = {
#   /**
#    * The data type of the image source.
#    */
# type: "image";
#   /**
#    * URL that points to an image.
#    */
#   url: string;
#   /**
#    * Corners of image specified in longitude, latitude pairs.
#    */
#   coordinates: [
#     [number, number],
#     [number, number],
#     [number, number],
#     [number, number],
#   ];
# };

# VideoSourceSpecification
# ImageSourceSpecification;


FillLayer = TypedDict(
    "FillLayer",
    {
        "id": str,
        "type": Literal["fill"],
        "metadata": NotRequired[Any],
        "source": str,
        "source-layer": NotRequired[str],
        "minzoom": NotRequired[int],
        "maxzoom": NotRequired[int],
        "filter": NotRequired[FilterSpecification],
        "layout": NotRequired[dict[str, Any]],
        "paint": NotRequired[dict[str, Any]],
    },
)


LineLayer = TypedDict(
    "LineLayer",
    {
        "id": str,
        "type": Literal["line"],
        "metadata": NotRequired[Any],
        "source": str,
        "source-layer": NotRequired[str],
        "minzoom": NotRequired[int],
        "maxzoom": NotRequired[int],
        "filter": NotRequired[FilterSpecification],
        "layout": NotRequired[dict[str, Any]],
        "paint": NotRequired[dict[str, Any]],
    },
)


SymbolLayer = TypedDict(
    "SymbolLayer",
    {
        "id": str,
        "type": Literal["symbol"],
        "metadata": NotRequired[Any],
        "source": str,
        "source-layer": NotRequired[str],
        "minzoom": NotRequired[float],
        "maxzoom": NotRequired[float],
        "filter": NotRequired[FilterSpecification],
        "layout": NotRequired[dict[str, Any]],
        "paint": NotRequired[dict[str, Any]],
    },
)

RasterPaint = TypedDict(
    "RasterPaint",
    {
        "raster-opacity": NotRequired[PropertyValueSpecification[float]]
        # "raster-opacity-transition"?: TransitionSpecification;
        # "raster-hue-rotate"?: PropertyValueSpecification<number>;
        # "raster-hue-rotate-transition"?: TransitionSpecification;
        # "raster-brightness-min"?: PropertyValueSpecification<number>;
        # "raster-brightness-min-transition"?: TransitionSpecification;
        # "raster-brightness-max"?: PropertyValueSpecification<number>;
        # "raster-brightness-max-transition"?: TransitionSpecification;
        # "raster-saturation"?: PropertyValueSpecification<number>;
        # "raster-saturation-transition"?: TransitionSpecification;
        # "raster-contrast"?: PropertyValueSpecification<number>;
        # "raster-contrast-transition"?: TransitionSpecification;
        # "raster-resampling"?: PropertyValueSpecification<"linear" | "nearest">;
        # "raster-fade-duration"?: PropertyValueSpecification<number>;
    },
)

RasterLayer = TypedDict(
    "RasterLayer",
    {
        "id": str,
        "type": Literal["raster"],
        "metadata": NotRequired[Any],
        "source": str,
        "source-layer": NotRequired[str],
        "minzoom": NotRequired[float],
        "maxzoom": NotRequired[float],
        "filter": NotRequired[FilterSpecification],
        "layout": NotRequired[dict[str, Any]],
        "paint": NotRequired[RasterPaint],
    },
)

CircleLayer = TypedDict(
    "CircleLayer",
    {
        "id": str,
        "type": Literal["circle"],
        "metadata": NotRequired[Any],
        "source": str,
        "source-layer": NotRequired[str],
        "minzoom": NotRequired[float],
        "maxzoom": NotRequired[float],
        "filter": NotRequired[FilterSpecification],
        # "layout": NotRequired[TypedDict(
        #     "CircleLayout",
        #     {
        #         "circle-sort-key": NotRequired[DataDrivenPropertyValueSpecification[float]],
        #         "visibility": NotRequired[VisibilitySpecification],
        #     }
        # )],
        # "paint": NotRequired[TypedDict(
        #     "CirclePaint",
        #     {
        #         "circle-radius": NotRequired[DataDrivenPropertyValueSpecification[float]],
        #         "circle-radius-transition": NotRequired[TransitionSpecification],
        #         "circle-color": NotRequired[DataDrivenPropertyValueSpecification[ColorSpecification]],
        #         "circle-color-transition": NotRequired[TransitionSpecification],
        #         "circle-blur": NotRequired[DataDrivenPropertyValueSpecification[float]],
        #         "circle-blur-transition": NotRequired[TransitionSpecification],
        #         "circle-opacity": NotRequired[DataDrivenPropertyValueSpecification[float]],
        #         "circle-opacity-transition": NotRequired[TransitionSpecification],
        #         "circle-translate": NotRequired[PropertyValueSpecification[Tuple[float, float]]],
        #         "circle-translate-transition": NotRequired[TransitionSpecification],
        #         "circle-translate-anchor": NotRequired[PropertyValueSpecification[Literal["map", "viewport"]]],
        #         "circle-pitch-scale": NotRequired[PropertyValueSpecification[Literal["map", "viewport"]]],
        #         "circle-pitch-alignment": NotRequired[PropertyValueSpecification[Literal["map", "viewport"]]],
        #         "circle-stroke-width": NotRequired[DataDrivenPropertyValueSpecification[float]],
        #         "circle-stroke-width-transition": NotRequired[TransitionSpecification],
        #         "circle-stroke-color": NotRequired[DataDrivenPropertyValueSpecification[ColorSpecification]],
        #         "circle-stroke-color-transition": NotRequired[TransitionSpecification],
        #         "circle-stroke-opacity": NotRequired[DataDrivenPropertyValueSpecification[float]],
        #         "circle-stroke-opacity-transition": NotRequired[TransitionSpecification],
        #     }
        # )],
    },
)

Source = VectorSource | RasterSource | RasterDEMSource | GeoJSONSource
Layer = FillLayer | LineLayer | SymbolLayer | RasterLayer | CircleLayer


class Style(TypedDict):
    version: Literal[8]
    name: NotRequired[str]
    metadata: NotRequired[Any]
    # center?: [number, number];
    # centerAltitude?: number;
    # zoom?: number;
    # bearing?: number;
    # pitch?: number;
    # roll?: number;
    # state?: StateSpecification;
    # light?: LightSpecification;
    # sky?: SkySpecification;
    # projection: NotRequired[ProjectionSpecification]
    # terrain?: TerrainSpecification;
    sources: dict[str, Source]
    # sprite?: SpriteSpecification;
    # glyphs?: string;
    # "font-faces"?: FontFacesSpecification;
    # transition?: TransitionSpecification
    layers: list[Layer]

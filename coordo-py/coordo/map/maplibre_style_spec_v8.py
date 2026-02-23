# Not all definitions have been imported from common/maplibre-style-spec-v8.ts
# Please add them when needed

from typing import (
    Any,
    Dict,
    Generic,
    List,
    Literal,
    NotRequired,
    Tuple,
    TypedDict,
    TypeVar,
    Union,
)

from geojson import GeoJSON

T = TypeVar("T")

ColorSpecification = str
PaddingSpecification = Union[float, List[float]]
NumberArraySpecification = Union[float, List[float]]
ColorArraySpecification = Union[str, List[str]]
VariableAnchorOffsetCollectionSpecification = List[Union[str, Tuple[float, float]]]
SpriteSpecification = Union[str, List[Dict[str, str]]]
FormattedSpecification = str
ResolvedImageSpecification = str
PromoteIdSpecification = Union[Dict[str, str], str]
ExpressionInputType = Union[str, float, bool]
CollatorExpression = TypedDict(
    "CollatorExpression",
    {
        "case-sensitive": NotRequired[Union[bool, "ExpressionSpecification"]],
        "diacritic-sensitive": Union[bool, "ExpressionSpecification"],
        "locale": NotRequired[Union[str, "ExpressionSpecification"]],
    },
)
CollatorExpressionSpecification = Tuple[Literal["collator"], CollatorExpression]

InterpolationSpecification = (
    Tuple[Literal["linear"]]
    | Tuple[Literal["exponential"], float]
    | Tuple[Literal["cubic-bezier"], float, float, float, float]
)
ProjectionDefinition = Tuple[str, str, float]
ProjectionDefinitionSpecification = Union[
    str,
    ProjectionDefinition,
    "PropertyValueSpecification[ProjectionDefinition]",
]

ExpressionSpecification = (
    Tuple[Literal["array"], "ExpressionSpecification"]
    | Tuple[
        Literal["array"],
        Union[Literal["string"], Literal["number"], Literal["boolean"]],
        "ExpressionSpecification",
    ]
    | Tuple[
        Literal["array"],
        Union[Literal["string"], Literal["number"], Literal["boolean"]],
        float,
        "ExpressionSpecification",
    ]
    | Tuple[
        Literal["boolean"],
        Union[Any, "ExpressionSpecification"],
        *Tuple[Union[Any, "ExpressionSpecification"], ...],
    ]
    | CollatorExpressionSpecification
    | Tuple[
        Literal["format"],
        *Tuple[
            str
            | Tuple[Literal["image"], "ExpressionSpecification"]
            | "ExpressionSpecification"
            | Dict[
                str,
                Union[
                    float,
                    "ExpressionSpecification",
                    ColorSpecification,
                    "ExpressionSpecification",
                    Literal["bottom", "center", "top"],
                ],
            ],
            ...,
        ],
    ]
    | Tuple[Literal["image"], Union[str, "ExpressionSpecification"]]
    | Tuple[Literal["literal"], Any]
    | Tuple[
        Literal["number"],
        Union[Any, "ExpressionSpecification"],
        *Tuple[Union[Any, "ExpressionSpecification"], ...],
    ]
    | Tuple[
        Literal["number-format"],
        Union[float, "ExpressionSpecification"],
        Dict[str, Union[str, float, "ExpressionSpecification"]],
    ]
    | Tuple[
        Literal["object"],
        Union[Any, "ExpressionSpecification"],
        *Tuple[Union[Any, "ExpressionSpecification"], ...],
    ]
    | Tuple[
        Literal["string"],
        Union[Any, "ExpressionSpecification"],
        *Tuple[Union[Any, "ExpressionSpecification"], ...],
    ]
    | Tuple[Literal["to-boolean"], Union[Any, "ExpressionSpecification"]]
    | Tuple[
        Literal["to-color"],
        Union[Any, "ExpressionSpecification"],
        *Tuple[Union[Any, "ExpressionSpecification"], ...],
    ]
    | Tuple[
        Literal["to-number"],
        Union[Any, "ExpressionSpecification"],
        *Tuple[Union[Any, "ExpressionSpecification"], ...],
    ]
    | Tuple[Literal["to-string"], Union[Any, "ExpressionSpecification"]]
    | Tuple[Literal["typeof"], Union[Any, "ExpressionSpecification"]]
    | Tuple[Literal["accumulated"]]
    | Tuple[Literal["feature-state"], Union[str, "ExpressionSpecification"]]
    | Tuple[Literal["geometry-type"]]
    | Tuple[Literal["id"]]
    | Tuple[Literal["line-progress"]]
    | Tuple[Literal["properties"]]
    | Tuple[
        Literal["at"],
        Union[float, "ExpressionSpecification"],
        "ExpressionSpecification",
    ]
    | Tuple[
        Literal["get"],
        Union[str, "ExpressionSpecification"],
        # NotRequired["ExpressionSpecification"],
    ]
    | Tuple[Literal["global-state"], str]
    | Tuple[
        Literal["has"],
        Union[str, "ExpressionSpecification"],
        NotRequired["ExpressionSpecification"],
    ]
    | Tuple[
        Literal["in"],
        Union[None, ExpressionInputType, "ExpressionSpecification"],
        Union[str, "ExpressionSpecification"],
    ]
    | Tuple[
        Literal["index-of"],
        Union[None, ExpressionInputType, "ExpressionSpecification"],
        Union[str, "ExpressionSpecification"],
        NotRequired[Union[float, "ExpressionSpecification"]],
    ]
    | Tuple[Literal["length"], Union[str, "ExpressionSpecification"]]
    | Tuple[
        Literal["slice"],
        Union[str, "ExpressionSpecification"],
        Union[float, "ExpressionSpecification"],
        NotRequired[Union[float, "ExpressionSpecification"]],
    ]
    | Tuple[Literal["!"], Union[bool, "ExpressionSpecification"]]
    | Tuple[
        Literal["!="],
        Union[None, ExpressionInputType, "ExpressionSpecification"],
        Union[None, ExpressionInputType, "ExpressionSpecification"],
        NotRequired["CollatorExpressionSpecification"],
    ]
    | Tuple[
        Literal["<"],
        Union[str, float, "ExpressionSpecification"],
        Union[str, float, "ExpressionSpecification"],
        NotRequired["CollatorExpressionSpecification"],
    ]
    | Tuple[
        Literal["<="],
        Union[str, float, "ExpressionSpecification"],
        Union[str, float, "ExpressionSpecification"],
    ]
    | Tuple[
        Literal["<="],
        Union[str, float, "ExpressionSpecification"],
        Union[str, float, "ExpressionSpecification"],
        "CollatorExpressionSpecification",
    ]
    | Tuple[
        Literal["=="],
        Union[None, ExpressionInputType, "ExpressionSpecification"],
        Union[None, ExpressionInputType, "ExpressionSpecification"],
    ]
    | Tuple[
        Literal["=="],
        Union[None, ExpressionInputType, "ExpressionSpecification"],
        Union[None, ExpressionInputType, "ExpressionSpecification"],
        "CollatorExpressionSpecification",
    ]
    | Tuple[
        Literal[">"],
        Union[str, float, "ExpressionSpecification"],
        Union[str, float, "ExpressionSpecification"],
        NotRequired["CollatorExpressionSpecification"],
    ]
    | Tuple[
        Literal[">="],
        Union[str, float, "ExpressionSpecification"],
        Union[str, float, "ExpressionSpecification"],
        NotRequired["CollatorExpressionSpecification"],
    ]
    | Tuple[Literal["all"], *Tuple[Union[bool, "ExpressionSpecification"], ...]]
    | Tuple[Literal["any"], *Tuple[Union[bool, "ExpressionSpecification"], ...]]
    | Tuple[
        Literal["case"],
        Union[bool, "ExpressionSpecification"],
        Union[None, ExpressionInputType, "ExpressionSpecification"],
        *Tuple[
            Union[bool, None, ExpressionInputType, "ExpressionSpecification"],
            ...,
        ],
        Union[None, ExpressionInputType, "ExpressionSpecification"],
    ]
    | Tuple[
        Literal["coalesce"],
        *Tuple[Union[ExpressionInputType, "ExpressionSpecification"], ...],
    ]
    | Tuple[
        Literal["match"],
        Union[str, float, "ExpressionSpecification"],
        Union[str, float, List[str], List[float]],
        Union[None, ExpressionInputType, "ExpressionSpecification"],
        *Tuple[
            Union[
                str,
                float,
                List[str],
                List[float],
                None,
                ExpressionInputType,
                "ExpressionSpecification",
            ],
            ...,
        ],
        Union[None, ExpressionInputType, "ExpressionSpecification"],
    ]
    | Tuple[Literal["within"], Any]
    | Tuple[
        Literal["interpolate"],
        InterpolationSpecification,
        Union[float, "ExpressionSpecification"],
        *Tuple[
            Union[
                float,
                ColorSpecification,
                "ExpressionSpecification",
                ProjectionDefinitionSpecification,
            ],
            ...,
        ],
    ]
    | Tuple[
        Literal["interpolate-hcl"],
        InterpolationSpecification,
        Union[float, "ExpressionSpecification"],
        *Tuple[
            Union[float, ColorSpecification, "ExpressionSpecification"],
            ...,
        ],
    ]
    | Tuple[
        Literal["interpolate-lab"],
        InterpolationSpecification,
        Union[float, "ExpressionSpecification"],
        *Tuple[
            Union[float, ColorSpecification, "ExpressionSpecification"],
            ...,
        ],
    ]
    | Tuple[
        Literal["step"],
        Union[float, "ExpressionSpecification"],
        Union[ExpressionInputType, "ExpressionSpecification"],
        *Tuple[
            Union[float, ExpressionInputType, "ExpressionSpecification"],
            ...,
        ],
    ]
    | Tuple[
        Literal["let"],
        str,
        Union[ExpressionInputType, "ExpressionSpecification"],
        *Tuple[Union[str, ExpressionInputType, "ExpressionSpecification"], ...],
    ]
    | Tuple[Literal["var"], str]
    | Tuple[
        Literal["concat"],
        *Tuple[Union[ExpressionInputType, "ExpressionSpecification"], ...],
    ]
    | Tuple[Literal["downcase"], Union[str, "ExpressionSpecification"]]
    | Tuple[Literal["is-supported-script"], Union[str, "ExpressionSpecification"]]
    | Tuple[Literal["resolved-locale"], CollatorExpressionSpecification]
    | Tuple[Literal["upcase"], Union[str, "ExpressionSpecification"]]
    | Tuple[
        Literal["rgb"],
        Union[float, "ExpressionSpecification"],
        Union[float, "ExpressionSpecification"],
        Union[float, "ExpressionSpecification"],
    ]
    | Tuple[
        Literal["rgba"],
        Union[float, "ExpressionSpecification"],
        Union[float, "ExpressionSpecification"],
        Union[float, "ExpressionSpecification"],
        Union[float, "ExpressionSpecification"],
    ]
    | Tuple[Literal["to-rgba"], Union[ColorSpecification, "ExpressionSpecification"]]
    | Tuple[
        Literal["-"],
        Union[float, "ExpressionSpecification"],
        NotRequired[Union[float, "ExpressionSpecification"]],
    ]
    | Tuple[
        Literal["*"],
        Union[float, "ExpressionSpecification"],
        Union[float, "ExpressionSpecification"],
        *Tuple[Union[float, "ExpressionSpecification"], ...],
    ]
    | Tuple[
        Literal["/"],
        Union[float, "ExpressionSpecification"],
        Union[float, "ExpressionSpecification"],
    ]
    | Tuple[
        Literal["%"],
        Union[float, "ExpressionSpecification"],
        Union[float, "ExpressionSpecification"],
    ]
    | Tuple[
        Literal["^"],
        Union[float, "ExpressionSpecification"],
        Union[float, "ExpressionSpecification"],
    ]
    | Tuple[Literal["+"], *Tuple[Union[float, "ExpressionSpecification"], ...]]
    | Tuple[Literal["abs"], Union[float, "ExpressionSpecification"]]
    | Tuple[Literal["acos"], Union[float, "ExpressionSpecification"]]
    | Tuple[Literal["asin"], Union[float, "ExpressionSpecification"]]
    | Tuple[Literal["atan"], Union[float, "ExpressionSpecification"]]
    | Tuple[Literal["ceil"], Union[float, "ExpressionSpecification"]]
    | Tuple[Literal["cos"], Union[float, "ExpressionSpecification"]]
    | Tuple[Literal["distance"], Any]
    | Tuple[Literal["e"]]
    | Tuple[Literal["floor"], Union[float, "ExpressionSpecification"]]
    | Tuple[Literal["ln"], Union[float, "ExpressionSpecification"]]
    | Tuple[Literal["ln2"]]
    | Tuple[Literal["log10"], Union[float, "ExpressionSpecification"]]
    | Tuple[Literal["log2"], Union[float, "ExpressionSpecification"]]
    | Tuple[
        Literal["max"],
        Union[float, "ExpressionSpecification"],
        *Tuple[Union[float, "ExpressionSpecification"], ...],
    ]
    | Tuple[
        Literal["min"],
        Union[float, "ExpressionSpecification"],
        *Tuple[Union[float, "ExpressionSpecification"], ...],
    ]
    | Tuple[Literal["pi"]]
    | Tuple[Literal["round"], Union[float, "ExpressionSpecification"]]
    | Tuple[Literal["sin"], Union[float, "ExpressionSpecification"]]
    | Tuple[Literal["sqrt"], Union[float, "ExpressionSpecification"]]
    | Tuple[Literal["tan"], Union[float, "ExpressionSpecification"]]
    | Tuple[Literal["zoom"]]
    | Tuple[Literal["heatmap-density"]]
    | Tuple[Literal["elevation"]]
    | Tuple[Literal["global-state"], str]
)

ExpressionFilterSpecification = Union[bool, "ExpressionSpecification"]

LegacyFilterSpecification = (
    Tuple[Literal["has"], str]
    | Tuple[Literal["!has"], str]
    | Tuple[Literal["=="], str, Union[str, float, bool]]
    | Tuple[Literal["!="], str, Union[str, float, bool]]
    | Tuple[Literal[">"], str, Union[str, float, bool]]
    | Tuple[Literal[">="], str, Union[str, float, bool]]
    | Tuple[Literal["<"], str, Union[str, float, bool]]
    | Tuple[Literal["<="], str, Union[str, float, bool]]
    | Tuple[Literal["in"], str, *Tuple[Union[str, float, bool], ...]]
    | Tuple[Literal["!in"], str, *Tuple[Union[str, float, bool], ...]]
    | Tuple[Literal["all"], *Tuple["LegacyFilterSpecification", ...]]
    | Tuple[Literal["any"], *Tuple["LegacyFilterSpecification", ...]]
    | Tuple[Literal["none"], *Tuple["LegacyFilterSpecification", ...]]
)

FilterSpecification = Union[ExpressionFilterSpecification, LegacyFilterSpecification]

VisibilitySpecification = Union[Literal["visible", "none"], "ExpressionSpecification"]


class TransitionSpecification(TypedDict):
    duration: NotRequired[float]
    delay: NotRequired[float]


class ExponentialCameraFunctionSpecification(TypedDict, Generic[T]):
    type: Literal["exponential"]
    stops: List[Tuple[float, T]]


class IntervalCameraFunctionSpecification(TypedDict, Generic[T]):
    type: Literal["interval"]
    stops: List[Tuple[float, T]]


CameraFunctionSpecification = (
    ExponentialCameraFunctionSpecification[T] | IntervalCameraFunctionSpecification[T]
)


class ExponentialSourceFunctionSpecification(TypedDict, Generic[T]):
    type: Literal["exponential"]
    stops: List[Tuple[float, T]]
    property: str
    default: NotRequired[T]


class IntervalSourceFunctionSpecification(TypedDict, Generic[T]):
    type: Literal["interval"]
    stops: List[Tuple[float, T]]
    property: str
    default: NotRequired[T]


class CategoricalSourceFunctionSpecification(TypedDict, Generic[T]):
    type: Literal["categorical"]
    stops: List[Tuple[str | float | bool, T]]
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
    stops: List[Tuple[ZoomValueDict, T]]
    property: str
    default: NotRequired[T]


class IntervalCompositeFunctionSpecification(TypedDict, Generic[T]):
    type: Literal["interval"]
    stops: List[Tuple[ZoomValueDict, T]]
    property: str
    default: NotRequired[T]


class CategoricalCompositeFunctionSpecification(TypedDict, Generic[T]):
    type: Literal["categorical"]
    stops: List[Tuple[ZoomValueDict | float | bool, T]]
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
        "layout": NotRequired[Dict[str, Any]],
        "paint": NotRequired[Dict[str, Any]],
    },
)


class VectorSource(TypedDict):
    type: Literal["vector"]
    url: NotRequired[str]
    tiles: NotRequired[list[str]]
    bounds: NotRequired[tuple[float, float, float, float]]
    scheme: NotRequired[Union[Literal["xyz"], Literal["tms"]]]
    minzoom: NotRequired[float]
    maxzoom: NotRequired[float]
    attribution: NotRequired[str]
    promoteId: NotRequired[Union[dict[str, str], str]]
    volatile: NotRequired[bool]
    encoding: NotRequired[Union[Literal["mvt"], Literal["mlt"]]]


class RasterSource(TypedDict):
    type: Literal["raster"]
    url: NotRequired[str]
    tiles: NotRequired[list[str]]
    bounds: NotRequired[tuple[float, float, float, float]]
    minzoom: NotRequired[float]
    maxzoom: NotRequired[float]
    tileSize: NotRequired[float]
    scheme: NotRequired[Union[Literal["xyz"], Literal["tms"]]]
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
    scheme: NotRequired[Union[Literal["xyz"], Literal["tms"]]]
    attribution: NotRequired[str]
    encoding: Union[Literal["terrarium"], Literal["mapbox"], Literal["custom"]]
    promoteId: Union[dict[str, str], NotRequired[str]]
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
        "layout": NotRequired[Dict[str, Any]],
        "paint": NotRequired[Dict[str, Any]],
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
        "layout": NotRequired[Dict[str, Any]],
        "paint": NotRequired[Dict[str, Any]],
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
        "layout": NotRequired[Dict[str, Any]],
        "paint": NotRequired[Dict[str, Any]],
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
        "layout": NotRequired[Dict[str, Any]],
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

# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

import pytest
from pydantic import ValidationError

from coordo.map.datapackage import DataPackageLayer

EMPTY_FC = {"type": "FeatureCollection", "features": []}


def make_layer(**extra):
    return DataPackageLayer(
        id="inventaire",
        type="datapackage",
        path="../catalog/inventaire",
        resource="inventaire_id",
        **extra,
    )


def test_cluster_source_emits_maplibre_cluster_props():
    layer = make_layer(cluster={"radius": 50, "maxZoom": 12.5})
    source = layer._build_source(EMPTY_FC)
    assert source["cluster"] is True
    assert source["clusterRadius"] == 50
    assert source["clusterMaxZoom"] == 12.5
    # Not provided -> not emitted
    assert "clusterMinPoints" not in source


def test_cluster_defaults_apply_when_block_present_but_empty():
    layer = make_layer(cluster={})
    source = layer._build_source(EMPTY_FC)
    assert source["cluster"] is True
    assert source["clusterRadius"] == 50
    assert source["clusterMaxZoom"] == 12.5


def test_cluster_min_points_emitted_when_set():
    layer = make_layer(cluster={"minPoints": 3})
    source = layer._build_source(EMPTY_FC)
    assert source["clusterMinPoints"] == 3


def test_no_cluster_by_default():
    layer = make_layer()
    source = layer._build_source(EMPTY_FC)
    assert "cluster" not in source
    assert source["type"] == "geojson"


def test_cluster_render_style_in_metadata():
    layer = make_layer(
        cluster={
            "colors": ["#99D6C2", "#009966", "#006B47"],
            "radii": [20, 30, 40],
            "steps": [100, 750],
        }
    )
    meta = layer._cluster_metadata()
    assert meta == {
        "colors": ["#99D6C2", "#009966", "#006B47"],
        "radii": [20, 30, 40],
        "steps": [100, 750],
    }
    # Render style stays out of the source (not a valid MapLibre source option)
    source = layer._build_source(EMPTY_FC)
    assert "colors" not in source


def test_cluster_metadata_omits_unset_style_keys():
    layer = make_layer(cluster={"colors": ["#a", "#b", "#c"], "steps": [10, 20]})
    assert layer._cluster_metadata() == {
        "colors": ["#a", "#b", "#c"],
        "steps": [10, 20],
    }


def test_cluster_metadata_is_none_without_style():
    # Clustering enabled but no render style -> nothing for the frontend metadata
    assert make_layer(cluster={})._cluster_metadata() is None
    assert make_layer(cluster={"radius": 50})._cluster_metadata() is None
    assert make_layer()._cluster_metadata() is None


def test_cluster_rejects_inconsistent_lengths():
    with pytest.raises(ValidationError):
        make_layer(cluster={"colors": ["#a", "#b"], "steps": [10, 20]})  # need 3 colors
    with pytest.raises(ValidationError):
        make_layer(cluster={"colors": ["#a", "#b", "#c"], "radii": [1, 2]})

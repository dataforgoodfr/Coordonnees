# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

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

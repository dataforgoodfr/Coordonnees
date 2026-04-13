/**
 * Copyright COORDONNÉES 2025, 2026
 * SPDX-License-Identifier: MPL-2.0
 */

import type { Map as MapLibreMap } from "maplibre-gl";

export function getLayerSymbolId({ layerId }: { layerId: string }) {
  return `${layerId}-symbol-layer`;
}

function getLayerSymbolPictureId({ layerId }: { layerId: string }) {
  return `${layerId}-symbol-picture-identifier`;
}

export function makeSetLayerSymbol({ map }: { map: MapLibreMap }) {
  /**
   * Update the icon-image of a Layer Layout.
   * To use an external image, use symbolUrl.
   * To use an image from your sprite, use spriteId
   * @param params.layerId —  The ID of the layer to set the layout property in.
   * @param params.imageUrl — The URL of the image file. Image file must be in png, webp, or jpg format.
   * @param params.spriteId — The ID of the image to load from the sprite attached to the map instance.
   * @param params.iconSize — The units in factor of the original icon size
   * @param params.fallbackId — The ID of a picture (from a sprite or from addImage)
   * to use as fallback when the main image couldn't load.
   */
  async function setLayerSymbolViaProperty({
    layerId,
    iconSize = 1,
    fallbackId,
    imageUrl,
    spriteId,
  }: {
    layerId: string;
    iconSize?: number;
    fallbackId?: string;
  } & (
    | { imageUrl: string; spriteId?: null }
    | { spriteId: string; imageUrl?: null }
  )) {
    let pictureId: string = "";

    if (spriteId) {
      pictureId = spriteId;
    }

    if (imageUrl) {
      const image = await map.loadImage(imageUrl);
      const imageId = getLayerSymbolPictureId({ layerId });
      map.addImage(imageId, image.data);
      pictureId = imageId;
    }

    const finalId = fallbackId
      ? ["coalesce", ["image", pictureId], ["image", fallbackId]]
      : pictureId;
    map.setLayoutProperty(layerId, "icon-image", finalId);
    map.setLayoutProperty(layerId, "icon-size", iconSize);
  }

  return setLayerSymbolViaProperty;
}

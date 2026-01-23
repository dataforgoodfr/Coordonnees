class LayerControl {
  constructor(options = {}) {
    this._map = null;
    this._container = null;
    this._panel = null;
  }

  onAdd(map) {
    this._map = map;
    this._container = document.createElement("div");
    this._container.className = "maplibregl-ctrl maplibregl-ctrl-group";
    this._container.innerHTML = "<button>L</button>";

    this._panel = document.createElement("div");
    this._panel.className =
      "maplibregl-ctrl-group maplibregl-ctrl-layer hidden";
    this._buildLayerList();
    this._container.appendChild(this._panel);

    this._container.addEventListener("click", () =>
      this._panel.classList.toggle("hidden"),
    );

    this._panel.addEventListener("click", (e) => e.stopPropagation());
    this._map.on("click", () => this._panel.classList.toggle("hidden"));

    return this._container;
  }

  _buildLayerList() {
    const layers = this._map.getStyle().layers;

    layers.forEach((layer) => {
      const layerId = layer.id;

      const label = document.createElement("label");
      label.style.display = "flex";
      label.style.cursor = "pointer";

      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.checked =
        this._map.getLayoutProperty(layerId, "visibility") !== "none";

      checkbox.addEventListener("change", () => {
        this._map.setLayoutProperty(
          layerId,
          "visibility",
          checkbox.checked ? "visible" : "none",
        );
      });

      label.appendChild(checkbox);
      label.appendChild(document.createTextNode(" " + layerId));

      this._panel.appendChild(label);
    });
  }

  onRemove() {
    this._container.remove();
    this._map = null;
  }
}

function renderTemplate(html, vars) {
  return html.replace(/{{\s*(\w+)\s*}}/g, (_, key) =>
    key in vars ? vars[key] : "",
  );
}

export function createMap(target, options = {}) {
  const el =
    typeof target === "string" ? document.querySelector(target) : target;

  if (!el) throw new Error("Map target not found");

  const map = new maplibregl.Map({
    container: el,
    style: "/style.json",
    center: [0, 0],
    zoom: 1,
  });

  let controlsAdded = false;
  map.on("styledata", () => {
    if (controlsAdded) return;
    controlsAdded = true;
    const style = map.getStyle();
    const controls = style.metadata.controls || [];

    controls.forEach((config) => {
      switch (config.type) {
        case "compass":
          map.addControl(
            new maplibregl.NavigationControl({ showZoom: false }),
            config.position,
          );
          break;
        case "zoom":
          map.addControl(
            new maplibregl.NavigationControl({ showCompass: false }),
            config.position,
          );
          break;
        case "layer":
          map.addControl(new LayerControl(), config.position);
          break;
        case "scale":
          map.addControl(new maplibregl.ScaleControl(), config.position);
          break;
      }
    });

    const layers = style.layers || [];

    layers.forEach((layer) => {
      if (layer.metadata?.popup) {
        map.on(layer.metadata.popup["trigger"], layer.id, (e) => {
          const coordinates = e.features[0].geometry.coordinates.slice();
          const properties = e.features[0].properties;
          // const popup = document.createElement("div");
          new maplibregl.Popup()
            .setLngLat(coordinates)
            .setHTML(renderTemplate(layer.metadata.popup["html"], properties))
            .addTo(map);
        });
        map.on("mouseenter", layer.id, () => {
          map.getCanvas().style.cursor = "pointer";
        });
        map.on("mouseleave", layer.id, () => {
          map.getCanvas().style.cursor = "";
        });
      }
    });
  });

  let state = {
    center: options.center || [0, 0],
    zoom: options.zoom || 1,
  };

  const root = document.createElement("div");
  el.appendChild(root);

  function init() {
    el.dispatchEvent(new CustomEvent("map:ready", { detail: api }));
  }

  const api = {};

  init();
  return api;
}

import l from "maplibre-gl";
class _ {
  constructor() {
  }
  onAdd(s) {
    return this._map = s, this._container = document.createElement("div"), this._container.className = "maplibregl-ctrl maplibregl-ctrl-group", this._container.innerHTML = "<button>L</button>", this._panel = document.createElement("div"), this._panel.className = "maplibregl-ctrl-group maplibregl-ctrl-layer hidden", this._buildLayerList(), this._container.appendChild(this._panel), this._container.addEventListener(
      "click",
      () => this._panel?.classList.toggle("hidden")
    ), this._panel.addEventListener("click", (o) => o.stopPropagation()), this._map?.on("click", () => this._panel?.classList.toggle("hidden")), this._container;
  }
  _buildLayerList() {
    this._map?.getStyle().layers?.forEach((o) => {
      const i = o.id, e = document.createElement("label");
      e.style.display = "flex", e.style.cursor = "pointer";
      const n = document.createElement("input");
      n.type = "checkbox", n.checked = this._map?.getLayoutProperty(i, "visibility") !== "none", n.addEventListener("change", () => {
        this._map?.setLayoutProperty(
          i,
          "visibility",
          n.checked ? "visible" : "none"
        );
      }), e.appendChild(n), e.appendChild(document.createTextNode(" " + i)), this._panel?.appendChild(e);
    });
  }
  onRemove() {
    this._container?.remove(), this._map = void 0;
  }
}
function C(c, s) {
  return c.replace(/{{\s*(\w+)\s*}}/g, (o, i) => s[i] ?? "");
}
function k(c, s = "https://demotiles.maplibre.org/globe.json") {
  const o = typeof c == "string" ? document.querySelector(c) : c;
  if (!o) throw new Error("Map target not found");
  const i = s.startsWith("http") ? new URL(s).origin : window.location.href, e = new l.Map({
    container: o,
    style: s,
    center: [0, 0],
    zoom: 1
  });
  let n, h = !1;
  e.on("styledata", () => {
    if (h) return;
    h = !0, n = e.getStyle(), (n.metadata.controls || []).forEach((t) => {
      switch (t.type) {
        case "compass":
          e.addControl(
            new l.NavigationControl({ showZoom: !1 }),
            t.position
          );
          break;
        case "zoom":
          e.addControl(
            new l.NavigationControl({ showCompass: !1 }),
            t.position
          );
          break;
        case "layer":
          e.addControl(new _(), t.position);
          break;
        case "scale":
          e.addControl(new l.ScaleControl(), t.position);
          break;
      }
    }), (n.layers || []).forEach((t) => {
      const r = t.metadata;
      r?.popup != null && (e.on(
        r.popup.trigger,
        t.id,
        (d) => {
          const u = d.features?.[0]?.geometry, p = d.features?.[0]?.properties, w = u.coordinates.slice();
          new l.Popup().setLngLat(w).setHTML(
            C(r.popup.html, p ?? {})
          ).addTo(e);
        }
      ), e.on("mouseenter", t.id, () => {
        e.getCanvas().style.cursor = "pointer";
      }), e.on("mouseleave", t.id, () => {
        e.getCanvas().style.cursor = "";
      }));
    });
  });
  const y = document.createElement("div");
  o.appendChild(y);
  function g() {
    o.dispatchEvent(new CustomEvent("map:ready"));
  }
  async function L(a, m) {
    const t = e.getLayer(a);
    if (t == null)
      throw new Error(`Layer ${a} doesn't exist.`);
    let r = t.metadata.url;
    if (!r)
      throw new Error(`Layer ${t.id} can't be filtered.`);
    r.startsWith("http") || (r = new URL(r, i).toString());
    const d = e.getSource(t?.source), p = await (await fetch(r, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(m)
    })).json();
    d.setData(p);
  }
  function b(a) {
    e.setLayoutProperty(a, "visibility", "none");
  }
  function f(a) {
    e.setLayoutProperty(a, "visibility", "visible");
  }
  function v(a) {
    return e.getLayer(a)?.metadata;
  }
  return g(), {
    mapInstance: e,
    hideLayer: b,
    showLayer: f,
    setLayerFilters: L,
    getLayerMetadata: v
  };
}
export {
  k as createMap
};

# Présentation

This library aims at simplify a MapLibre style map integration into a website.
The idea behind it is to supply an already configured map based on a [MapLibre Style Spec](https://maplibre.org/maplibre-style-spec/) that can be integrated directly into a <div>.
In addition to the map, an API will be passed so the frontend will be able to interact with the map.

# Usage

```
import { createMap } from 'coordo'
import 'coordo/coordo.css'

const mapApi = createMap('#targetID', '<path-to-map-config-file-or-URL>);
const data = mapApi.getDataForLater('#layerId');
```

# How to Test Changes :

Let's say you made changes on the lib TS in a branch named `feat/my_task`

- Create a new branch in https://github.com/dataforgoodfr/14_Data4Trees.
- Modify `webapp/package.json` :

```diff
- "coordo": "github:dataforgoodfr/Coordonnees#main",
+ "coordo": "github:dataforgoodfr/Coordonnees#feat/my_task",
```

- Run the webapp as mentioned in the Readme.
- Verify that there are no breaking changes in the app.
- If any breaking change that can't be solved in your Coordo branch, [create a new Issue](https://github.com/dataforgoodfr/14_Data4Trees/issues).
- Sync with the Lead Dev

---

## Controls

### Control popup rendering with `setLayerPopup`

The `setLayerPopup` function allows you to attach a popup to a specific map layer. The popup is triggered by user interaction (e.g., click, mouseenter) and its content is dynamically generated using a callback function. This callback can return either a string (HTML) or a DOM element, giving you full control over the popup's appearance and behavior.

#### Usage

- **`layerId`**: The ID of the layer to attach the popup to.
- **`trigger`**: The event type that triggers the popup (e.g., `"click"`, `"mouseenter"`).
- **`renderCallback`**: A function that takes the feature's properties and returns the popup content (as HTML string or DOM element).
- **`popupConfig`** (optional): Configuration for the popup (e.g., `className`, `closeButton`, `anchor`).

#### Examples

<details>
<summary><b>HTML & JavaScript</b></summary>

**Example with HTML string**

```js
const renderPopup = (properties) => {
  return `
    <div class="popup-content">
      <h3>\${properties.name}</h3>
      <p>Value: \${properties.value}</p>
    </div>
  `;
};

mapApiRef.current.setLayerPopup({
  layerId: "my-layer-id",
  trigger: "click",
  renderCallback: renderPopup,
  popupConfig: {
    className: "custom-popup",
    closeButton: true,
    anchor: "bottom",
  },
});
```

**Example with DOM element**

```js
const renderPopup = (properties) => {
  const div = document.createElement("div");
  div.className = "popup-content";
  div.innerHTML = `
    <h3>\${properties.name}</h3>
    <p>Value: \${properties.value}</p>
  `;
  return div;
};

mapApiRef.current.setLayerPopup({
  layerId: "my-layer-id",
  trigger: "click",
  renderCallback: renderPopup,
});
```

</details>

<details>
<summary><b>React</b></summary>

```tsx
const renderPopup = (properties: MyDataType) => {
  const container = document.createElement("div");
  const root = createRoot(container);
  root.render(
    <MyReactPopupContent data={properties} onClose={() => root.unmount()} />,
  );
  return container;
};

mapApiRef.current.setLayerPopup<MyDataType>({
  layerId: "my-layer-id",
  trigger: "click",
  renderCallback: renderPopup,
  popupConfig: {
    className: "bg-background/90 rounded-md",
    closeButton: false, // To self-manage the popup closing
    anchor: "center",
  },
});
```

</details>

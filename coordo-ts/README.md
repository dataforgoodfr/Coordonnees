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

---

## Filters

### Filter layer data with `setLayerFilters`

`setLayerFilters` asks the backend for the data of a layer restricted by a filter, then replaces the layer data on the map. The backend applies the filter to the layer's resource **before** it is grouped or aggregated, so each feature is recomputed from the matching rows only (counts, averages, histograms…).

> Filters use the **raw resource column names**, not the aliases defined in the layer `columns`.

Use `setSourceFilter` instead to hide features client-side without a request; the two can be combined.

#### With a `where` object

Conditions are keyed by property and ANDed together. Each condition has exactly one operator. An `undefined` condition is skipped.

```ts
await mapApi.setLayerFilters({
  layerId: "enquete",
  where: {
    age: undefined, // no restriction
    coh: { between: ["2022", "2023"] },
    sex: { eq: "2" },
    typ: { in: ["1", "2"] },
  },
});
```

| Operator  | Example                       | Matches                                    |
| --------- | ----------------------------- | ------------------------------------------ |
| `eq`      | `{ eq: "2" }`                 | equal to                                   |
| `neq`     | `{ neq: "0" }`                | different from                             |
| `lt` `lte` `gt` `gte` | `{ gte: 10 }`     | compared to                                |
| `in`      | `{ in: ["1", "2"] }`          | one of the values (`[]` matches nothing)   |
| `between` | `{ between: [2022, 2023] }`   | between both bounds, inclusive             |
| `like`    | `{ like: "Mak%" }`            | pattern, `%` for any characters            |
| `isNull`  | `{ isNull: true }`            | empty (`false`: not empty)                 |

#### With the `cql` builders

For `or`, `not` or nested conditions. `and` and `or` skip `undefined` conditions, and return `undefined` (no restriction) when none is left.

```ts
import { cql } from "coordo";

await mapApi.setLayerFilters({
  filters: cql.and(
    cql.inList("typ", ["1", "2"]),
    cql.or(cql.eq("sex", "2"), cql.not(cql.isNull("coh"))),
  ),
  layerId: "enquete",
});
```

`whereToCql(where)` compiles a `where` object into the same expressions, to compose it further. Any other [CQL2-JSON](https://docs.ogc.org/is/21-065r2/21-065r2.html) filter can be passed as `filters` as is.

#### Type checking

Describe the filterable properties of your layers to get autocompletion and type errors on layer ids, properties and values:

```ts
type Layers = {
  enquete: { coh: string; sex: "1" | "2"; typ: "0" | "1" | "2" };
};

const mapApi = createMap<Layers>("#map", styleUrl);

mapApi.setLayerFilters({ layerId: "enquete", where: { typ: { in: ["3"] } } });
//                                                                  ^ type error
```

`createCql<Layers["enquete"]>()` returns the same builders, typed for one layer.

#### Clearing, errors and overlapping calls

- `clearLayerFilters(layerId)` restores the unfiltered data.
- The returned promise resolves once the new data is on the map.
- A filter on a property the layer's resource doesn't have is rejected before any request, with the list of available properties.
- When the backend answers with an error, the promise rejects and the current data is kept.
- A newer call for the same layer aborts the previous one, whose promise rejects with an `AbortError`:

```ts
try {
  await mapApi.setLayerFilters({ layerId: "enquete", where });
} catch (error) {
  if (error instanceof DOMException && error.name === "AbortError") return;
  throw error;
}
```

### Tests

```sh
npm test
```

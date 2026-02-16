# Overview

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

# Development

## Commandes

- `npm run build` : package l'application pour la mise en production (dossier [dist](./dist))
- `npm run check:code` : Applique les 3 commandes de vérification de code: Linter, TS Compiler, Formatter.
- `npm run compile` : Vérifie que TypeScript compile correctement
- `npm run format` : Applique le formattage de prettier à l'ensemble du projet
- `npm run format:check` : Détermine les fichiers où le formattage de prettier aurait des effets (fichiers non formattés correctement)
- `npm run lint` : Vérifie que le code ./src respecte les règles de Lint
- `npm run lint:fix` : Fix si possible les problèmes de Linter dans ./src

## Test your changes

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

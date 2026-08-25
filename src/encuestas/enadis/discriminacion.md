# Discriminación vivida

```js
import {dashboardTema} from "../../components/tablero.js";
const indicadores = await FileAttachment("../../data/indicadores.csv").csv({typed: true});
const geoEntidades = await FileAttachment("../../data/mx_entidades.json").json();
```

```js
display(dashboardTema("discriminacion", indicadores, {geoEntidades}));
```

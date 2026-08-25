# Jefatura del hogar

```js
import {dashboardTema} from "../../components/tablero.js";
const indicadores = await FileAttachment("../../data/indicadores.csv").csv({typed: true});
const indicadoresTipoDisc = await FileAttachment("../../data/indicadores_tipo_disc.csv").csv({typed: true});
const geoEntidades = await FileAttachment("../../data/mx_entidades.json").json();
```

```js
display(dashboardTema("hogar", indicadores, {geoEntidades, datosTipoDisc: indicadoresTipoDisc}));
```

# Numeralia

```js
import {dashboardTema} from "../../components/tablero.js";
const indicadores = await FileAttachment("../../data/principal/censo.csv").csv({typed: true});
const indicadoresTipoDisc = await FileAttachment("../../data/tipo_disc/distribucion.csv").csv({typed: true});
const geoEntidades = await FileAttachment("../../data/mx_entidades.json").json();
```

```js
display(dashboardTema("numeralia-censo", indicadores, {geoEntidades, datosTipoDisc: indicadoresTipoDisc}));
```

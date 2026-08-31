# Trabajo e ingreso

```js
import {dashboardTema} from "../../components/tablero.js";
const indicadores = await FileAttachment("../../data/principal/enigh.csv").csv({typed: true});
const indicadoresTipoDisc = await FileAttachment("../../data/tipo_disc/trabajo.csv").csv({typed: true});
const indicadoresDecil = await FileAttachment("../../data/decil/trabajo.csv").csv({typed: true});
const geoEntidades = await FileAttachment("../../data/mx_entidades.json").json();
```

```js
display(dashboardTema("trabajo", indicadores, {geoEntidades, datosTipoDisc: indicadoresTipoDisc, datosDecil: indicadoresDecil}));
```

# Quién ejerce la violencia

<p class="seccion-intro">
Cada ámbito tiene su propio denominador: la violencia laboral se calcula solo
entre quienes trabajaron, y la escolar solo entre quienes asistieron a la
escuela en los últimos doce meses. Quien no está expuesta a un ámbito queda
fuera del cálculo, no contada como "sin violencia". Los porcentajes de una
misma lista no suman el total del ámbito: una mujer agredida por su padre y
por su hermano aparece en ambas barras. El desglose por edad no es opcional
aquí: sin él, algunas cifras se invierten.
</p>

```js
import {dashboardTema} from "../../components/tablero.js";
const indicadores = await FileAttachment("../../data/indicadores.csv").csv({typed: true});
const indicadoresTipoDisc = await FileAttachment("../../data/indicadores_tipo_disc.csv").csv({typed: true});
const geoEntidades = await FileAttachment("../../data/mx_entidades.json").json();
```

```js
display(dashboardTema("agresor", indicadores, {geoEntidades, datosTipoDisc: indicadoresTipoDisc}));
```

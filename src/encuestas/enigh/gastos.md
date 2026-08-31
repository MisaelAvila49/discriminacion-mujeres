# Gastos por discapacidad

<p class="seccion-intro">
El gasto se registra en la ENIGH a nivel HOGAR, no persona: la encuesta anota
que el hogar hizo el gasto, no qué integrante lo hizo. Cada cifra de esta
página hereda esa marca de hogar a cada persona que vive ahí, y se lee como
"personas que viven en un hogar que gasta en X", agrupadas por su propio sexo
y discapacidad. Los montos incluyen el gasto no monetario —lo que pagó otra
persona, el trabajo o un programa— porque también es parte del costo de vivir
con discapacidad. Solo hay tabla de gastos para 2022 y 2024.
</p>

```js
import {dashboardTema} from "../../components/tablero.js";
const indicadores = await FileAttachment("../../data/indicadores.csv").csv({typed: true});
const indicadoresTipoDisc = await FileAttachment("../../data/indicadores_tipo_disc.csv").csv({typed: true});
const indicadoresDecil = await FileAttachment("../../data/indicadores_decil.csv").csv({typed: true});
const geoEntidades = await FileAttachment("../../data/mx_entidades.json").json();
```

```js
display(dashboardTema("gastos", indicadores, {geoEntidades, datosTipoDisc: indicadoresTipoDisc, datosDecil: indicadoresDecil}));
```

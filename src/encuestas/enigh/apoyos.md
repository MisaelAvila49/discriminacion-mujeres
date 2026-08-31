# Apoyos y transferencias

<p class="seccion-intro">
La beca y la pensión se registran en la ENIGH a nivel HOGAR, no persona: la
encuesta anota que el hogar recibe el ingreso, no qué integrante específico.
Cada cifra de esta página hereda esa marca de hogar a cada persona que vive
ahí, y se lee como "personas que viven en un hogar que recibe X", agrupadas
por su propio sexo y discapacidad — no como "personas con discapacidad que
reciben SU beca". Lo que sale del bolsillo del hogar (aparatos, cuidados,
educación especial, transporte) está en la sección de Gastos.
</p>

```js
import {dashboardTema} from "../../components/tablero.js";
const indicadores = await FileAttachment("../../data/indicadores.csv").csv({typed: true});
const indicadoresTipoDisc = await FileAttachment("../../data/indicadores_tipo_disc.csv").csv({typed: true});
const indicadoresDecil = await FileAttachment("../../data/indicadores_decil.csv").csv({typed: true});
const geoEntidades = await FileAttachment("../../data/mx_entidades.json").json();
```

```js
display(dashboardTema("apoyos", indicadores, {geoEntidades, datosTipoDisc: indicadoresTipoDisc, datosDecil: indicadoresDecil}));
```

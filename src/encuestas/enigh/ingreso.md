# Ingreso y apoyos

<p class="seccion-intro">
El ingreso se registra en la ENIGH a nivel HOGAR salvo cuando se indica lo
contrario: la encuesta anota que el hogar percibe cierto ingreso, no qué
integrante lo aporta. Las cifras de hogar heredan esa marca a cada persona que
vive ahí y se leen como "personas que viven en un hogar que recibe X". Dos
indicadores sí son individuales, porque la encuesta registra el ingreso por
renglón de persona: el ingreso propio y cuánto aporta cada quien al hogar. Los
montos van en pesos constantes.
</p>

```js
import {dashboardTema} from "../../components/tablero.js";
const indicadores = await FileAttachment("../../data/principal/enigh.csv").csv({typed: true});
const indicadoresTipoDisc = await FileAttachment("../../data/tipo_disc/ingreso.csv").csv({typed: true});
const indicadoresDecil = await FileAttachment("../../data/decil/ingreso.csv").csv({typed: true});
const geoEntidades = await FileAttachment("../../data/mx_entidades.json").json();
```

```js
display(dashboardTema("ingreso", indicadores, {geoEntidades, datosTipoDisc: indicadoresTipoDisc, datosDecil: indicadoresDecil}));
```

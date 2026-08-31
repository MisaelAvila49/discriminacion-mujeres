# Tecnología y conectividad

<p class="seccion-intro">
Los cuatro indicadores de esta página (conexión a internet, celular,
teléfono fijo, televisión de paga) son de HOGAR, no de persona: la ENIGH
pregunta si el hogar tiene el servicio o aparato, no cuál integrante lo usa
ni si específicamente lo usa la persona con discapacidad. Se revisó la
tabla completa de población de la ENIGH buscando una variable de uso
personal de celular o internet, y no existe — el cuestionario no la
pregunta. La cifra se lee como "hogares con integrante con discapacidad que
tienen acceso a X", no como "personas con discapacidad que usan X".
</p>

```js
import {dashboardTema} from "../../components/tablero.js";
const indicadores = await FileAttachment("../../data/principal/enigh.csv").csv({typed: true});
const indicadoresTipoDisc = await FileAttachment("../../data/tipo_disc/tecnologia.csv").csv({typed: true});
const geoEntidades = await FileAttachment("../../data/mx_entidades.json").json();
```

```js
display(dashboardTema("tecnologia", indicadores, {geoEntidades, datosTipoDisc: indicadoresTipoDisc}));
```

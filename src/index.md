# Distribución de la población

<p class="subtitulo-portada">
Cuántas personas hay en cada grupo del tablero: mujeres y hombres, con y sin
discapacidad, por rango de edad y entidad.
</p>

```js
import {kpis, formatear, barrasComparadas, mapaEntidades} from "./components/graficas.js";
import {prepararSeries} from "./components/filtros.js";
import {ORDEN_EDAD} from "./components/comparacion.js";
import * as Plot from "npm:@observablehq/plot";
import {resize} from "observablehq:stdlib";
const indicadores = await FileAttachment("./data/indicadores.csv").csv({typed: true});
const geoEntidades = await FileAttachment("./data/mx_entidades.json").json();
```

```js
// Todo en esta página sale del tema "distribucion", que a diferencia del resto
// del tablero emite conteos de población en vez de tasas.
const anio = d3.max(indicadores.filter((d) => d.tema === "distribucion"), (d) => d.anio);
const pobl = indicadores.filter(
  (d) => d.tema === "distribucion" && d.indicador === "Población" && d.anio === anio
);
const prev = indicadores.filter(
  (d) => d.tema === "distribucion" &&
         d.indicador === "Prevalencia de discapacidad" && d.anio === anio
);

// Población por grupo, sumando todas las entidades y edades.
const porGrupo = d3.rollups(pobl, (v) => d3.sum(v, (d) => d.num),
                            (d) => d.sexo, (d) => d.disc);
const grupo = new Map();
for (const [sexo, xs] of porGrupo) for (const [disc, n] of xs) grupo.set(`${sexo}|${disc}`, n);

const total = d3.sum([...grupo.values()]);
const conDisc = (grupo.get("Mujeres|Con discapacidad") ?? 0) +
                (grupo.get("Hombres|Con discapacidad") ?? 0);
const mujeresCD = grupo.get("Mujeres|Con discapacidad") ?? 0;

const millones = (n) => (n / 1e6).toFixed(2) + " M";
```

```js
display(kpis([
  {
    etiqueta: `Personas con discapacidad · ${anio}`,
    cifra: millones(conDisc),
    nota: `${(conDisc / total * 100).toFixed(1)}% de la población de 18 años o más`,
  },
  {
    etiqueta: "Son mujeres",
    cifra: `${(mujeresCD / conDisc * 100).toFixed(1)}%`,
    nota: `${millones(mujeresCD)} de mujeres con discapacidad`,
  },
  {
    etiqueta: "Población adulta total",
    cifra: millones(total),
    nota: "Personas de 18 años o más",
  },
]));
```

<span class="kicker">01 · Los cuatro grupos</span>

Todo el tablero compara estos cuatro grupos. Las barras muestran de qué tamaño
es cada uno: las personas con discapacidad son una minoría de la población
adulta, y por eso sus cifras se leen siempre como proporción de su propio
grupo y nunca como parte del total.

```js
const datosGrupos = [...grupo.entries()]
  .map(([k, n]) => {
    const [sexo, disc] = k.split("|");
    return {serie: `${sexo} ${disc === "Con discapacidad" ? "con" : "sin"} discapacidad`,
            sexo, disc, pct: n / 1e6, casos: null, fragil: false};
  })
  .sort((a, b) => b.pct - a.pct);

display(resize((width) => Plot.plot({
  width,
  height: 260,
  style: {fontSize: "13px"},
  marginLeft: 190,
  marginRight: 60,
  x: {label: "millones de personas", grid: true},
  y: {label: null, domain: datosGrupos.map((d) => d.serie)},
  marks: [
    Plot.ruleX([0], {stroke: "#e2e8f0"}),
    Plot.barX(datosGrupos, {
      x: "pct", y: "serie",
      fill: (d) => d.sexo === "Mujeres" ? "#E8930C" : "#2166AC",
      fillOpacity: (d) => d.disc === "Con discapacidad" ? 0.95 : 0.55,
      insetTop: 1, insetBottom: 1,
      channels: {"Población": (d) => (d.pct * 1e6).toLocaleString("es-MX", {maximumFractionDigits: 0})},
      tip: {format: {x: false, y: false, fill: false, fillOpacity: false}},
    }),
    Plot.text(datosGrupos, {
      x: "pct", y: "serie", text: (d) => `${d.pct.toFixed(2)} M`,
      textAnchor: "start", dx: 5, fontSize: 12.5,
    }),
  ],
})));
```

<span class="kicker">02 · La discapacidad crece con la edad</span>

Esta es la cifra que explica buena parte del tablero. La prevalencia de
discapacidad se multiplica por diez entre las personas de 18 a 29 años y las de
60 y más. Cualquier comparación que mezcle edades arrastra ese efecto: los
grupos con discapacidad son, en promedio, mucho mayores que los grupos sin
discapacidad, y eso basta para invertir el signo de algunos indicadores.

```js
const datosPrev = ORDEN_EDAD.flatMap((edad) =>
  ["Mujeres", "Hombres"].map((sexo) => {
    const f = prev.filter((d) => d.rango_edad === edad && d.sexo === sexo);
    const num = d3.sum(f, (d) => d.num), den = d3.sum(f, (d) => d.den);
    return {rango_edad: edad, serie: sexo, pct: den ? num / den * 100 : null,
            num, den, casos: d3.sum(f, (d) => d.casos), fragil: false};
  })
);

display(resize((width) => barrasComparadas(datosPrev, {
  dim: "rango_edad", dimLabel: "Rango de edad", comparacion: "sexo",
  titulo: `Prevalencia de discapacidad por edad · ${anio}`,
  fuente: "ENIGH (INEGI)", formato: "pct", width,
})));
```

<span class="kicker">03 · Dónde vive la población con discapacidad</span>

```js
const porEnt = d3.rollups(
  pobl.filter((d) => d.disc === "Con discapacidad"),
  (v) => d3.sum(v, (d) => d.num), (d) => d.entidad
);
const totalEnt = d3.rollups(pobl, (v) => d3.sum(v, (d) => d.num), (d) => d.entidad);
const totalPorEnt = new Map(totalEnt);
const valores = new Map(porEnt.map(([ent, n]) => [ent, n / totalPorEnt.get(ent) * 100]));
// Población: personas con discapacidad por entidad (el numerador), no el
// total de adultos — es la cuenta real detrás del porcentaje de prevalencia.
const poblacionPorEnt = new Map(porEnt);

display(resize((width) => mapaEntidades(geoEntidades, valores, {
  titulo: `Porcentaje de población adulta con discapacidad · ${anio}`,
  fuente: "ENIGH (INEGI)",
  formato: "pct", etiquetaValor: "Prevalencia",
  poblacion: poblacionPorEnt, width,
})));
```

<div class="nota-portada">

**Sobre estas cifras.** Provienen de la ENIGH ${anio} y están expandidas con el
factor de la encuesta. La condición de discapacidad se define como declarar que
no se puede hacer o se tiene mucha dificultad para al menos una de ocho
actividades básicas; la categoría intermedia de "poca dificultad" queda fuera,
siguiendo el criterio del INEGI. Los detalles están en
[Definiciones](/metodologia/definiciones).

</div>

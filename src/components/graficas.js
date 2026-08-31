// src/components/graficas.js
// Librería de gráficas del tablero. Todas las especificaciones de Observable
// Plot viven aquí; las páginas no llaman a Plot directamente.
//
// Tres reglas transversales:
//   1. Cada barra lleva su valor escrito al final. El naranja de las mujeres
//      no alcanza contraste 3:1 contra el fondo claro, y la etiqueta directa
//      es el relevo obligatorio (validador de dataviz).
//   2. Las celdas con muestra insuficiente se dibujan, pero con textura de
//      rayas y un asterisco. Se muestran porque ocultarlas deja huecos que se
//      leen como ceros; se marcan porque la cifra no es confiable.
//   3. Con dos o más series siempre hay leyenda. La identidad nunca depende
//      solo del color: va también en la etiqueta y en la textura.

import * as Plot from "npm:@observablehq/plot";
import {html} from "npm:htl";
import {COMPARACION_POR_CLAVE, escalaColor, ROJO, ORDEN_EDAD} from "./comparacion.js";
import {MIN_CASOS} from "./agregar.js";

// Envuelve una gráfica para la animación de entrada y el escalonado de barras
// (definido en custom-style.css). Respeta prefers-reduced-motion desde el CSS.
export function animar(nodo) {
  const cont = document.createElement("div");
  cont.className = "grafica-anim";
  cont.appendChild(nodo);
  requestAnimationFrame(() => {
    cont.querySelectorAll('svg g[aria-label="bar"] rect').forEach((barra, i) => {
      barra.style.animationDelay = `${(i % 40) * 12}ms`;
    });
  });
  return cont;
}

// Patrón de rayas para las celdas de muestra insuficiente. Se inyecta una sola
// vez por documento y se referencia por id desde el fill de las barras.
const ID_TRAMA = "trama-fragil";
function asegurarTrama() {
  if (typeof document === "undefined") return;
  if (document.getElementById(ID_TRAMA)) return;
  const svg = html`<svg width="0" height="0" style="position:absolute"
    aria-hidden="true"><defs>
    <pattern id="${ID_TRAMA}" width="6" height="6" patternUnits="userSpaceOnUse"
             patternTransform="rotate(45)">
      <rect width="6" height="6" fill="currentColor" opacity="0.25"></rect>
      <line x1="0" y1="0" x2="0" y2="6" stroke="currentColor" stroke-width="3"></line>
    </pattern></defs></svg>`;
  document.body.appendChild(svg);
}

// Formato de valor según el tipo de indicador. El tablero mezcla porcentajes
// con pesos (ingreso laboral), y un "%" pegado a un ingreso mensual sería un
// error de lectura grave.
export function formatear(valor, formato = "pct") {
  if (valor == null || !isFinite(valor)) return "s/d";
  if (formato === "pesos") {
    return "$" + Math.round(valor).toLocaleString("es-MX");
  }
  if (formato === "horas") return `${valor.toFixed(1)} h`;
  if (formato === "conteo") return Math.round(valor).toLocaleString("es-MX");
  return `${valor.toFixed(1)}%`;
}

// --- Escala tipográfica de las gráficas -------------------------------------
// Un solo lugar donde vive el tamaño del texto de TODAS las gráficas. Antes
// cada una traía su propio número (11, 11.5, 12, 12.5) y el tablero se veía
// disparejo según qué gráfica tocara.
//
// Plot fija 10px por omisión para los ejes, que en una tarjeta de tablero
// queda por debajo del mínimo cómodo de lectura. Se sube desde `style` porque
// Plot no expone el tamaño de los ejes como opción.
export const TIPO = {
  // Ejes, rótulos de faceta y leyendas.
  ejes: 13,
  // Valor escrito sobre cada barra, celda o punto.
  valor: 12.5,
};

const ESTILO_EJES = {fontSize: `${TIPO.ejes}px`};

// Nombre de la medida, para tooltips, encabezados y leyendas.
function etiquetaMedida(formato) {
  if (formato === "pesos") return "Ingreso";
  if (formato === "horas") return "Horas";
  if (formato === "conteo") return "Personas";
  return "Porcentaje";
}

function ejeValor(formato) {
  if (formato === "pesos") {
    return {label: "pesos", grid: true,
            tickFormat: (d) => d >= 1000 ? "$" + (d / 1000).toFixed(0) + "k"
                                         : "$" + d};
  }
  if (formato === "horas") {
    return {label: "horas a la semana", grid: true,
            tickFormat: (d) => `${d} h`};
  }
  if (formato === "conteo") {
    return {label: "personas", grid: true,
            tickFormat: (d) => d.toLocaleString("es-MX")};
  }
  return {label: "%", grid: true, tickFormat: (d) => `${d}%`};
}

// Etiqueta directa al final de la barra. Marca con asterisco las celdas
// frágiles para que la advertencia viaje pegada al número, no solo en el aviso
// general de la página.
function textoBarra(formato) {
  return (d) => formatear(d.pct, formato) + (d.fragil ? " *" : "");
}

// Cuánta gente (ya expandida por el factor) respalda la barra. `num` es la
// cuenta de personas que cumplen la condición — el número real detrás del
// porcentaje —, así que es la única cifra de población que va en el tooltip;
// se omite en pesos/horas, donde `num` es masa de dinero o de tiempo, no
// gente. La tabla de respaldo (`tablaDatos`) trae el detalle completo,
// incluidos los casos de muestra sin expandir; el tooltip se queda corto a
// propósito para no repetir ahí la misma explicación.
function fmtPoblacion(v) {
  return v == null || !isFinite(v) ? "s/d" : Math.round(v).toLocaleString("es-MX");
}
function fmtPoblacionCorta(v) {
  if (v == null || !isFinite(v)) return "s/d";
  const abs = Math.abs(v);
  if (abs >= 1e6) return (v / 1e6).toFixed(2) + " M";
  if (abs >= 1e3) return (v / 1e3).toFixed(2) + " mil";
  return Math.round(v).toLocaleString("es-MX");
}
function canalesPoblacion(formato) {
  return formato === "pct" ? {"Población": (d) => fmtPoblacionCorta(d.num)} : {};
}

// Canales del tooltip: la dimensión, el grupo, el valor y la población que
// hay detrás. Deliberadamente corto — el detalle completo (casos de muestra
// incluidos) vive en la tabla de respaldo, no aquí.
function canales(formato, dimLabel) {
  return {
    [dimLabel]: (d) => d[dimLabel === "Entidad" ? "entidad" : "rango_edad"],
    "Grupo": (d) => d.serie,
    [etiquetaMedida(formato)]: (d) => formatear(d.pct, formato),
    ...canalesPoblacion(formato),
  };
}

// --- Comparación principal --------------------------------------------------
// Barras agrupadas: una barra por serie de la comparación activa, agrupadas por
// la dimensión que se pase (rango de edad, año o entidad).
//
// datos: filas con {serie, pct, casos, fragil, [dim]}
// Rejilla de pequeños múltiplos. `facetaCol` va en columnas (el año, que se
// lee de izquierda a derecha como el tiempo) y `facetaFila` en filas (la
// edad). Cualquiera de las dos puede ser null; sin ninguna, es una sola
// gráfica con las series en el eje x.
//
// Los ejes son compartidos entre paneles a propósito: son pequeños múltiplos,
// y su valor está en que todos los paneles se midan con la misma regla.
export function barrasComparadas(datos, {dim = null, dimLabel = "", comparacion,
    titulo = "", subtitulo = "", fuente = "", formato = "pct",
    dominioDim = null, facetaCol = null, facetaFila = null,
    width = undefined} = {}) {
  asegurarTrama();
  const color = escalaColor(comparacion);

  // Las barras SIEMPRE se posicionan por serie en el eje x. Cuando además hay
  // una dimensión (por ejemplo el rango de edad), esa dimensión va en `fx`,
  // que crea un grupo por valor y coloca las series lado a lado dentro de
  // cada grupo.
  //
  // Poner la dimensión en `x` y dejar que las series compartieran posición
  // hacía que Plot las apilara: en 2020, el grupo de 30 a 44 años mostraba
  // una barra de 153.8%, que es la suma de mujeres (62.2%) y hombres (91.5%).
  // Dos marcas en la misma coordenada x se apilan por omisión.
  const agrupaPorDim = Boolean(dim) && dim !== "serie";
  const hayFacetas = Boolean(facetaCol || facetaFila);

  const dominioFila = facetaFila === "rango_edad"
    ? ORDEN_EDAD.filter((r) => datos.some((d) => d.rango_edad === r))
    : null;

  // Con muchos paneles, la etiqueta encima de cada barra se encima. En ese
  // caso se apaga y la lectura fina queda en el tooltip y en la tabla.
  const nPaneles = (facetaCol ? new Set(datos.map((d) => d[facetaCol])).size : 1) *
                   (facetaFila ? new Set(datos.map((d) => d[facetaFila])).size : 1);
  const etiquetasVisibles = nPaneles <= 4;

  // Cuando la dimensión agrupa, `fx` la ocupa y las series se separan dentro
  // de cada grupo por el eje x. `fx` no puede usarse a la vez para agrupar y
  // para facetar, así que ambos modos son excluyentes; la geometría del
  // tablero nunca los pide juntos.
  const posicion = agrupaPorDim
    ? {fx: dim, x: "serie"}
    : {x: "serie"};

  const marcas = [
    Plot.ruleY([0], {stroke: "#e2e8f0"}),
    Plot.barY(datos, {
      ...posicion, y: "pct", fill: "serie",
      // Hueco de superficie entre barras vecinas: es lo que deja leerlas
      // como dos objetos distintos y no como un bloque.
      insetLeft: 1, insetRight: 1,
      fillOpacity: 0.9,
      channels: canales(formato, dimLabel || "Entidad"),
      tip: {format: {fx: false, fy: false, x: false, y: false, fill: false}},
    }),
    // Encima de las frágiles, la trama de rayas.
    Plot.barY(datos.filter((d) => d.fragil), {
      ...posicion, y: "pct", fill: `url(#${ID_TRAMA})`,
      insetLeft: 1, insetRight: 1,
    }),
    // Contorno bajo el puntero: Plot.pointerX porque `x` (la serie) es SIEMPRE
    // la dimensión categórica que separa una barra de otra, sin importar si
    // además hay agrupamiento por fx o facetas. Plot.pointer a secas (sin
    // eje fijo) empareja por distancia a la punta de la barra y puede
    // resaltar la barra vecina en vez de la que está bajo el cursor.
    Plot.barY(datos, Plot.pointerX({
      ...posicion, y: "pct", fill: "none", stroke: "#1D1D1B", strokeWidth: 1.8,
      insetLeft: 1, insetRight: 1, pointerEvents: "none",
      maxRadius: Infinity,
    })),
  ];
  if (etiquetasVisibles) {
    marcas.push(Plot.text(datos, {
      ...posicion, y: "pct", text: textoBarra(formato),
      dy: -7, fontSize: TIPO.valor, fill: "var(--theme-foreground)",
    }));
  }

  // Techo del eje: deja aire arriba de la barra más alta para que su etiqueta
  // no se corte contra el borde. Sin esto, el valor de la barra máxima queda
  // recortado a la mitad.
  const maxV = Math.max(...datos.map((d) => d.pct ?? 0), 0);
  const techo = formato === "pct" ? Math.min(maxV * 1.12, 100) : maxV * 1.12;

  // Sin `height` explícito, Plot calcula el suyo (crece si la leyenda se
  // envuelve a dos líneas en una tarjeta angosta de grid-cols-2). El CSS del
  // tablero recorta el SVG a max-height: 300px, y como el SVG usa viewBox,
  // recortar una altura MAYOR a la que Plot calculó escala TODO el dibujo
  // hacia abajo — ejes, leyenda y las cifras sobre cada barra se ven
  // diminutos, aunque su fontSize en el código siga siendo el mismo. Fijar
  // aquí la misma altura que ya usa el CSS evita que Plot y el CSS discrepen.
  // Con `facetaFila` sí crece: ahí cada fila es un panel real, no una
  // leyenda envuelta.
  const alturaBase = 300;

  return animar(Plot.plot({
    style: ESTILO_EJES,
    ...(width ? {width} : {}),
    height: facetaFila ? alturaBase + (dominioFila?.length ?? 1) * 90 : alturaBase,
    title: titulo,
    caption: fuente,
    marginBottom: hayFacetas || agrupaPorDim ? 40 : 46,
    marginLeft: 58,
    marginRight: facetaFila ? 76 : 12,
    marginTop: facetaCol ? 20 : 8,
    // El eje x nombra a las series solo cuando ellas son el eje. Al agrupar o
    // facetar, la leyenda ya las identifica y repetirlas en cada grupo es
    // ruido que además no cabe.
    x: (hayFacetas || agrupaPorDim)
      ? {axis: null}
      : {label: dimLabel || null,
         ...(dominioDim ? {domain: dominioDim} : {})},
    ...(agrupaPorDim
      ? {fx: {label: dimLabel || null,
              ...(dominioDim ? {domain: dominioDim} : {})}}
      : facetaCol ? {fx: {label: null}} : {}),
    ...(facetaFila ? {fy: {label: null, ...(dominioFila ? {domain: dominioFila} : {})}} : {}),
    y: {...ejeValor(formato), domain: [0, techo]},
    color,
    marks: marcas,
    ...(hayFacetas
      ? {facet: {data: datos,
                 ...(facetaCol ? {x: facetaCol} : {}),
                 ...(facetaFila ? {y: facetaFila} : {})}}
      : {}),
  }));
}

// --- Serie temporal ---------------------------------------------------------
// Líneas por serie. El eje x son ediciones de encuesta (2017, 2022...), que son
// pocas y discretas: se declara banda para que Plot no las trate como fechas ni
// interpole años que no existen.
export function serieTemporal(datos, {comparacion, titulo = "", subtitulo = "",
    fuente = "", formato = "pct"} = {}) {
  const color = escalaColor(comparacion);
  return animar(Plot.plot({
    style: ESTILO_EJES,
    title: titulo,
    caption: fuente,
    marginLeft: 52,
    marginRight: 12,
    x: {label: "Edición", type: "point", tickFormat: (d) => String(d)},
    y: ejeValor(formato),
    color,
    marks: [
      Plot.ruleY([0], {stroke: "#e2e8f0"}),
      Plot.lineY(datos, {
        x: "anio", y: "pct", stroke: "serie", strokeWidth: 2, marker: "circle",
        channels: {"Grupo": (d) => d.serie,
                   ...canalesPoblacion(formato)},
        tip: {format: {x: true, y: true, stroke: false}},
      }),
      Plot.text(datos, {
        x: "anio", y: "pct", text: textoBarra(formato),
        dy: -10, fontSize: TIPO.valor, fill: "var(--theme-foreground)",
      }),
    ],
  }));
}

// --- Ranking comparado ------------------------------------------------------
// Barras horizontales con las DOS series de la comparación por fila, ordenadas
// por la brecha entre ellas.
//
// Resuelve el caso de muchas categorías con pocos datos cada una: los treinta
// agresores de la ENDIREH como treinta gráficas de dos barras son ilegibles y
// no dejan comparar entre sí. Aquí caben en una sola vista, y el orden por
// brecha pone arriba lo que el tablero busca — qué agresor es más específico
// de la discapacidad, no cuál es más frecuente en general (un hijo violenta a
// menos mujeres que un padre, pero es 3.5 veces más frecuente cuando hay
// discapacidad).
//
// El eje va horizontal porque las etiquetas son frases ("una persona
// desconocida del trabajo"): en vertical se cortan o se giran.
export function rankingComparado(datos, {dim, dimLabel = "", comparacion,
    titulo = "", subtitulo = "", fuente = "", formato = "pct",
    limite = 20, width = undefined} = {}) {
  asegurarTrama();
  const color = escalaColor(comparacion);
  const series = color.domain ?? [];

  // Brecha por categoría: la razón entre la primera y la segunda serie de la
  // comparación. Se usa razón y no diferencia de puntos porque estas tasas son
  // pequeñas y muy distintas entre sí — dos puntos de diferencia no significan
  // lo mismo sobre una base de 0.5% que sobre una de 20%.
  const porDim = new Map();
  for (const d of datos) {
    if (!porDim.has(d[dim])) porDim.set(d[dim], {});
    porDim.get(d[dim])[d.serie] = d.pct;
  }
  const brechaDe = (k) => {
    const v = porDim.get(k) ?? {};
    const a = v[series[0]], b = v[series[1]];
    if (!(a > 0) || !(b > 0)) return -Infinity;
    return a / b;
  };

  const categorias = [...porDim.keys()]
    .sort((a, b) => brechaDe(b) - brechaDe(a))
    .slice(0, limite);
  const orden = datos.filter((d) => categorias.includes(d[dim]));

  return animar(Plot.plot({
    style: ESTILO_EJES,
    ...(width ? {width} : {}),
    title: titulo,
    subtitle: subtitulo,
    caption: fuente,
    marginLeft: 210,
    marginRight: 56,
    // Dos barras por categoría más el aire entre grupos. 30px por fila y no
    // 38: con tres rankings apilados (13, 8 y 9 agresores) la diferencia son
    // 240px menos de scroll, y las barras siguen siendo legibles porque cada
    // una lleva su valor escrito al final.
    height: Math.max(240, categorias.length * 30 + 64),
    x: {...ejeValor(formato), label: null},
    y: {label: null, axis: null, domain: series},
    fy: {label: null, domain: categorias},
    color,
    marks: [
      Plot.ruleX([0], {stroke: "#e2e8f0"}),
      Plot.barX(orden, {
        x: "pct", y: "serie", fy: dim, fill: "serie",
        insetTop: 1, insetBottom: 1,
        channels: {
          [dimLabel || "Categoría"]: (d) => d[dim],
          "Grupo": (d) => d.serie,
          [etiquetaMedida(formato)]: (d) => formatear(d.pct, formato),
          ...canalesPoblacion(formato),
        },
        tip: {format: {x: false, y: false, fy: false, fill: false}},
      }),
      Plot.barX(orden.filter((d) => d.fragil), {
        x: "pct", y: "serie", fy: dim, fill: `url(#${ID_TRAMA})`,
        insetTop: 1, insetBottom: 1,
      }),
      Plot.text(orden, {
        x: "pct", y: "serie", fy: dim, text: textoBarra(formato),
        textAnchor: "start", dx: 4, fontSize: TIPO.valor,
        fill: "var(--theme-foreground)",
      }),
      // pointerY y no pointer a secas: la categoría es el eje discreto, y
      // emparejar por distancia a la punta resaltaría la fila equivocada
      // cuando dos barras difieren mucho en longitud.
      Plot.barX(orden, Plot.pointerY({
        x: "pct", y: "serie", fy: dim, fill: "none",
        stroke: "#1D1D1B", strokeWidth: 1.8,
        insetTop: 1, insetBottom: 1, pointerEvents: "none",
        maxRadius: Infinity,
      })),
    ],
  }));
}

// --- Ranking por entidad ----------------------------------------------------
// Barras horizontales ordenadas. Solo tiene sentido con fuentes de
// representatividad estatal o municipal (Censo, ENIGH, ENDIREH); ENADIS no.
export function rankingEntidades(datos, {titulo = "", subtitulo = "",
    fuente = "", formato = "pct", limite = 32, width = undefined} = {}) {
  asegurarTrama();
  const orden = [...datos].sort((a, b) => (b.pct ?? -1) - (a.pct ?? -1))
    .slice(0, limite);
  return animar(Plot.plot({
    style: ESTILO_EJES,
    ...(width ? {width} : {}),
    title: titulo,
    caption: fuente,
    marginLeft: 138,
    marginRight: 52,
    height: Math.max(240, orden.length * 19 + 60),
    x: {...ejeValor(formato), label: null},
    y: {label: null, domain: orden.map((d) => d.entidad)},
    marks: [
      Plot.ruleX([0], {stroke: "#e2e8f0"}),
      Plot.barX(orden, {
        x: "pct", y: "entidad", fill: ROJO, fillOpacity: 0.85,
        // Extremo redondeado del lado del dato.
        insetTop: 1, insetBottom: 1,
        channels: {
          "Porcentaje": (d) => formatear(d.pct, formato),
          ...canalesPoblacion(formato),
        },
        tip: {format: {x: false, y: false, fill: false}},
      }),
      Plot.barX(orden.filter((d) => d.fragil), {
        x: "pct", y: "entidad", fill: `url(#${ID_TRAMA})`,
        insetTop: 1, insetBottom: 1,
      }),
      Plot.text(orden, {
        x: "pct", y: "entidad", text: textoBarra(formato),
        textAnchor: "start", dx: 4, fontSize: TIPO.valor,
        fill: "var(--theme-foreground)",
      }),
      // Plot.pointerY: `y` (la entidad) es la dimensión categórica que separa
      // una fila de otra; Plot.pointer a secas empareja por cercanía a la
      // punta de la barra y puede resaltar la fila equivocada cuando hay
      // barras muy distintas en longitud.
      Plot.barX(orden, Plot.pointerY({
        x: "pct", y: "entidad", fill: "none", stroke: "#1D1D1B", strokeWidth: 1.8,
        insetTop: 1, insetBottom: 1, pointerEvents: "none",
        maxRadius: Infinity,
      })),
    ],
  }));
}

// --- Aviso de muestra insuficiente ------------------------------------------
// Se coloca junto a la gráfica, no en una nota al pie: la advertencia tiene que
// estar donde está el número.
export function avisoMuestra(filas, {umbral = MIN_CASOS} = {}) {
  const fragiles = filas.filter((f) => f.fragil);
  // Ojo: html`` (plantilla vacía) devuelve null, y un null suelto dentro de un
  // arreglo de nodos se pinta como la palabra "null" en la página. Cuando no
  // hay nada que avisar hay que devolver un nodo real y vacío.
  if (!fragiles.length) return document.createDocumentFragment();
  const minimo = Math.min(...fragiles.map((f) => f.casos));
  return html`<p class="aviso-muestra" role="note">
    <strong>Muestra insuficiente.</strong>
    ${fragiles.length === 1
      ? html`Una de las barras se calculó con menos de ${umbral} casos`
      : html`${fragiles.length} de las barras se calcularon con menos de
             ${umbral} casos`}
    (la menor, con ${minimo}). Se dibujan con rayas y un asterisco.
    Con tan pocos casos la cifra puede moverse mucho de una muestra a otra:
    sirve para ver el orden de magnitud, no para comparar diferencias chicas.
  </p>`;
}

// --- Tarjetas de KPI --------------------------------------------------------
// La primera tarjeta es la destacada (borde rojo). Patrón F: los KPI arriba,
// la gráfica principal enseguida.
export function kpis(tarjetas) {
  return html`<div class="kpi-fila">
    ${tarjetas.map((t, i) => html`<div class="kpi-tarjeta ${i === 0 ? "kpi-destacado" : ""}">
      <span class="kpi-etiqueta">${t.etiqueta}</span>
      <span class="kpi-cifra">${t.cifra}</span>
      ${t.nota ? html`<span class="kpi-nota" title=${t.nota}>${t.nota}</span>` : ""}
    </div>`)}
  </div>`;
}

// --- Tabla de respaldo ------------------------------------------------------
// Toda gráfica del tablero tiene su tabla equivalente: es el relevo de
// accesibilidad para el contraste bajo y para quien lee con lector de pantalla.
export function tablaDatos(filas, {dimLabel = "Grupo", dim = "serie",
    formato = "pct"} = {}) {
  return html`<details class="tabla-datos">
    <summary>Ver los datos de esta gráfica</summary>
    <table>
      <thead><tr>
        <th>${dimLabel}</th><th>Grupo</th>
        <th>${etiquetaMedida(formato)}</th>
        ${formato === "pct" ? html`<th>Pob. cumple</th>` : ""}
        <th>Pob. total</th>
        <th>Casos en muestra</th>
      </tr></thead>
      <tbody>
        ${filas.map((f) => html`<tr>
          <td>${f[dim] ?? ""}</td>
          <td>${f.serie ?? ""}</td>
          <td>${formatear(f.pct, formato)}${f.fragil ? " *" : ""}</td>
          ${formato === "pct" ? html`<td>${fmtPoblacion(f.num)}</td>` : ""}
          <td>${fmtPoblacion(f.den)}</td>
          <td>${f.casos?.toLocaleString("es-MX") ?? "s/d"}</td>
        </tr>`)}
      </tbody>
    </table>
  </details>`;
}

// --- Mapa coroplético de entidades ------------------------------------------
// Adaptado del componente de jcf-stats. El geojson identifica cada entidad con
// un código ISO en properties.id; aquí se traduce al nombre oficial, que es la
// llave que usan los data loaders.
export const ISO_A_ENTIDAD = {
  "MX-AGU": "Aguascalientes", "MX-BCN": "Baja California",
  "MX-BCS": "Baja California Sur", "MX-CAM": "Campeche",
  "MX-COA": "Coahuila", "MX-COL": "Colima", "MX-CHP": "Chiapas",
  "MX-CHH": "Chihuahua", "MX-CMX": "Ciudad de México", "MX-DUR": "Durango",
  "MX-GUA": "Guanajuato", "MX-GRO": "Guerrero", "MX-HID": "Hidalgo",
  "MX-JAL": "Jalisco", "MX-MEX": "México", "MX-MIC": "Michoacán",
  "MX-MOR": "Morelos", "MX-NAY": "Nayarit", "MX-NLE": "Nuevo León",
  "MX-OAX": "Oaxaca", "MX-PUE": "Puebla", "MX-QUE": "Querétaro",
  "MX-ROO": "Quintana Roo", "MX-SLP": "San Luis Potosí", "MX-SIN": "Sinaloa",
  "MX-SON": "Sonora", "MX-TAB": "Tabasco", "MX-TAM": "Tamaulipas",
  "MX-TLA": "Tlaxcala", "MX-VER": "Veracruz", "MX-YUC": "Yucatán",
  "MX-ZAC": "Zacatecas",
};

// Dibuja el mapa. `valores` es un Map de nombre de entidad al valor a colorear.
// La escala es secuencial de un solo tono (magnitud), nunca un arcoíris.
export function mapaEntidades(geo, valores, {titulo = "", subtitulo = "",
    fuente = "", formato = "pct", etiquetaValor = "valor",
    poblacion = null, width = undefined, conLeyenda = true, alto = 300} = {}) {
  const feats = geo.features.map((f) => {
    const nombre = ISO_A_ENTIDAD[f.properties.id] ?? f.properties.name;
    return {...f, properties: {...f.properties, nombre,
      valor: valores.get(nombre) ?? null}};
  });

  const canales = {
    "Entidad": (d) => d.properties.nombre,
    [etiquetaValor]: (d) => d.properties.valor == null
      ? "sin dato" : formatear(d.properties.valor, formato),
    // `poblacion` trae la cuenta de personas que cumplen la condición
    // (num), ya expandida — el mismo criterio que en canalesPoblacion().
    ...(poblacion ? {"Población": (d) =>
      fmtPoblacionCorta(poblacion.get(d.properties.nombre))} : {}),
  };

  // Escala fija de 0 a 100 para los porcentajes, con los extremos marcados.
  // Es lo que permite comparar dos mapas entre sí (dos años, dos grupos): con
  // un dominio ajustado a cada conjunto, el mismo tono significaría valores
  // distintos en cada mapa y la comparación visual engañaría.
  const vals = feats.map((f) => f.properties.valor).filter((v) => v != null);
  const dominio = formato === "pct"
    ? [0, 100]
    : (vals.length ? [0, Math.max(...vals)] : [0, 1]);

  return animar(conHoverGeo(Plot.plot({
    style: ESTILO_EJES,
    ...(width ? {width} : {}),
    title: titulo,
    caption: fuente,
    projection: {type: "mercator",
                 domain: {type: "FeatureCollection", features: feats}},
    height: alto,
    color: {
      scheme: "reds", type: "linear", domain: dominio,
      // En una rejilla de mapas la leyenda se dibuja una sola vez arriba: es
      // la misma escala para todos y repetirla come el espacio del mapa.
      legend: conLeyenda, label: etiquetaValor, unknown: "#eee",
      // Los extremos se marcan explícitamente para que la barra de color diga
      // de qué a qué va, en vez de dejar al lector suponer el rango.
      ...(formato === "pct" ? {ticks: [0, 25, 50, 75, 100]} : {}),
      tickFormat: (d) => formatear(d, formato),
    },
    marks: [
      // Sin trazo entre polígonos vecinos: un trazo blanco (aunque sea
      // delgado) antialiasea a gris contra el relleno de color a cualquier
      // grosor. Los polígonos se tocan directo; la separación entre
      // unidades ya la da el cambio de color de relleno.
      Plot.geo(feats, {
        fill: (d) => d.properties.valor,
        stroke: "none",
        channels: canales,
        tip: {channels: canales,
              format: {fill: false, stroke: false, strokeWidth: false}},
      }),
    ],
  })));
}

// Plot.plot con leyenda devuelve un <figure> con DOS <svg>: la rampa de la
// leyenda (aparece primero en el DOM) y el mapa. querySelector("svg") a
// secas agarraba la rampa, y la clase de hover nunca llegaba al mapa real.
// Hay que buscar específicamente el svg que contiene los polígonos.
function conHoverGeo(fig) {
  if (fig?.tagName === "svg") {
    fig.classList.add("mapa-hover");
    return fig;
  }
  const svg = fig?.querySelector?.('svg:has(g[aria-label="geo"])')
    ?? [...(fig?.querySelectorAll?.("svg") ?? [])]
      .find((s) => s.querySelector('g[aria-label="geo"]'));
  if (svg) svg.classList.add("mapa-hover");
  return fig;
}

// --- Heatmap de año por rango de edad ---------------------------------------
// Sustituye a la rejilla de barras cuando se cruzan las dos dimensiones: 12
// paneles de barras ocupan una pantalla entera, y la misma información cabe en
// una cuadrícula que además deja ver el gradiente de un golpe.
//
// Una celda por (año, rango de edad) y una cuadrícula por serie de la
// comparación, para no codificar dos variables en un solo color.
export function heatmapEdadAnio(datos, {comparacion, titulo = "",
    subtitulo = "", fuente = "", formato = "pct", width = undefined} = {}) {
  const comp = COMPARACION_POR_CLAVE[comparacion];
  const series = comp?.series ?? [...new Set(datos.map((d) => d.serie))];
  const anios = [...new Set(datos.map((d) => String(d.anio)))].sort();

  const vals = datos.map((d) => d.pct).filter((v) => v != null);
  // Escala fija de 0 a 100, igual que el mapa: es lo que permite comparar las
  // dos cuadrículas de la comparación entre sí. Con un dominio ajustado a
  // cada una, el mismo rojo significaría cosas distintas en cada cuadrícula.
  const dominio = formato === "pct"
    ? [0, 100]
    : (vals.length ? [0, Math.max(...vals)] : [0, 1]);

  return animar(Plot.plot({
    style: ESTILO_EJES,
    ...(width ? {width} : {}),
    title: titulo,
    caption: fuente,
    marginLeft: 64,
    marginBottom: 40,
    marginTop: 14,
    height: 60 + ORDEN_EDAD.length * 34,
    padding: 0.04,
    x: {label: null, domain: anios, type: "band"},
    y: {label: null, domain: ORDEN_EDAD, type: "band"},
    fx: {label: null, domain: series},
    color: {
      scheme: "reds", type: "linear", domain: dominio,
      legend: true, label: etiquetaMedida(formato),
      ...(formato === "pct" ? {ticks: [0, 25, 50, 75, 100]} : {}),
      tickFormat: (d) => formatear(d, formato),
    },
    marks: [
      Plot.cell(datos, {
        x: (d) => String(d.anio), y: "rango_edad", fx: "serie",
        fill: "pct", inset: 1,
        channels: {
          "Grupo": (d) => d.serie,
          "Año": (d) => String(d.anio),
          "Edad": (d) => d.rango_edad,
          [etiquetaMedida(formato)]: (d) => formatear(d.pct, formato),
          ...canalesPoblacion(formato),
        },
        tip: {format: {x: false, y: false, fx: false, fill: false}},
      }),
      // El valor va escrito en cada celda: es lo que vuelve al heatmap
      // legible sin obligar a estimar el tono contra la leyenda.
      Plot.text(datos, {
        x: (d) => String(d.anio), y: "rango_edad", fx: "serie",
        text: (d) => formatear(d.pct, formato) + (d.fragil ? " *" : ""),
        fontSize: TIPO.valor,
        // Texto claro sobre las celdas oscuras del extremo alto de la escala.
        // El umbral se mide contra el dominio fijo (0-100), no contra el rango
        // de los datos: con la escala fija, una celda de 60% siempre tiene el
        // mismo tono y por lo tanto siempre necesita el mismo color de texto.
        fill: (d) => {
          const [lo, hi] = dominio;
          const t = hi > lo ? ((d.pct ?? 0) - lo) / (hi - lo) : 0;
          return t > 0.6 ? "#fff" : "#1D1D1B";
        },
      }),
      // Ambos ejes (año, rango de edad) son categóricos: Plot.pointer a
      // secas es correcto aquí, sin necesidad de fijar un eje (lección 31
      // de la skill observableframework — heatmaps son la excepción).
      Plot.cell(datos, Plot.pointer({
        x: (d) => String(d.anio), y: "rango_edad", fx: "serie",
        fill: "none", stroke: "#1D1D1B", strokeWidth: 2, inset: 1,
        pointerEvents: "none", maxRadius: Infinity,
      })),
    ],
  }));
}

// --- Rejilla de mapas (small multiples geográficos) -------------------------
// Un mapa por combinación de las dimensiones activas, todos con la MISMA
// escala de color (0-100), que es lo que permite compararlos entre sí. Con
// escalas independientes el mismo rojo significaría cosas distintas en cada
// panel y la comparación visual engañaría.
//
// `grupos` es un arreglo de {etiqueta, valores, poblacion}: un panel por
// elemento. `poblacion` es opcional.
export function mapasMultiples(geo, grupos, {titulo = "", fuente = "",
    formato = "pct", etiquetaValor = "valor", width = undefined} = {}) {
  const anchoPanel = width
    ? Math.max(190, Math.floor(width / Math.min(grupos.length, 2)) - 12)
    : 300;

  const paneles = grupos.map(({etiqueta, valores, poblacion}) =>
    html`<figure class="mapa-panel">
      <figcaption class="mapa-panel-titulo">${etiqueta}</figcaption>
      ${mapaEntidades(geo, valores, {
        formato, etiquetaValor, poblacion,
        width: anchoPanel,
        // La leyenda se dibuja una sola vez para toda la rejilla: repetirla
        // en cada panel gasta el espacio que necesitan los mapas.
        conLeyenda: false,
      })}
    </figure>`);

  return html`<div class="mapas-multiples">
    ${titulo ? html`<h2 class="mapas-titulo">${titulo}</h2>` : ""}
    ${leyendaEscala({formato, etiquetaValor})}
    <div class="mapas-rejilla" style="--mapa-min: ${anchoPanel}px">${paneles}</div>
    ${fuente ? html`<figcaption class="mapas-fuente">${fuente}</figcaption>` : ""}
  </div>`;
}

// Leyenda de color independiente, para encabezar una rejilla de mapas que
// comparten escala.
export function leyendaEscala({formato = "pct", etiquetaValor = "valor"} = {}) {
  const dominio = formato === "pct" ? [0, 100] : null;
  if (!dominio) return document.createDocumentFragment();
  return Plot.legend({
    color: {
      scheme: "reds", type: "linear", domain: dominio,
      label: etiquetaValor,
      ticks: [0, 25, 50, 75, 100],
      tickFormat: (d) => formatear(d, formato),
    },
    width: 260,
    style: {fontSize: `${TIPO.ejes}px`},
  });
}

// --- Barras por entidad, con las series comparadas --------------------------
// Barras verticales a lo largo del ancho: una entidad por posición, y dentro
// de cada una las dos series de la comparación lado a lado. Es la vista que
// permite leer la brecha entidad por entidad, cosa que un mapa por serie no
// deja hacer (obliga a saltar de un mapa a otro).
//
// Las entidades se ordenan por la brecha, no alfabéticamente: el orden es lo
// que convierte la gráfica en un hallazgo en vez de una lista.
export function barrasPorEntidad(datos, {comparacion, titulo = "",
    fuente = "", formato = "pct", width = undefined, ordenarPor = "brecha"} = {}) {
  asegurarTrama();
  const color = escalaColor(comparacion);
  const comp = COMPARACION_POR_CLAVE[comparacion];
  const series = comp?.series ?? [...new Set(datos.map((d) => d.serie))];

  // Orden de las entidades: por la diferencia entre la primera y la segunda
  // serie, de mayor a menor.
  const porEnt = new Map();
  for (const d of datos) {
    const a = porEnt.get(d.entidad) ?? {};
    a[d.serie] = d.pct;
    porEnt.set(d.entidad, a);
  }
  const orden = [...porEnt.entries()]
    .map(([entidad, v]) => ({
      entidad,
      brecha: (v[series[0]] ?? 0) - (v[series[1]] ?? 0),
      total: v[series[0]] ?? 0,
    }))
    .sort((a, b) => ordenarPor === "brecha"
      ? b.brecha - a.brecha
      : b.total - a.total)
    .map((d) => d.entidad);

  const maxV = Math.max(...datos.map((d) => d.pct ?? 0), 0);
  // "pesos" y "conteo" no tienen techo natural en 100 (un ingreso o un
  // conteo de personas pueden ser cualquier magnitud); solo "pct" sí.
  const techo = formato === "pct" ? Math.min(maxV * 1.1, 100) : maxV * 1.1;

  return animar(Plot.plot({
    style: ESTILO_EJES,
    ...(width ? {width} : {}),
    title: titulo,
    caption: fuente,
    marginBottom: 96,
    marginLeft: 58,
    marginTop: 8,
    height: 340,
    // Una banda por entidad; dentro, una barra por serie.
    fx: {domain: orden, label: null, tickRotate: -60},
    x: {axis: null},
    y: {...ejeValor(formato), domain: [0, techo]},
    color,
    marks: [
      Plot.ruleY([0], {stroke: "#e2e8f0"}),
      Plot.barY(datos, {
        fx: "entidad", x: "serie", y: "pct", fill: "serie",
        insetLeft: 0.5, insetRight: 0.5,
        fillOpacity: 0.9,
        channels: {
          "Entidad": (d) => d.entidad,
          "Grupo": (d) => d.serie,
          [etiquetaMedida(formato)]: (d) => formatear(d.pct, formato),
          ...canalesPoblacion(formato),
        },
        tip: {format: {fx: false, x: false, y: false, fill: false}},
      }),
      Plot.barY(datos.filter((d) => d.fragil), {
        fx: "entidad", x: "serie", y: "pct", fill: `url(#${ID_TRAMA})`,
        insetLeft: 0.5, insetRight: 0.5,
      }),
      // Plot.pointerX con fx incluido: sin fx, el emparejamiento por x podría
      // cruzar la banda de una entidad vecina cuando las barras son cortas.
      Plot.barY(datos, Plot.pointerX({
        fx: "entidad", x: "serie", y: "pct", fill: "none",
        stroke: "#1D1D1B", strokeWidth: 1.8,
        insetLeft: 0.5, insetRight: 0.5, pointerEvents: "none",
        maxRadius: Infinity,
      })),
    ],
  }));
}

// --- Heatmap de brecha ------------------------------------------------------
// Matriz de dos dimensiones categóricas (agresor × tipo de violencia) donde el
// color es la RAZÓN entre las dos series de la comparación, no el nivel.
//
// El nivel y la brecha responden preguntas distintas y aquí importa la
// segunda: un padre agrede a más mujeres que un hijo en términos absolutos,
// pero la violencia del hijo es cuatro veces más frecuente cuando hay
// discapacidad. Con color por nivel, esa fila se vería pálida y el hallazgo
// desaparecería.
//
// La escala diverge en 1 (misma frecuencia en ambos grupos) a propósito: por
// debajo de 1 el rojo se apaga hacia el gris, así que una celda intensa
// siempre significa "aquí la desigualdad es mayor", nunca "aquí hay muchos
// casos".
export function heatmapBrecha(celdas, {titulo = "", subtitulo = "",
    fuente = "", filaLabel = "Agresor", colLabel = "Tipo",
    width = undefined} = {}) {
  if (!celdas.length) return html`<p class="nota-indicador">Sin datos.</p>`;
  asegurarTrama();

  // Orden de filas por brecha máxima: en una matriz el orden es la mitad del
  // mensaje, y alfabético no dice nada.
  const peor = new Map();
  for (const d of celdas) {
    const v = peor.get(d.fila) ?? -Infinity;
    if (d.razon != null && isFinite(d.razon)) {
      peor.set(d.fila, Math.max(v, d.razon));
    } else if (!peor.has(d.fila)) {
      peor.set(d.fila, -Infinity);
    }
  }
  const filas = [...peor.entries()].sort((a, b) => b[1] - a[1]).map(([f]) => f);
  const columnas = [...new Set(celdas.map((d) => d.col))];

  const maxRazon = Math.max(
    ...celdas.map((d) => (isFinite(d.razon) ? d.razon : 1)), 2);

  return animar(Plot.plot({
    style: ESTILO_EJES,
    ...(width ? {width} : {}),
    title: titulo,
    subtitle: subtitulo,
    caption: fuente,
    marginLeft: 210,
    marginTop: 34,
    marginBottom: 42,
    height: Math.max(220, filas.length * 30 + 90),
    x: {domain: columnas, label: null, tickSize: 0},
    y: {domain: filas, label: null, tickSize: 0},
    color: {
      type: "linear",
      domain: [1, maxRazon],
      range: ["#f1f5f9", ROJO],
      clamp: true,
      legend: true,
      label: "veces más frecuente con discapacidad",
    },
    marks: [
      Plot.cell(celdas, {
        x: "col", y: "fila", fill: "razon",
        inset: 1.5, rx: 3,
        channels: {
          [filaLabel]: (d) => d.fila,
          [colLabel]: (d) => d.col,
          "Con discapacidad": (d) => formatear(d.a, "pct"),
          "Sin discapacidad": (d) => formatear(d.b, "pct"),
          "Brecha": (d) => isFinite(d.razon) ? `${d.razon.toFixed(2)}x` : "s/d",
        },
        tip: {format: {x: false, y: false, fill: false}},
      }),
      // La razón escrita dentro de la celda: el color por sí solo no permite
      // leer una cifra, y sin el número la matriz solo sirve para ver el
      // patrón, no para citarla.
      Plot.text(celdas, {
        x: "col", y: "fila",
        text: (d) => isFinite(d.razon) ? `${d.razon.toFixed(1)}x` : "",
        fontSize: TIPO.valor,
        // Texto claro sobre celdas oscuras.
        fill: (d) => (isFinite(d.razon) && d.razon > 1 + (maxRazon - 1) * 0.55)
          ? "#fff" : "var(--theme-foreground)",
      }),
      Plot.cell(celdas.filter((d) => d.fragil), {
        x: "col", y: "fila", fill: `url(#${ID_TRAMA})`, inset: 1.5, rx: 3,
      }),
    ],
  }));
}

// --- Heatmap de entidades por corte -----------------------------------------
// Entidades en el eje vertical y cortes (año, edad o ambos) en el horizontal.
// `jerarquia` activa el eje de dos niveles: el año agrupa arriba y el rango de
// edad se lista abajo, en vez de meter "2020 · 18-29" en una sola etiqueta
// que se corta.
export function heatmapEntidades(celdas, {titulo = "", fuente = "",
    formato = "pct", width = undefined, jerarquia = false,
    etiquetaGrupo = "Año", etiquetaSub = "Rango de edad"} = {}) {
  // Orden de las filas por el promedio de la entidad, de mayor a menor: en una
  // matriz el orden es la mitad del mensaje, y alfabético no dice nada.
  const suma = new Map();
  for (const d of celdas) {
    const a = suma.get(d.entidad) ?? {t: 0, n: 0};
    if (d.pct != null) {a.t += d.pct; a.n += 1;}
    suma.set(d.entidad, a);
  }
  const filas = [...suma.entries()]
    .sort((a, b) => (b[1].n ? b[1].t / b[1].n : -1) - (a[1].n ? a[1].t / a[1].n : -1))
    .map(([e]) => e);

  const dominio = formato === "pct"
    ? [0, 100]
    : [0, Math.max(...celdas.map((d) => d.pct ?? 0), 1)];

  const grupos = [...new Set(celdas.map((d) => d.grupo))];
  const subs = [...new Set(celdas.map((d) => d.sub))];

  return animar(Plot.plot({
    style: ESTILO_EJES,
    ...(width ? {width} : {}),
    title: titulo,
    caption: fuente,
    marginLeft: 132,
    marginTop: jerarquia ? 40 : 34,
    marginBottom: jerarquia ? 46 : 10,
    marginRight: 8,
    height: Math.max(340, filas.length * 17 + (jerarquia ? 96 : 60)),
    // Con jerarquía: `fx` es el año (rótulo arriba) y `x` el rango de edad
    // (rótulo abajo). Son dos ejes distintos, así que ninguna etiqueta tiene
    // que apretar dos valores en el mismo espacio.
    ...(jerarquia
      ? {fx: {domain: grupos, label: etiquetaGrupo, axis: "top"},
         x: {domain: subs, type: "band", label: etiquetaSub, axis: "bottom",
             tickRotate: subs.length > 4 ? -35 : 0}}
      : {x: {domain: subs, type: "band", axis: "top", label: null,
             tickRotate: subs.length > 6 ? -35 : 0}}),
    y: {domain: filas, type: "band", label: null},
    color: {
      scheme: "reds", type: "linear", domain: dominio,
      legend: true, label: etiquetaMedida(formato),
      ...(formato === "pct" ? {ticks: [0, 25, 50, 75, 100]} : {}),
      tickFormat: (d) => formatear(d, formato),
    },
    marks: [
      Plot.cell(celdas, {
        ...(jerarquia ? {fx: "grupo"} : {}),
        x: "sub", y: "entidad", fill: "pct", inset: 0.5,
        channels: {
          "Entidad": (d) => d.entidad,
          [etiquetaGrupo]: (d) => d.grupo,
          ...(jerarquia ? {[etiquetaSub]: (d) => d.sub} : {}),
          [etiquetaMedida(formato)]: (d) => formatear(d.pct, formato),
          ...canalesPoblacion(formato),
        },
        tip: {format: {fx: false, x: false, y: false, fill: false}},
      }),
      // Ambos ejes son categóricos (sub, entidad): Plot.pointer a secas.
      Plot.cell(celdas, Plot.pointer({
        ...(jerarquia ? {fx: "grupo"} : {}),
        x: "sub", y: "entidad", fill: "none", stroke: "#1D1D1B",
        strokeWidth: 2, inset: 0.5, pointerEvents: "none", maxRadius: Infinity,
      })),
    ],
  }));
}

// --- Explicación en lenguaje llano ------------------------------------------
// Desplegable que responde "¿qué quiere decir este análisis?" para quien no
// viene de la encuesta. Va cerrado y junto a la tabla de datos: no compite con
// la gráfica, pero está a un clic cuando la cifra no se entiende sola.
export function explicacion(texto) {
  if (!texto) return document.createDocumentFragment();
  return html`<details class="explica-analisis">
    <summary>¿Qué quiere decir este análisis?</summary>
    <p>${texto}</p>
  </details>`;
}

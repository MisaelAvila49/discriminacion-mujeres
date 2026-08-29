// src/components/comparacion.js
// El modelo de comparación del tablero. Todo el sitio gira alrededor de cuatro
// pares fijos; esta es la única definición de cuáles son, qué grupos los
// componen y cómo se colorean. Cambiar aquí cambia todas las páginas.
//
// Cada registro de los data loaders trae dos llaves de identidad:
//   sexo:  "Mujeres" | "Hombres"
//   disc:  "Con discapacidad" | "Sin discapacidad"
// El grupo es la concatenación de ambas. Las comparaciones son subconjuntos
// de esos cuatro grupos.

// --- Paleta -----------------------------------------------------------------
// Los cuatro grupos NO son cuatro categorías independientes: son dos binarios
// cruzados (sexo × discapacidad). Se codifican como 2 tonos × 2 intensidades.
// Cuatro tonos distintos NO pasan el validador de daltonismo en modo oscuro
// (rojo/naranja/verde colisionan para deuteranopía, ΔE 4.5); dos tonos pasan
// con margen amplio (ΔE 24.7 protan en oscuro, 29.6 en claro).
//
// Validado con dataviz/scripts/validate_palette.js --pairs all, ambos modos.
// El tono identifica el SEXO. La discapacidad se codifica con intensidad +
// textura, nunca solo con color.
export const COLOR_SEXO = {
  Mujeres: "#E8930C",  // naranja: evita el estereotipo rosa
  Hombres: "#2166AC",  // azul
};

// Versiones para modo oscuro (escalones propios, no un volteo automático:
// el naranja claro y el rojo de marca se salen de la banda L 0.48-0.67).
export const COLOR_SEXO_OSCURO = {
  Mujeres: "#C97D08",
  Hombres: "#4A90D9",
};

// Rojo de marca del dashboard (kickers, bordes de acento, KPI destacado).
export const ROJO = "#C4101B";

// Orden ordinal de los rangos de edad. Vive aquí, en el módulo base sin
// dependencias, porque lo necesitan tanto las gráficas como los filtros y
// declararlo en cualquiera de los dos crearía un ciclo de importación.
export const ORDEN_EDAD = ["18-29", "30-44", "45-59", "60+"];

// Los cuatro grupos con su color efectivo. "Con discapacidad" usa el tono pleno
// y textura de rayas; "Sin discapacidad" usa el mismo tono aclarado. La
// diferencia de intensidad es secundaria: la textura y la etiqueta directa son
// las que cargan la identidad para quien no distingue el tono.
export const GRUPOS = [
  {clave: "M-CD", sexo: "Mujeres", disc: "Con discapacidad", etiqueta: "Mujeres con discapacidad",  color: "#E8930C", textura: true},
  {clave: "M-SD", sexo: "Mujeres", disc: "Sin discapacidad", etiqueta: "Mujeres sin discapacidad",  color: "#F5C376", textura: false},
  {clave: "H-CD", sexo: "Hombres", disc: "Con discapacidad", etiqueta: "Hombres con discapacidad",  color: "#2166AC", textura: true},
  {clave: "H-SD", sexo: "Hombres", disc: "Sin discapacidad", etiqueta: "Hombres sin discapacidad",  color: "#8FB8DA", textura: false},
];

export const GRUPO_POR_CLAVE = Object.fromEntries(GRUPOS.map((g) => [g.clave, g]));

// --- Las cuatro comparaciones ------------------------------------------------
// `filtra` decide qué grupos entran; `pregunta` es el texto que encabeza la
// página cuando esa comparación está activa.
export const COMPARACIONES = [
  {
    clave: "disc-sexo",
    etiqueta: "Mujeres vs Hombres con discapacidad",
    corto: "M CD vs H CD",
    grupos: ["M-CD", "H-CD"],
    colapsa: null,
    series: ["Mujeres con discapacidad", "Hombres con discapacidad"],
    llaveSerie: "grupo",
    pregunta: "Entre personas con discapacidad, ¿cuánto pesa ser mujer?",
  },
  {
    clave: "disc-mujeres",
    etiqueta: "Mujeres con vs sin discapacidad",
    corto: "M CD vs M SD",
    grupos: ["M-CD", "M-SD"],
    colapsa: null,
    series: ["Mujeres con discapacidad", "Mujeres sin discapacidad"],
    llaveSerie: "grupo",
    pregunta: "Entre mujeres, ¿cuánto pesa la discapacidad?",
  },
  {
    clave: "disc-extremo",
    etiqueta: "Mujer con discapacidad vs Hombre sin discapacidad",
    corto: "M CD vs H SD",
    grupos: ["M-CD", "H-SD"],
    colapsa: null,
    series: ["Mujeres con discapacidad", "Hombres sin discapacidad"],
    llaveSerie: "grupo",
    pregunta: "¿Qué tan grande es la brecha cuando se suman las dos desventajas?",
  },
  {
    clave: "sexo",
    etiqueta: "Mujeres vs Hombres",
    corto: "M vs H",
    grupos: ["M-CD", "M-SD", "H-CD", "H-SD"],
    // Colapsa la discapacidad: agrega ambos niveles dentro de cada sexo.
    colapsa: "disc",
    series: ["Mujeres", "Hombres"],
    llaveSerie: "sexo",
    pregunta: "¿Qué tan distinta es la situación de las mujeres frente a la de los hombres?",
  },
];

export const COMPARACION_POR_CLAVE = Object.fromEntries(
  COMPARACIONES.map((c) => [c.clave, c])
);

// --- Qué puede y qué no puede cada fuente -----------------------------------
// Las cuatro encuestas NO son intercambiables. Ofrecer un filtro que la fuente
// no sostiene produce cifras que se ven bien y no significan nada, y ese es el
// error más caro del tablero porque no se detecta contando casos.
//
// `nivel`: hasta dónde llega la representatividad del diseño muestral.
// `comparaciones`: cuáles de los tres pares tienen sentido en esa fuente.
export const FUENTES = {
  enadis: {
    nombre: "ENADIS",
    anios: [2017, 2022],
    // Representatividad nacional. NO admite desagregación por entidad, aunque
    // el número de casos por estado parezca suficiente.
    nivel: "nacional",
    comparaciones: ["sexo", "disc-mujeres", "disc-sexo"],
    nota: "Diseño muestral nacional: no produce estimaciones por entidad.",
  },
  enigh: {
    nombre: "ENIGH",
    anios: [2020, 2022, 2024],
    nivel: "estatal",
    comparaciones: ["sexo", "disc-mujeres", "disc-sexo"],
    nota: "Las ediciones 2016 y 2018 no traen tabla de población y quedan fuera.",
  },
  censo: {
    nombre: "Censo 2020 (cuestionario ampliado)",
    anios: [2020],
    // Única fuente con desagregación municipal: de aquí salen mapa y ranking.
    nivel: "municipal",
    comparaciones: ["sexo", "disc-mujeres", "disc-sexo"],
    nota: "Muestra ampliada del Censo; única fuente con nivel municipal.",
  },
  endireh: {
    nombre: "ENDIREH",
    anios: [2016, 2021],
    nivel: "estatal",
    // Solo entrevista mujeres de 15 años o más: no existe el hombre como
    // término de comparación. Las dos comparaciones que lo requieren se
    // ocultan, no se dibujan vacías.
    comparaciones: ["disc-mujeres"],
    nota: "Encuesta aplicada solo a mujeres de 15 años o más: no admite " +
          "comparación con hombres. La pregunta de discapacidad existe desde 2021.",
  },
};

// Comparaciones válidas para una fuente. La página pinta el selector con esto,
// de modo que un par imposible nunca llega a ofrecerse.
export function comparacionesDe(fuente) {
  const f = FUENTES[fuente];
  if (!f) return COMPARACIONES;
  return COMPARACIONES.filter((c) => f.comparaciones.includes(c.clave));
}

// ¿Esta fuente admite desagregación geográfica de este nivel?
export function admiteNivel(fuente, nivel) {
  const orden = {nacional: 0, estatal: 1, municipal: 2};
  const f = FUENTES[fuente];
  if (!f) return false;
  return orden[nivel] <= orden[f.nivel];
}

// Escala de color de Plot para una comparación dada. Con dos series siempre
// hay leyenda (regla: >= 2 series => leyenda presente).
export function escalaColor(comparacion) {
  const c = COMPARACION_POR_CLAVE[comparacion] ?? COMPARACIONES[0];
  if (c.llaveSerie === "sexo") {
    return {domain: c.series, range: c.series.map((s) => COLOR_SEXO[s]), legend: true};
  }
  const colores = c.grupos.map((k) => GRUPO_POR_CLAVE[k].color);
  return {domain: c.series, range: colores, legend: true};
}

// Etiqueta de serie de una fila, según la comparación activa. Es lo que se usa
// como canal de color y en la leyenda.
export function serieDe(fila, comparacion) {
  const c = COMPARACION_POR_CLAVE[comparacion] ?? COMPARACIONES[0];
  if (c.llaveSerie === "sexo") return fila.sexo;
  return `${fila.sexo === "Mujeres" ? "Mujeres" : "Hombres"} ${
    fila.disc === "Con discapacidad" ? "con" : "sin"} discapacidad`;
}

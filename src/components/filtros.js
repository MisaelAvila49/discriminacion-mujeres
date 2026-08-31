// src/components/filtros.js
// Panel de filtros homologado del tablero y la preparación de datos que
// consumen las gráficas.
//
// Reglas de los filtros (heredadas del diseño de anomalias-concesiones):
//   - Un selector aparece solo si tiene más de una opción real. Un "Año" con
//     un único año es ruido, no un control.
//   - Si una dimensión no aplica a la fuente, se oculta; no se deja vacía ni
//     deshabilitada. El caso vivo es ENADIS, que no admite desagregación por
//     entidad, y ENDIREH, que no admite comparación con hombres.
//   - El centinela de "sin filtro" es la cadena "Todas"/"Todos", nunca null ni
//     "". Un centinela inconsistente entre el control y el comparador es lo
//     que deja el tablero filtrado por un valor inexistente y las gráficas en
//     blanco.

import * as Inputs from "npm:@observablehq/inputs";
import {html} from "npm:htl";
import {
  COMPARACIONES, comparacionesDe, FUENTES, admiteNivel, serieDe, ORDEN_EDAD,
} from "./comparacion.js";
import {tasaPorGrupo} from "./agregar.js";

// --- Los dos sentidos de "todos" -------------------------------------------
// Un selector puesto en "todos" puede querer decir dos cosas distintas, y
// confundirlas es lo que hacía que el tablero mostrara cifras que no
// corresponden a ninguna población real:
//
//   AGREGADO  ("Todas las edades"): junta los grupos en una sola barra. Es
//     válido cuando los grupos son disjuntos dentro de un mismo levantamiento;
//     sumar los rangos de edad de la ENIGH 2024 reconstruye la población
//     adulta de 2024, que existe.
//
//   POR SEPARADO ("Por rango de edad"): una faceta por valor. No agrega nada,
//     solo despliega. Es el único sentido admisible para el año.
//
// El año NO admite el sentido agregado. Sumar numerador y denominador de 2020,
// 2022 y 2024 cuenta tres veces a la misma población y da 51.4% de ocupación
// femenina, una cifra que no corresponde a ninguna edición: 2020 fue 48.9%,
// 2022 fue 52.6% y 2024 fue 52.5%. Por eso el selector de año ofrece
// "Comparar años" (facetas) y nunca un agregado.
export const TODAS = "Todas";
export const TODOS = "Todos";

// Centinelas del modo "por separado". Se distinguen de TODOS/TODAS para que el
// código nunca tenga que adivinar cuál de los dos sentidos se pidió.
export const POR_SEPARADO = "__facetas__";
export const AGREGADO = "__agregado__";

export const ETIQUETA_EDAD_AGREGADA = "Todas las edades (juntas)";
export const ETIQUETA_EDAD_FACETAS = "Por rango de edad (por separado)";
export const ETIQUETA_ANIO_FACETAS = "Comparar años (por separado)";

// Centinela de "todos los dominios de discapacidad juntos": es el
// comportamiento de siempre, sin desagregar. NO se llama TODOS porque ese
// centinela ya significa "sin filtrar la dimensión" en filtrar() de forma
// genérica, y aquí además hay que distinguirlo de un dominio real llamado
// "Todos" que no existe pero podría confundirse.
export const TODOS_TIPO_DISC = "Todos";

// Mismo patrón que TODOS_TIPO_DISC: centinela de "todos los deciles
// juntos" (comportamiento agregado de hoy), distinto del TODAS/TODOS
// genérico de filtrar().
export const TODOS_DECIL = "Todos";
export const ETIQUETA_DECIL_TODOS = "Todos los deciles";
export const ETIQUETA_DECIL_COMPARAR = "Comparar deciles";

// El orden ordinal de los rangos de edad vive en comparacion.js (módulo base).
// Se importa arriba y se reexporta para no romper a quien ya lo tomaba de este
// módulo; el reexport por sí solo no crearía el binding que usa este archivo.
export {ORDEN_EDAD};

// Construye el panel. `datos` son las filas crudas del data loader de la
// fuente activa; de ahí se derivan las opciones reales de cada selector.
// `edadInicial` permite que una página abra ya desglosada por edad. Lo usa la
// página de violencia: su agregado sin controlar por edad invierte el signo del
// hallazgo (paradoja de Simpson), así que ahí el desglose es el estado inicial
// y no algo que el lector tenga que descubrir.
export function panelFiltros(datos, {fuente, mostrarEntidad = null,
    mostrarEdad = true, comparacionInicial = null,
    edadInicial = AGREGADO} = {}) {
  const meta = FUENTES[fuente] ?? {};
  const compsValidas = comparacionesDe(fuente);

  const anios = [...new Set(datos.map((d) => String(d.anio)))].sort();
  const entidades = [...new Set(datos.map((d) => d.entidad))]
    .filter(Boolean).sort((a, b) => a.localeCompare(b, "es"));
  const rangos = ORDEN_EDAD.filter((r) => datos.some((d) => d.rango_edad === r));
  const tiposDisc = [...new Set(datos.map((d) => d.tipo_discapacidad))]
    .filter((t) => t && t !== TODOS_TIPO_DISC).sort((a, b) => a.localeCompare(b, "es"));
  const deciles = [...new Set(datos.map((d) => d.decil))]
    .filter((dc) => dc && dc !== TODOS_DECIL)
    .sort((a, b) => Number(a) - Number(b));

  // La entidad se ofrece solo si la fuente es representativa a ese nivel. Es
  // la salvaguarda de ENADIS: aunque hay casos suficientes por estado, su
  // diseño muestral no sostiene la estimación.
  const puedeEntidad = mostrarEntidad ?? admiteNivel(fuente, "estatal");

  const comparacion = Inputs.select(
    compsValidas.map((c) => c.clave),
    {
      label: "Comparación",
      value: comparacionInicial ?? compsValidas[0]?.clave,
      format: (k) => COMPARACIONES.find((c) => c.clave === k)?.etiqueta ?? k,
    }
  );

  // Año: un año concreto, o comparar todos como facetas. Nunca agregado.
  // Arranca comparando ediciones: la evolución en el tiempo es lo primero que
  // se quiere ver, y fijar un año de entrada escondía que existe la serie.
  const anio = anios.length > 1
    ? Inputs.select([POR_SEPARADO, ...anios], {
        label: "Año",
        value: POR_SEPARADO,
        format: (k) => k === POR_SEPARADO ? ETIQUETA_ANIO_FACETAS : k,
      })
    : null;

  const entidad = puedeEntidad && entidades.length > 1
    ? Inputs.select([TODAS, ...entidades], {label: "Entidad", value: TODAS})
    : null;

  // Edad: agregada (una barra con toda la población), por separado (una
  // faceta por rango) o un rango concreto.
  const edad = mostrarEdad && rangos.length > 1
    ? Inputs.select([AGREGADO, POR_SEPARADO, ...rangos], {
        label: "Rango de edad",
        value: edadInicial,
        format: (k) => k === AGREGADO ? ETIQUETA_EDAD_AGREGADA
                     : k === POR_SEPARADO ? ETIQUETA_EDAD_FACETAS : k,
      })
    : null;

  // Dominio de dificultad (NO "tipo de discapacidad": la ENIGH pregunta ocho
  // dominios de dificultad funcional — ver, oír, caminar...— que no son
  // categorías diagnósticas de discapacidad. Llamarlo "tipo" sugeriría una
  // clasificación clínica que estos datos no ofrecen). Solo tiene sentido
  // con la comparación "Mujeres vs
  // Hombres con discapacidad" (ambas series ya están filtradas a "con
  // discapacidad"; desagregar por dominio dice EN QUÉ tipo pesa más ser
  // mujer). En las otras dos comparaciones una de las series es "sin
  // discapacidad", que no tiene dominio que mostrar, así que el filtro se
  // oculta en vez de ofrecer una desagregación que no aplica a media
  // gráfica. Reacciona al valor ACTUAL de comparación, no solo al inicial:
  // ver más abajo el manejo de mostrarSelectorTipo.
  let tipoDisc = null;
  let tipoDiscWrap = null;
  function actualizarVisibilidadTipo() {
    if (!tipoDiscWrap) return;
    const mostrar = comparacion.value === "disc-sexo" && tiposDisc.length > 1;
    tipoDiscWrap.style.display = mostrar ? "" : "none";
  }
  // "Brazos o manos" o "Bañarse o vestirse" a secas leen como partes del
  // cuerpo, no como el dominio de dificultad que son. Con prefijo quedan
  // como fragmento de oración ("Dificultad para caminar"). "Mental" es la
  // excepción: no es una acción, así que no acepta el mismo prefijo.
  const ETIQUETA_DOMINIO = {
    Mental: "Dificultad mental o emocional",
  };
  if (tiposDisc.length > 1) {
    tipoDisc = Inputs.select([TODOS_TIPO_DISC, ...tiposDisc], {
      label: "Dominio de dificultad", value: TODOS_TIPO_DISC,
      format: (k) => k === TODOS_TIPO_DISC ? "Todos los dominios"
        : ETIQUETA_DOMINIO[k] ?? `Dificultad para ${k.toLowerCase()}`,
    });
    tipoDiscWrap = html`<div class="filtro-tipo-disc">${tipoDisc}</div>`;
  }

  // Decil de ingreso: a diferencia de dominio de dificultad, aplica a las
  // 4 comparaciones por igual (no solo a "disc-sexo"), así que siempre se
  // muestra si hay más de un decil real en los datos filtrados — sin
  // gatillo de comparación. Activarlo excluye año-por-facetas y
  // edad-por-facetas: el decil sustituye el eje X (ver geometria() en
  // este mismo archivo), y desplegar además año o edad como facetas
  // produciría 30-40 grupos de barras en un solo panel, ilegible. Si el
  // usuario reactiva "comparar años" o "por rango de edad" mientras decil
  // está activo, decil vuelve a "Todos" — mismo patrón defensivo que ya
  // usa tipoDiscapacidad para no dejar un filtro fantasma detrás de una
  // gráfica que ya no lo muestra.
  let decilInput = null;
  if (deciles.length > 1) {
    decilInput = Inputs.select([TODOS_DECIL, ETIQUETA_DECIL_COMPARAR], {
      label: "Decil de ingreso", value: TODOS_DECIL,
      format: (k) => k === TODOS_DECIL ? ETIQUETA_DECIL_TODOS : k,
    });
  }

  const controles = [comparacion, anio, entidad, edad, decilInput].filter(Boolean);
  const cont = html`<div class="panel-filtros">
    ${controles}
    ${tipoDiscWrap ?? ""}
    ${meta.nota ? html`<p class="panel-nota">${meta.nota}</p>` : ""}
  </div>`;

  const valor = () => ({
    comparacion: comparacion.value,
    // Si solo hay un año, ese es el año; no hay nada que comparar.
    anio: anio ? anio.value : (anios[0] ?? POR_SEPARADO),
    entidad: entidad ? entidad.value : TODAS,
    rangoEdad: edad ? edad.value : AGREGADO,
    // Fuera de "disc-sexo" el filtro está oculto: se fuerza a "Todos" para
    // que cambiar de comparación y volver no deje un dominio pegado detrás
    // de una gráfica que ya no lo muestra.
    tipoDiscapacidad: (tipoDisc && comparacion.value === "disc-sexo")
      ? tipoDisc.value : TODOS_TIPO_DISC,
    decil: decilInput ? decilInput.value : TODOS_DECIL,
  });

  // Exclusión mutua: activar decil fuerza año a un valor concreto y edad a
  // agregado; reactivar año-por-facetas o edad-por-facetas fuerza decil a
  // "Todos". Se resuelve en los propios listeners de cada control, no en
  // valor(), para que el estado interno de los Inputs (lo que se ve en
  // pantalla) quede sincronizado con lo que valor() reporta — si solo se
  // pisara el valor reportado sin tocar el control, el selector seguiría
  // mostrando la opción vieja aunque el filtro real ya hubiera cambiado.
  function comparandoDeciles() {
    return decilInput && decilInput.value === ETIQUETA_DECIL_COMPARAR;
  }

  cont.value = valor();
  actualizarVisibilidadTipo();
  for (const c of controles) {
    c.addEventListener("input", () => {
      actualizarVisibilidadTipo();
      if (c === decilInput && comparandoDeciles()) {
        // Solo se pisa el año si estaba en "comparar años" (facetas): ahí
        // sí hay que fijarlo a alguno concreto porque decil ocupa el eje X.
        // Si el usuario ya tenía un año concreto elegido, se respeta — no
        // hay motivo para saltar al más reciente y cambiarle los datos que
        // está viendo sin que lo haya pedido.
        if (anio && anio.value === POR_SEPARADO) anio.value = anios.at(-1);
        if (edad) edad.value = AGREGADO;
      } else if ((c === anio || c === edad) && comparandoDeciles()) {
        decilInput.value = TODOS_DECIL;
      }
      cont.value = valor();
      cont.dispatchEvent(new Event("input", {bubbles: true}));
    });
  }
  if (tipoDisc) {
    tipoDisc.addEventListener("input", () => {
      cont.value = valor();
      cont.dispatchEvent(new Event("input", {bubbles: true}));
    });
  }
  return cont;
}

// --- Preparación de datos ---------------------------------------------------

// Aplica los filtros del panel a las filas crudas. No calcula porcentajes:
// solo recorta el universo. La agregación viene después, para que sumar
// entidades o edades nunca promedie tasas.
// Los centinelas de "por separado" y "agregado" NO recortan: en ambos casos
// entran todas las filas y lo que cambia es cómo se dibujan después. Solo un
// valor concreto recorta el universo.
export function filtrar(datos, {indicador = null, anio = POR_SEPARADO,
    entidad = TODAS, rangoEdad = AGREGADO, tipoDiscapacidad = TODOS_TIPO_DISC,
    decil = TODOS_DECIL} = {}) {
  const abierto = (v) => v === TODOS || v === TODAS ||
                         v === POR_SEPARADO || v === AGREGADO;
  // `decil` en `filtrar()` es "Todos" (sin recortar) o "Comparar deciles"
  // (tampoco recorta: entran todas las filas reales, el desglose lo hace
  // geometria()/dimX, no este filtro) — nunca un decil concreto, porque el
  // panel no ofrece elegir un solo decil, solo agregado o comparar todos.
  return datos.filter((d) =>
    (indicador == null || d.indicador === indicador) &&
    (abierto(anio) || String(d.anio) === String(anio)) &&
    (abierto(entidad) || d.entidad === entidad) &&
    (abierto(rangoEdad) || d.rango_edad === rangoEdad) &&
    (d.tipo_discapacidad == null || d.tipo_discapacidad === (tipoDiscapacidad ?? TODOS_TIPO_DISC)) &&
    (d.decil == null ||
      (decil === TODOS_DECIL ? d.decil === TODOS_DECIL : true))
  );
}

// Traduce el estado del panel a la geometría de la gráfica: qué va en el eje x
// y qué va en las facetas de la rejilla de pequeños múltiplos.
//
// Devuelve {dimX, facetaCol, facetaFila}. `dimX` es lo que separa las barras
// dentro de cada panel; las facetas multiplican paneles.
export function geometria(v, {aniosDisponibles = []} = {}) {
  const comparaDeciles = v.decil === ETIQUETA_DECIL_COMPARAR;

  // Comparar deciles sustituye el eje X y excluye año/edad como facetas —
  // la exclusión mutua ya se resuelve en panelFiltros() forzando los
  // controles, pero geometria() la respeta aquí también por si acaso llega
  // un estado inconsistente (por ejemplo, un valor de panel guardado de
  // antes de este cambio): comparar deciles SIEMPRE gana sobre año/edad.
  if (comparaDeciles) {
    return {facetaCol: null, facetaFila: null, dimX: "decil"};
  }

  const comparaAnios = v.anio === POR_SEPARADO && aniosDisponibles.length > 1;
  const separaEdad = v.rangoEdad === POR_SEPARADO;

  // Los años van como columnas (se leen de izquierda a derecha, como el
  // tiempo) y las edades como filas.
  //
  // Dentro de cada panel el eje x son siempre las series de la comparación.
  // "Todas las edades (juntas)" significa exactamente eso: una barra por
  // serie con la población agregada, no las edades desplegadas en el eje.
  // Poner ahí la edad sería devolver un desglose que el usuario no pidió.
  return {
    facetaCol: comparaAnios ? "anio" : null,
    facetaFila: separaEdad ? "rango_edad" : null,
    dimX: null,
  };
}

// Convierte filas crudas en las series de la comparación activa y las agrega
// por la dimensión pedida.
//
// `dim` es la dimensión del eje: "rango_edad", "anio" o "entidad". Puede ser
// null para un solo grupo de barras (solo las series).
//
// El paso clave: `serieDe` colapsa los cuatro grupos a las dos series de la
// comparación, y solo entonces se agrega. Para "Mujeres vs Hombres" eso suma
// a las mujeres con y sin discapacidad en una sola serie, que es justo lo que
// esa comparación significa.
// `dim` puede ser un nombre de columna o un arreglo de nombres: al facetar por
// año y edad a la vez, la agregación tiene que respetar ambas llaves para que
// cada panel de la rejilla tenga su propia cifra en vez de repetir el total.
export function prepararSeries(datos, {comparacion, dim = null, formato = "pct"}) {
  const comp = COMPARACIONES.find((c) => c.clave === comparacion);
  if (!comp) return [];
  const dims = (Array.isArray(dim) ? dim : [dim]).filter(Boolean);
  const separaDecil = dims.includes("decil");

  // Solo los grupos que participan en la comparación, decidido por
  // pertenencia real a `comp.grupos` (no por un `if` a mano por cada
  // clave): "sexo" colapsa discapacidad y usa los 4 grupos, las demás
  // comparaciones son subconjuntos de 2. Antes esto era un `if` explícito
  // por clave (sexo / disc-mujeres / disc-sexo); con una 4ª comparación
  // (disc-extremo) y la posibilidad de más en el futuro, filtrar por la
  // lista ya declarada en COMPARACIONES evita mantener dos fuentes de
  // verdad sincronizadas a mano.
  const filas = datos
    .filter((d) => {
      if (comp.clave === "sexo") return true;
      const sx = d.sexo === "Mujeres" ? "M" : "H";
      const cd = d.disc === "Con discapacidad" ? "CD" : "SD";
      return comp.grupos.includes(`${sx}-${cd}`);
    })
    // Cuando se está separando por decil (dim incluye "decil"), la fila
    // agregada decil="Todos" no tiene un valor numérico que graficar en
    // el eje X — se excluye aquí, antes de agregar, para que no aparezca
    // como una undécima barra sin sentido junto a los deciles 1-10.
    .filter((d) => !separaDecil || d.decil !== TODOS_DECIL)
    .map((d) => ({...d, serie: serieDe(d, comparacion)}));

  const agregadas = tasaPorGrupo(filas, ["serie", ...dims], formato);

  // Orden estable: primero por las dimensiones (edad y decil en su orden
  // ordinal/numérico, no alfabético — "10" antes que "2" alfabéticamente
  // sería un orden sin sentido para una escala de pobre a rico), luego por
  // el orden de las series declaradas en la comparación, para que la
  // leyenda y las barras coincidan siempre.
  const posSerie = new Map(comp.series.map((s, i) => [s, i]));
  return agregadas.sort((a, b) => {
    for (const k of dims) {
      if (k === "rango_edad") {
        const d = ORDEN_EDAD.indexOf(a.rango_edad) - ORDEN_EDAD.indexOf(b.rango_edad);
        if (d !== 0) return d;
      } else if (k === "decil") {
        const d = Number(a.decil) - Number(b.decil);
        if (d !== 0) return d;
      } else {
        const d = String(a[k] ?? "").localeCompare(String(b[k] ?? ""), "es");
        if (d !== 0) return d;
      }
    }
    return (posSerie.get(a.serie) ?? 99) - (posSerie.get(b.serie) ?? 99);
  });
}

// Brecha entre las dos series de la comparación, en puntos porcentuales.
// Devuelve también el texto listo para la tarjeta de KPI.
export function brechaDe(series, comparacion, {formato = "pct"} = {}) {
  const comp = COMPARACIONES.find((c) => c.clave === comparacion);
  if (!comp) return null;
  const [a, b] = comp.series;
  const fa = series.find((s) => s.serie === a);
  const fb = series.find((s) => s.serie === b);
  if (!fa || !fb || fa.pct == null || fb.pct == null) return null;

  const dif = fa.pct - fb.pct;
  if (formato === "pesos") {
    const razon = fb.pct ? fa.pct / fb.pct : null;
    return {
      dif,
      texto: "$" + Math.round(Math.abs(dif)).toLocaleString("es-MX"),
      detalle: razon
        ? `${a} ganan ${(razon * 100).toFixed(0)} pesos por cada 100 que ganan ${b.toLowerCase()}`
        : "",
    };
  }
  if (formato === "conteo") {
    // Diferencia de personas, no de puntos porcentuales: "125 mil personas
    // más alto en mujeres con discapacidad", no "12.5 pp". Mismo tono que el
    // detalle genérico de abajo (sin comillas, grupo en minúsculas a media
    // frase), para que la voz de la tarjeta de KPI sea uniforme entre
    // formatos.
    return {
      dif,
      texto: Math.round(Math.abs(dif)).toLocaleString("es-MX"),
      detalle: `Más alto en ${(dif >= 0 ? a : b).toLowerCase()}`,
    };
  }
  // El detalle cabe en un renglón: nombra al grupo que queda más alto y ya.
  // Decir "X por encima de Y" repite el nombre completo de las dos series y
  // en esta comparación llega a "Hombres con discapacidad por encima de
  // mujeres con discapacidad", que se desborda a tres líneas.
  //
  // Se dice "más alto en" y no "a favor de": el tablero mide tanto cosas
  // buenas (ocupación, ingreso) como malas (violencia, analfabetismo), y en
  // esas últimas estar arriba no es estar mejor.
  return {
    dif,
    texto: `${Math.abs(dif).toFixed(1)} pp`,
    detalle: `Más alto en ${(dif >= 0 ? a : b).toLowerCase()}`,
  };
}

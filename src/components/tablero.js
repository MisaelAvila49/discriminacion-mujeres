// src/components/tablero.js
// El renderer de las páginas temáticas. Las páginas son cascarones de unas
// pocas líneas que llaman a `dashboardTema(clave, datos)`; toda la lógica de
// armado vive aquí, para que N páginas compartan un solo renderer y el texto
// viva en un catálogo en vez de repartido por los archivos .md.

import {html} from "npm:htl";
import {resize} from "observablehq:stdlib";
import * as Inputs from "npm:@observablehq/inputs";
import {
  panelFiltros, filtrar, prepararSeries, brechaDe, geometria,
  TODAS, POR_SEPARADO, AGREGADO,
} from "./filtros.js";
import {
  barrasComparadas, avisoMuestra, kpis,
  tablaDatos, formatear, heatmapEdadAnio,
  mapasMultiples, barrasPorEntidad, heatmapEntidades, explicacion,
  rankingComparado,
} from "./graficas.js";
import {
  COMPARACION_POR_CLAVE, FUENTES, admiteNivel, ORDEN_EDAD,
} from "./comparacion.js";
import {CATALOGO, ENCUESTAS, ENCUESTA_POR_CLAVE} from "./catalogo.js";

export {CATALOGO, ENCUESTAS, ENCUESTA_POR_CLAVE};

// Etiqueta legible de la dimensión del eje.
const ETIQUETA_DIM = {
  rango_edad: "Rango de edad",
  anio: "Edición",
  entidad: "Entidad",
  decil: "Decil de ingreso",
};

// Arma una gráfica completa: barras + aviso de muestra + tabla de respaldo,
// dentro de una tarjeta. `geo` trae la geometría de facetas del panel.
function bloqueGrafica(filas, {comparacion, geo, formato, titulo,
    fuente, explica = null}) {
  const dims = [geo.facetaCol, geo.facetaFila, geo.dimX].filter(Boolean);
  const series = prepararSeries(filas, {comparacion, dim: dims, formato});
  if (!series.length) {
    return html`<div class="card"><p class="aviso-muestra">Sin datos para esta
      combinación de filtros. Prueba con otro año o quita el filtro de
      entidad.</p></div>`;
  }

  // Facetar por una dimensión con un solo valor no despliega nada y sí parte
  // la gráfica en una columna angosta. Le pasa a los indicadores del Censo,
  // que solo tienen 2020: con "comparar años" quedaban en una tira de barras
  // diminutas. Si la dimensión no varía en ESTOS datos, se deja plana.
  const nCol = geo.facetaCol
    ? new Set(series.map((d) => d[geo.facetaCol])).size : 0;
  const nFila = geo.facetaFila
    ? new Set(series.map((d) => d[geo.facetaFila])).size : 0;
  const facetaCol = nCol > 1 ? geo.facetaCol : null;
  const facetaFila = nFila > 1 ? geo.facetaFila : null;

  // Cuando se cruzan las dos dimensiones (año y rango de edad), la rejilla de
  // barras produce doce paneles que no caben en una pantalla. La misma
  // información entra en un heatmap de año por edad, con una cuadrícula por
  // serie, y además deja ver el gradiente de un vistazo.
  const cruzaAnioYEdad = Boolean(facetaCol && facetaFila);

  // Sin faceta de columna pero con desglose por edad, la edad se lee mejor en
  // el eje x que como filas apiladas: son cuatro barras por serie, no cuatro
  // paneles de una barra.
  const dimX = (!facetaCol && facetaFila === "rango_edad")
    ? "rango_edad" : geo.dimX;
  const facetaFilaFinal = dimX === "rango_edad" ? null : facetaFila;

  const grafica = resize((width) => cruzaAnioYEdad
    ? heatmapEdadAnio(series, {comparacion, formato, titulo, fuente, width})
    : barrasComparadas(series, {
        dim: dimX, dimLabel: ETIQUETA_DIM[dimX] ?? "",
        facetaCol, facetaFila: facetaFilaFinal,
        comparacion, formato, titulo, fuente, width,
      }));

  return html`<div class="card">
    ${grafica}
    ${avisoMuestra(series)}
    ${explicacion(explica)}
    ${tablaDatos(series, {
      dim: dims[0] ?? "serie",
      dimLabel: ETIQUETA_DIM[dims[0]] ?? "Grupo", formato,
    })}
  </div>`;
}

// Renderiza la página completa de un tema. `datos` son TODAS las filas del
// archivo de indicadores; aquí se recortan por encuesta e indicador.
// `geoEntidades` es el FeatureCollection de los estados. Es opcional: si no se
// pasa, la sección de territorio muestra solo el ranking.
// --- Secciones con filtros propios ------------------------------------------
// Cada sección de la página tiene su propio panel y se repinta sola. Antes un
// único panel gobernaba las tres, y como las fuentes no comparten ediciones
// (ENIGH trae 2020-2024, el Censo solo 2020, ENDIREH solo 2021), un estado
// válido para una sección producía geometrías imposibles en otra. Con paneles
// independientes cada bloque solo ofrece lo que sus datos sostienen.
function seccion({titulo, datos, fuente, construir, edadInicial = AGREGADO,
    conEntidad = null, conDecil = true, extras = []}) {
  if (!datos.length) return null;

  const panel = panelFiltros(datos, {fuente, edadInicial,
                                     mostrarEntidad: conEntidad,
                                     mostrarDecil: conDecil});
  // Controles propios de la sección (por ejemplo, el selector de ámbito del
  // ranking). Viven junto al panel y repintan igual que sus filtros.
  for (const ex of extras) {
    ex.addEventListener("input", () => pintar());
  }
  const cuerpo = html`<div class="seccion-cuerpo"></div>`;
  const anios = [...new Set(datos.map((d) => String(d.anio)))].sort();

  function pintar() {
    const v = panel.value;
    const geo = geometria(v, {aniosDisponibles: anios});
    const nodos = construir({v, geo, anios});
    cuerpo.replaceChildren(...nodos.filter(Boolean));
  }
  panel.addEventListener("input", pintar);
  pintar();

  return html`<section class="seccion-tablero">
    ${titulo ? html`<span class="kicker">${titulo}</span>` : ""}
    ${panel}
    ${extras.length ? html`<div class="panel-filtros">${extras}</div>` : ""}
    ${cuerpo}
  </section>`;
}

// `datosTipoDisc`/`datosDecil` son opcionales y vienen de archivos APARTE
// (indicadores_tipo_disc.csv, indicadores_decil.csv): ambos multiplican el
// tamaño de los datos, y la mayoría de las páginas no activan ninguno de
// los dos filtros. Separarlos evita que las páginas que no los usan paguen
// su peso de descarga. Solo Trabajo/Apoyos/Educación (ENIGH) pasan
// `datosDecil` por ahora; el selector de decil solo aparece si hay más de
// un valor real en los datos, así que si esto no se pasa el filtro
// simplemente no se ofrece (mismo criterio que ya usa datosTipoDisc).
export function dashboardTema(clave, datos, {geoEntidades = null,
    datosTipoDisc = null, datosDecil = null} = {}) {
  const tema = CATALOGO[clave];
  if (!tema) return html`<p>Tema desconocido: ${clave}</p>`;

  const fuente = tema.fuentePrincipal;
  // `todo` reúne el archivo principal con los dos de desglose SIN filtrar por
  // encuesta, porque los indicadores secundarios de un tema pueden venir de
  // otra (por ejemplo, un tema de ENIGH que contrasta con una cifra del
  // Censo). Filtrar por la fuente principal aquí dejaba a la sección de
  // secundarios leyendo solo `datos` —el archivo principal, que no trae las
  // columnas de dominio ni de decil—, y por eso su panel nunca ofrecía esos
  // dos filtros aunque los datos existieran.
  const todo = datos.concat(datosTipoDisc ?? [], datosDecil ?? []);
  const datosFuente = todo.filter((d) => d.encuesta === fuente);
  const principales = datosFuente.filter((d) => d.indicador === tema.indicadorPrincipal);

  // --- Sección 1: el indicador principal, con sus KPIs -------------------
  const seccionPrincipal = seccion({
    titulo: null,
    datos: principales,
    fuente,
    edadInicial: tema.abrePorEdad ? POR_SEPARADO : AGREGADO,
    construir: ({v, geo, anios}) => {
      const filas = filtrar(datosFuente, {
        indicador: tema.indicadorPrincipal,
        anio: v.anio, entidad: v.entidad, rangoEdad: v.rangoEdad,
        tipoDiscapacidad: v.tipoDiscapacidad,
        decil: v.decil,
      });

      // Las tarjetas resumen SIEMPRE una sola edición. Mezclar años contaría
      // a la misma población varias veces, así que al comparar ediciones se
      // toma la más reciente y la tarjeta lo dice.
      const anioKpi = v.anio === POR_SEPARADO ? anios.at(-1) : v.anio;
      const filasKpi = filas.filter((d) => String(d.anio) === String(anioKpi));
      const total = prepararSeries(filasKpi, {
        comparacion: v.comparacion, dim: null, formato: tema.formato,
      });
      const brecha = brechaDe(total, v.comparacion, {formato: tema.formato});

      const tarjetas = [];
      if (brecha) {
        tarjetas.push({etiqueta: `Brecha ${anioKpi}`, cifra: brecha.texto,
                       nota: brecha.detalle});
      }
      for (const s of total) {
        tarjetas.push({
          etiqueta: s.serie,
          cifra: formatear(s.pct, tema.formato),
          nota: `${s.casos.toLocaleString("es-MX")} casos · ${anioKpi}`,
        });
      }

      return [
        kpis(tarjetas),
        bloqueGrafica(filas, {
          comparacion: v.comparacion, geo, formato: tema.formato,
          titulo: tema.indicadorPrincipal,
          fuente: filas[0]?.fuente ?? "",
          explica: tema.explica,
        }),
      ];
    },
  });

  // --- Sección 2: indicadores relacionados, con su propio panel ----------
  // Todos los secundarios de un tema comparten panel, pero ese panel se
  // construye con los datos de los secundarios, no con los del principal:
  // así el selector de año ofrece las ediciones que ellos sí tienen.
  const datosSec = (tema.secundarios ?? []).flatMap((sec) =>
    todo.filter((d) => d.encuesta === sec.encuesta && d.indicador === sec.indicador)
  );

  const seccionSecundarios = seccion({
    titulo: "Indicadores relacionados",
    datos: datosSec,
    // El panel se rige por la fuente menos permisiva de las involucradas, para
    // no ofrecer un filtro que alguna de las gráficas no pueda cumplir.
    fuente: tema.secundarios?.[0]?.encuesta ?? fuente,
    construir: ({v}) => {
      const tarjetas = [];
      for (const sec of tema.secundarios ?? []) {
        const fsec = todo.filter(
          (d) => d.encuesta === sec.encuesta && d.indicador === sec.indicador
        );
        const compsOk = FUENTES[sec.encuesta]?.comparaciones ?? [];
        // Si la comparación activa no aplica a la fuente del secundario (el
        // caso de ENDIREH con los pares que incluyen hombres), se omite en
        // vez de dibujar una gráfica vacía.
        if (!compsOk.includes(v.comparacion)) continue;

        // Cada indicador resuelve su propia geometría con SUS años: es lo que
        // evita que un indicador de un solo año (Censo) quede partido en una
        // columna vacía por comparar ediciones que no tiene.
        const aniosSec = [...new Set(fsec.map((d) => String(d.anio)))].sort();
        const geoSec = geometria(v, {aniosDisponibles: aniosSec});

        const ffil = filtrar(fsec, {
          anio: v.anio, entidad: v.entidad, rangoEdad: v.rangoEdad,
          tipoDiscapacidad: v.tipoDiscapacidad,
          decil: v.decil,
        });
        if (!ffil.length) continue;

        tarjetas.push(bloqueGrafica(ffil, {
          comparacion: v.comparacion, geo: geoSec,
          formato: sec.formato ?? "pct",
          titulo: sec.indicador,
          fuente: ffil[0]?.fuente ?? "",
          explica: sec.explica,
        }));
      }
      if (!tarjetas.length) {
        return [html`<p class="nota-indicador">Ningún indicador relacionado
          admite esta combinación de filtros.</p>`];
      }
      // Rejilla de dos columnas, con la primera gráfica a ancho completo
      // cuando el total es impar. Así nunca queda una tarjeta suelta ocupando
      // media fila:
      //
      //   1 -> 1              4 -> 2 + 2
      //   2 -> 2              5 -> 1 + 2 + 2
      //   3 -> 1 + 2
      //
      // El impar se resuelve promoviendo la primera, que es la más importante
      // de la sección, en vez de dejar un hueco al final.
      if (tarjetas.length === 1) {
        return [html`<div class="grid">${tarjetas}</div>`];
      }
      if (tarjetas.length % 2 === 1) {
        const [principal, ...resto] = tarjetas;
        return [
          html`<div class="grid">${principal}</div>`,
          html`<div class="grid grid-cols-2">${resto}</div>`,
        ];
      }
      return [html`<div class="grid grid-cols-2">${tarjetas}</div>`];
    },
  });

  // --- Sección de ranking, con su propio panel ---------------------------
  // Para temas con MUCHAS categorías de pocos datos cada una (los treinta
  // agresores de la ENDIREH): en vez de treinta gráficas de dos barras, una
  // sola de barras horizontales ordenada por brecha, con un selector para
  // elegir el grupo de indicadores. Un tema la activa declarando
  // `tema.ranking`; los demás no pagan nada.
  const seccionRanking = tema.ranking ? (() => {
    const grupos = tema.ranking.grupos ?? [];
    const indicadoresRanking = grupos.flatMap((g) => g.indicadores);
    const datosRank = todo.filter(
      (d) => d.encuesta === (tema.ranking.encuesta ?? fuente) &&
             indicadoresRanking.includes(d.indicador));
    if (!datosRank.length) return null;

    const selector = Inputs.select(grupos.map((g) => g.clave), {
      label: tema.ranking.etiqueta ?? "Ámbito",
      value: grupos[0]?.clave,
      format: (k) => grupos.find((g) => g.clave === k)?.nombre ?? k,
    });

    return seccion({
      titulo: tema.ranking.titulo ?? "Ranking",
      datos: datosRank,
      fuente: tema.ranking.encuesta ?? fuente,
      // El ranking ya usa el eje vertical para las categorías: desplegar
      // además año o edad como facetas lo partiría en rejillas ilegibles.
      conDecil: false,
      extras: [selector],
      construir: ({v}) => {
        const grupo = grupos.find((g) => g.clave === selector.value)
          ?? grupos[0];
        const fdat = filtrar(
          datosRank.filter((d) => grupo.indicadores.includes(d.indicador)), {
            anio: v.anio, entidad: v.entidad, rangoEdad: v.rangoEdad,
            tipoDiscapacidad: v.tipoDiscapacidad,
          });
        if (!fdat.length) {
          return [html`<p class="nota-indicador">Sin datos para esta
            combinación de filtros.</p>`];
        }
        // `dim: "indicador"` en vez de una columna de dimensión propia: cada
        // agresor es un indicador distinto en el CSV, y la etiqueta legible
        // se recorta del nombre completo del indicador.
        const series = prepararSeries(fdat, {
          comparacion: v.comparacion, dim: "indicador",
          formato: tema.formato ?? "pct",
        }).map((d) => ({...d, indicador: grupo.recorta
          ? d.indicador.replace(grupo.recorta, "").replace(/ en los últimos 12 meses$/, "")
          : d.indicador}));

        return [html`<div class="grid">${html`<div class="card">
          ${resize((width) => rankingComparado(series, {
            dim: "indicador", dimLabel: grupo.dimLabel ?? "Agresor",
            comparacion: v.comparacion, formato: tema.formato ?? "pct",
            titulo: grupo.nombre, fuente: fdat[0]?.fuente ?? "",
            limite: tema.ranking.limite ?? 20, width,
          }))}
          ${avisoMuestra(series)}
          ${explicacion(grupo.explica ?? tema.ranking.explica)}
          ${tablaDatos(series, {dim: "indicador",
                                dimLabel: grupo.dimLabel ?? "Agresor",
                                formato: tema.formato ?? "pct"})}
        </div>`}</div>`];
      },
    });
  })() : null;

  // --- Sección 3: territorio, con su propio panel ------------------------
  // Solo existe si la fuente tiene representatividad estatal. Su panel oculta
  // el selector de entidad: la vista ES la desagregación por entidad, y
  // filtrar a una sola la dejaría sin sentido. También oculta decil
  // (conDecil: false): seriesDeCombo de abajo agrega por entidad nada más
  // (dim: "entidad", sin "decil"), así que "Comparar deciles" aquí mezclaría
  // la fila agregada "Todos" con las 10 filas por decil dentro del mismo
  // grupo entidad+serie — doble conteo silencioso en vez de una vista real.
  const seccionTerritorio = admiteNivel(fuente, "estatal")
    ? seccion({
        titulo: "Territorio",
        datos: principales,
        fuente,
        conEntidad: false,
        conDecil: false,
        construir: ({v, anios}) => {
          const comp = COMPARACION_POR_CLAVE[v.comparacion];
          const etiquetaValor = tema.formato === "pesos" ? "Ingreso"
            : tema.formato === "conteo" ? "Personas" : "Porcentaje";

          // Qué dimensiones están abiertas en esta vista. El territorio ya usa
          // una dimensión completa (las 32 entidades), así que cada dimensión
          // extra multiplica el número de mapas.
          const comparaAnios = v.anio === POR_SEPARADO && anios.length > 1;
          const separaEdad = v.rangoEdad === POR_SEPARADO;
          const edades = ORDEN_EDAD.filter((r) =>
            datosFuente.some((d) => d.rango_edad === r));

          // Las combinaciones de año y edad que hay que dibujar.
          const combos = [];
          for (const a of comparaAnios ? anios : [v.anio === POR_SEPARADO ? anios.at(-1) : v.anio]) {
            for (const e of separaEdad ? edades : [v.rangoEdad]) {
              combos.push({anio: a, edad: e});
            }
          }

          const etiquetaCombo = ({anio, edad}) => {
            const partes = [];
            if (comparaAnios) partes.push(String(anio));
            if (separaEdad) partes.push(`${edad} años`);
            return partes.join(" · ") || String(anio);
          };

          // Serie completa (las dos de la comparación, no solo la primera)
          // por entidad, para la gráfica de barras que encabeza la sección.
          const seriesDeCombo = (c) => {
            const filas = filtrar(datosFuente, {
              indicador: tema.indicadorPrincipal, anio: c.anio, rangoEdad: c.edad,
              tipoDiscapacidad: v.tipoDiscapacidad,
              decil: v.decil,
            });
            return {
              filas,
              porEnt: prepararSeries(filas, {
                comparacion: v.comparacion, dim: "entidad", formato: tema.formato,
              }),
            };
          };

          // --- Comparar ediciones: heatmap, no mapas ----------------------
          // Un mapa por edición obliga a saltar de uno a otro para ver si una
          // entidad subió o bajó, que es justo la pregunta que se hace al
          // comparar años. En un heatmap la entidad es una fila y su
          // evolución se lee de corrido.
          if (comparaAnios) {
            // Un heatmap por serie de la comparación, no solo por la primera.
            // Mostrar únicamente a las mujeres en una vista rotulada "Mujeres
            // vs Hombres" deja al lector sin el término de comparación: la
            // pregunta de la sección es la brecha, y una sola serie no la
            // responde. Los dos comparten escala de color, así que los tonos
            // son comparables entre cuadrículas.
            const seriesComp = comp?.series ?? [];
            const paneles = [];
            for (const s of seriesComp) {
              const celdas = [];
              for (const c of combos) {
                const {porEnt} = seriesDeCombo(c);
                for (const d of porEnt.filter((x) => x.serie === s)) {
                  // `grupo` rotula arriba (el año) y `sub` abajo (la edad).
                  // Separarlos evita la etiqueta "2020 · 18-29" que no cabe.
                  celdas.push({...d, grupo: String(c.anio),
                               sub: separaEdad ? c.edad : String(c.anio)});
                }
              }
              if (!celdas.length) continue;
              paneles.push(html`<div class="card matriz-alta">
                ${resize((width) => heatmapEntidades(celdas, {
                  titulo: s,
                  fuente: datosFuente[0]?.fuente ?? "",
                  formato: tema.formato, width,
                  // El eje de dos niveles solo hace falta cuando hay año Y
                  // edad; con solo el año, una fila de rótulos basta.
                  jerarquia: separaEdad,
                  etiquetaGrupo: "Año", etiquetaSub: "Rango de edad",
                }))}
                ${avisoMuestra(celdas)}
              </div>`);
            }
            if (!paneles.length) return [];

            return [
              html`<p class="nota-indicador">${tema.indicadorPrincipal} por
                entidad. Las dos cuadrículas comparten la escala de color, así
                que un mismo tono significa lo mismo en ambas.</p>`,
              html`<div class="grid ${
                paneles.length > 1 ? "grid-cols-2" : ""}">${paneles}</div>`,
            ];
          }

          const bloques = [];

          // --- Un año, edad por separado: una gráfica de barras por rango ---
          // Sin mapas. Con la edad abierta serían ocho mapas (cuatro rangos
          // por dos series) de 32 entidades, y a ese tamaño el tono deja de
          // distinguirse. Las barras conservan las dos series y las 32
          // entidades en cada rango, que es lo que se quiere comparar.
          if (separaEdad) {
            for (const c of combos) {
              const {filas, porEnt} = seriesDeCombo(c);
              if (porEnt.length < 2) continue;
              bloques.push(html`<div class="card">
                ${resize((width) => barrasPorEntidad(porEnt, {
                  comparacion: v.comparacion,
                  titulo: `${c.edad} años`,
                  fuente: filas[0]?.fuente ?? "",
                  formato: tema.formato, width,
                }))}
                ${avisoMuestra(porEnt)}
              </div>`);
            }
            if (!bloques.length) return [];
            return [
              html`<p class="nota-indicador">${tema.indicadorPrincipal} por
                entidad, un panel por rango de edad. Las entidades se ordenan
                por la brecha entre los dos grupos, así que el orden cambia
                de un rango a otro.</p>`,
              ...bloques,
            ];
          }

          // --- Un año, sin desglose de edad: barras arriba, mapas abajo ---
          // Las barras dan la comparación entidad por entidad (la brecha se
          // lee directo, sin saltar entre mapas); los mapas dan la forma
          // geográfica de cada grupo. Se complementan.
          const comboBarras = combos[0];
          const {filas: filasB, porEnt} = seriesDeCombo(comboBarras);
          if (porEnt.length >= 2) {
            bloques.push(html`<div class="card">
              ${resize((width) => barrasPorEntidad(porEnt, {
                comparacion: v.comparacion,
                titulo: `${tema.indicadorPrincipal} por entidad · ${etiquetaCombo(comboBarras)}`,
                fuente: filasB[0]?.fuente ?? "",
                formato: tema.formato, width,
              }))}
              ${avisoMuestra(porEnt)}
            </div>`);
          }

          // Mapas: uno por serie de la comparación (Mujeres, Hombres...), con
          // escala compartida para que los tonos sean comparables entre ellos.
          const seriesComp = comp?.series ?? [];
          for (const c of combos) {
            const {filas, porEnt: pe} = seriesDeCombo(c);
            const grupos = seriesComp.map((s) => {
              const foco = pe.filter((d) => d.serie === s);
              return {
                etiqueta: s,
                valores: new Map(foco.map((d) => [d.entidad, d.pct])),
                // `num`, no `den`: es la cuenta de quienes cumplen la
                // condición, ya expandida. Solo tiene sentido como
                // "población" en indicadores de porcentaje — en pesos u
                // horas sería masa de dinero o de tiempo.
                poblacion: tema.formato === "pct"
                  ? new Map(foco.map((d) => [d.entidad, d.num]))
                  : null,
                foco,
              };
            }).filter((g) => g.foco.length >= 2);
            if (!grupos.length) continue;

            bloques.push(html`<div class="card">
              ${geoEntidades
                ? resize((width) => mapasMultiples(geoEntidades, grupos, {
                    titulo: `Mapas por grupo · ${etiquetaCombo(c)}`,
                    fuente: filas[0]?.fuente ?? "",
                    formato: tema.formato, etiquetaValor, width,
                  }))
                : html`<p class="nota-indicador">Mapa no disponible.</p>`}
            </div>`);
          }

          return bloques;
        },
      })
    : null;

  return html`<div class="tablero-tema">
    <p class="entrada-tema">${tema.entrada}</p>
    ${[seccionPrincipal, seccionSecundarios, seccionRanking,
       seccionTerritorio].filter(Boolean)}
  </div>`;
}

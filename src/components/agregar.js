// src/components/agregar.js
// Agregación de indicadores por grupo. Dos reglas que no se negocian:
//
// 1. NUNCA se promedian porcentajes. Se suman numerador y denominador de cada
//    grupo y luego se divide. Promediar tasas de grupos de distinto tamaño da
//    un número que no corresponde a ninguna población real.
// 2. Toda cifra de encuesta va expandida por el factor de expansión (FAC_PER,
//    factor, FACTOR según la fuente), pero la SUFICIENCIA se juzga con el
//    número de casos SIN expandir. Un dato expandido a 40 mil personas que
//    viene de 8 entrevistas sigue siendo 8 entrevistas.

// Umbral de casos sin expandir debajo del cual la cifra se marca como frágil.
// 30 es el corte que usa el INEGI para no publicar una estimación directa.
export const MIN_CASOS = 30;

// Agrupa filas por un conjunto de llaves sumando numerador, denominador y el
// conteo de casos muestrales. Espera que cada fila traiga:
//   num    - suma ponderada de quienes cumplen la condición
//   den    - suma ponderada de la población de referencia
//   casos  - número de registros muestrales (sin expandir) del denominador
export function agrupar(datos, llaves) {
  const mapa = new Map();
  for (const fila of datos) {
    const clave = llaves.map((k) => fila[k]).join("||");
    if (!mapa.has(clave)) {
      const base = {};
      for (const k of llaves) base[k] = fila[k];
      base.num = 0;
      base.den = 0;
      base.casos = 0;
      mapa.set(clave, base);
    }
    const acc = mapa.get(clave);
    acc.num += Number(fila.num) || 0;
    acc.den += Number(fila.den) || 0;
    acc.casos += Number(fila.casos) || 0;
  }
  return [...mapa.values()];
}

// Agrega pct = num/den*100 y la bandera de fragilidad. pct queda null si no hay
// denominador (no es cero: es "no calculable", y una barra en cero mentiría).
export function conPorcentaje(filas) {
  return filas.map((f) => ({
    ...f,
    pct: f.den > 0 ? (f.num / f.den) * 100 : null,
    fragil: f.casos < MIN_CASOS,
  }));
}

// Atajo: agrupar + porcentaje en un paso.
export function tasaPorGrupo(datos, llaves) {
  return conPorcentaje(agrupar(datos, llaves));
}

// ¿Alguna celda de la selección quedó por debajo del umbral? Lo usa el aviso
// de muestra insuficiente que se muestra junto a la gráfica.
export function hayFragiles(filas) {
  return filas.some((f) => f.fragil);
}

// Cuántas y cuáles. Para redactar el aviso con nombres concretos en vez de una
// advertencia genérica que nadie lee.
export function resumenFragiles(filas, llaveEtiqueta = "grupo") {
  const fr = filas.filter((f) => f.fragil);
  return {
    n: fr.length,
    minCasos: fr.length ? Math.min(...fr.map((f) => f.casos)) : null,
    etiquetas: [...new Set(fr.map((f) => f[llaveEtiqueta]).filter(Boolean))],
  };
}

// Brecha en puntos porcentuales entre dos series de la misma comparación.
// Positiva = la primera serie está por encima. Devuelve null si falta alguna
// o si alguna no es calculable.
export function brecha(filas, llaveSerie, serieA, serieB) {
  const a = filas.find((f) => f[llaveSerie] === serieA);
  const b = filas.find((f) => f[llaveSerie] === serieB);
  if (!a || !b || a.pct == null || b.pct == null) return null;
  return a.pct - b.pct;
}

// Razón entre dos series ("las mujeres con discapacidad ganan 0.62 por cada
// peso que gana un hombre sin discapacidad"). null si el divisor es 0 o falta.
export function razon(filas, llaveSerie, serieA, serieB) {
  const a = filas.find((f) => f[llaveSerie] === serieA);
  const b = filas.find((f) => f[llaveSerie] === serieB);
  if (!a || !b || !b.pct) return null;
  return a.pct / b.pct;
}

// Materializa una tabla Arrow (parquet) a objetos JS planos, convirtiendo las
// columnas numéricas indicadas con Number(). Sin esto, los valores quedan como
// tipos Arrow que no suman ni comparan bien, y la tabla solo se puede iterar
// una vez.
export function materializar(tabla, numericas = ["num", "den", "casos"]) {
  return [...tabla].map((fila) => {
    const o = {...fila};
    for (const k of numericas) if (k in o) o[k] = Number(o[k]);
    return o;
  });
}

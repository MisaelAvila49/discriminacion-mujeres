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
      base._varAcum = 0;
      base._filasSinEE = 0;
      base._filas = 0;
      mapa.set(clave, base);
    }
    const acc = mapa.get(clave);
    acc.num += Number(fila.num) || 0;
    acc.den += Number(fila.den) || 0;
    acc.casos += Number(fila.casos) || 0;

    // Propagación del error al SUMAR filas (por ejemplo, las 32 entidades
    // para llegar al nacional). El error de una suma no es la suma de los
    // errores: se acumulan varianzas, es decir errores al cuadrado pesados
    // por el denominador de cada parte, y al final se vuelve a sacar raíz
    // en `conPorcentaje`.
    //
    // Esto trata las partes como independientes, lo cual NO es exacto: dos
    // entidades comparten estratos de diseño y la covarianza entre ellas se
    // pierde. El resultado subestima levemente el error del agregado. Es
    // preferible a las dos alternativas: no mostrar nada al agregar, o
    // sumar errores, que lo sobreestimaría mucho más. El error exacto del
    // nacional solo sale de recalcularlo sobre los microdatos, que es lo
    // que hacen los loaders para las combinaciones que sí emiten.
    acc._filas += 1;
    const ee = Number(fila.ee);
    const den = Number(fila.den) || 0;
    if (fila.ee == null || fila.ee === "" || !isFinite(ee)) {
      acc._filasSinEE += 1;
    } else {
      acc._varAcum += (ee * den) ** 2;
    }
  }
  return [...mapa.values()];
}

// Agrega pct = num/den y la bandera de fragilidad. pct queda null si no hay
// denominador (no es cero: es "no calculable", y una barra en cero mentiría).
// El ×100 solo aplica cuando el indicador es un porcentaje: en pesos u horas,
// num/den YA es la cifra final (pesos, horas), y multiplicarla por 100 la
// infla cien veces — $13,444 de ingreso mensual se convertía en $1,344,400.
//
// "conteo" es distinto de los demás: no es una RAZÓN de nada (num/den), es
// un CONTEO absoluto de personas (num), y `den` en ese indicador solo existe
// para que la fila conserve la forma común num/den/casos del resto del
// tablero — ahí `den` es la población nacional total, una constante que no
// varía por grupo, así que dividir por ella daría "qué fracción del país es
// este grupo" (~0.2%), no el conteo real de millones de personas que se
// quiere mostrar. Por eso "conteo" usa `num` directo, sin dividir.
export function conPorcentaje(filas, formato = "pct") {
  const escala = formato === "pct" ? 100 : 1;
  return filas.map((f) => {
    const pct = formato === "conteo" ? f.num
      : f.den > 0 ? (f.num / f.den) * escala : null;

    // Error estándar del grupo ya agregado, en la misma unidad que `pct`.
    // Solo se publica si TODAS las partes traían error: con una sola parte
    // sin estimar, el intervalo saldría más angosto de lo real y sería peor
    // que no mostrarlo. En "conteo" no se ofrece intervalo porque `pct` ahí
    // es una población expandida, no una razón.
    let ee = null;
    if (formato !== "conteo" && f.den > 0 && f._filasSinEE === 0 &&
        f._varAcum > 0) {
      ee = (Math.sqrt(f._varAcum) / f.den) * escala;
    }

    return {
      ...f,
      pct,
      ee,
      // Intervalo de confianza al 95 %, el convencional para estadística
      // oficial. Se recorta en cero porque una proporción negativa no
      // existe, y el límite superior de un porcentaje se recorta en cien.
      ic: (ee == null || pct == null) ? null : {
        lo: Math.max(formato === "pct" ? 0 : -Infinity, pct - 1.96 * ee),
        hi: formato === "pct" ? Math.min(100, pct + 1.96 * ee) : pct + 1.96 * ee,
      },
      fragil: f.casos < MIN_CASOS,
    };
  });
}

// Atajo: agrupar + porcentaje en un paso.
export function tasaPorGrupo(datos, llaves, formato = "pct") {
  return conPorcentaje(agrupar(datos, llaves), formato);
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

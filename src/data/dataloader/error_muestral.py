"""
error_muestral.py: Error estándar de una razón bajo el diseño muestral real.

Por qué hace falta. El tablero permite combinar filtros (entidad, rango de
edad, dominio de dificultad, decil), y cada filtro parte la muestra. Medido
sobre la ENIGH 2024, participación laboral de mujeres con discapacidad:

    nacional                    n=10,931   29.9%   ±0.65 pp
    + rango de edad 18 a 29        n=718   39.2%   ±2.23 pp
    + una entidad                  n=400   25.9%   ±2.45 pp
    + entidad Y rango de edad       n=23   32.3%  ±11.64 pp

La última fila tiene un intervalo de confianza de 9.5 % a 55.1 %: la cifra
no distingue nada, y hasta ahora el tablero la mostraba con una trama que
advertía "pocos casos" sin decir cuántos puntos de incertidumbre había
detrás. El 82 % de las celdas del archivo por dominio y el 55 % de las de
decil quedan por debajo de treinta casos, así que no es una situación
marginal.

Por qué NO se usa la fórmula binomial. La tentación es calcular
sqrt(p(1-p)/n), que no necesita más que el conteo. Esa fórmula supone
muestreo aleatorio simple, y la ENIGH es un diseño estratificado por
conglomerados: las personas se seleccionan por manzana (UPM), y quienes
viven en la misma manzana se parecen entre sí más de lo que se parecerían
dos personas tomadas al azar del país. El efecto de diseño medido sobre este
mismo indicador es de 2.20 a nivel nacional, es decir que la fórmula simple
subestima el error en un tercio (0.44 pp contra 0.65 pp reales). Publicar un
intervalo más angosto que el real es peor que no publicarlo.

Método. Linearización de Taylor para el estimador de razón, con varianza
entre UPM dentro de cada estrato, que es el procedimiento estándar para
encuestas complejas y el que usa el propio INEGI:

    r = sum(w_i * y_i) / sum(w_i)
    u_i = w_i * (y_i - r)
    V(r) = (1/N²) * sum_estratos [ n_h/(n_h-1) * sum_UPM (u_h - u_h_medio)² ]

Los estratos con una sola UPM no aportan varianza y se omiten: no es que su
varianza sea cero, es que con una sola unidad no se puede estimar. Cuando
eso deja la varianza en cero, la función devuelve None y el indicador viaja
sin error en vez de con un cero que se leería como certeza absoluta.

Las columnas de diseño están en los microdatos: `upm` y `est_dis` en ENIGH y
Censo, `upm` y `est_dis` en ENDIREH (donde el factor es `fac_muj`). ENADIS
2017 no publica UPM, así que ahí el error no es calculable y sus indicadores
salen sin la columna.
"""

import numpy as np
import pandas as pd


# Nombres que usan las distintas encuestas para las mismas dos variables de
# diseño. Se prueban en orden hasta encontrar las que existan.
COLS_UPM = ("upm", "UPM", "upm_dis", "UPM_DIS")
COLS_ESTRATO = ("est_dis", "EST_DIS", "estrato", "ESTRATO", "est_diseño")


def columnas_diseno(df):
    """
    Devuelve (upm, estrato) con los nombres que existan en el dataframe, o
    (None, None) si la encuesta no publica el diseño. Se resuelve por
    tanteo y no con un parámetro por loader porque el mismo estimador se
    usa desde ENIGH, ENDIREH y Censo, que nombran distinto lo mismo.
    """
    upm = next((c for c in COLS_UPM if c in df.columns), None)
    est = next((c for c in COLS_ESTRATO if c in df.columns), None)
    return upm, est


def error_razon(df, y, peso="factor", upm=None, estrato=None):
    """
    Error estándar de la razón sum(w*y)/sum(w), bajo diseño estratificado
    por conglomerados.

    `y` puede ser el nombre de una columna booleana o numérica, o una Serie
    alineada con `df`. Devuelve None cuando el error no es estimable: sin
    columnas de diseño, con menos de dos UPM en todos los estratos, o con
    denominador cero. None significa "no se pudo calcular", nunca cero.
    """
    if upm is None or estrato is None:
        upm, estrato = columnas_diseno(df)
    if upm is None or estrato is None or not len(df):
        return None

    yy = (df[y] if isinstance(y, str) else y).astype(float).values
    w = pd.to_numeric(df[peso], errors="coerce").fillna(0.0).values
    total = w.sum()
    if total <= 0:
        return None

    r = float((w * yy).sum() / total)
    aporte = pd.DataFrame({
        "_est": df[estrato].values,
        "_upm": df[upm].values,
        "_u": w * (yy - r),
    })
    # Un punto por UPM: la varianza del diseño vive entre conglomerados, no
    # entre personas.
    por_upm = aporte.groupby(["_est", "_upm"], observed=True)["_u"].sum()

    varianza = 0.0
    for _, s in por_upm.groupby(level=0, observed=True):
        n = len(s)
        if n < 2:
            continue
        varianza += n / (n - 1) * float(((s - s.mean()) ** 2).sum())

    if varianza <= 0:
        return None
    return float(np.sqrt(varianza) / total)


def agrega_error(g, base, llaves, y, peso="factor"):
    """
    Calcula el error estándar por grupo y lo pega como columna `ee` al
    dataframe ya agregado `g`.

    `base` son los microdatos sin agregar y `llaves` las columnas por las
    que se agrupó, de modo que cada fila de `g` recibe el error de su propio
    subgrupo. El error viaja en la misma unidad que la razón (proporción, no
    puntos porcentuales); el front lo multiplica junto con el valor.
    """
    upm, estrato = columnas_diseno(base)
    if upm is None or estrato is None:
        g["ee"] = np.nan
        return g

    # groupby con UNA llave entrega la llave suelta y con varias una tupla;
    # se normaliza a tupla siempre para que el emparejamiento con las filas
    # de `g` no dependa de cuántas dimensiones tenga el indicador. Sin esto
    # el caso de una sola llave devolvía NaN en todas las filas, en
    # silencio.
    errores = {}
    for llave, sub in base.groupby(llaves, dropna=True, observed=True):
        clave = llave if isinstance(llave, tuple) else (llave,)
        errores[clave] = error_razon(sub, y, peso=peso, upm=upm,
                                     estrato=estrato)

    g["ee"] = [errores.get(tuple(fila)) for fila in
               g[llaves].itertuples(index=False, name=None)]
    return g

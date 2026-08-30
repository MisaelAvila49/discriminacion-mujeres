"""
utils_enadis.py: Base compartida de los data loaders de ENADIS 2017 y 2022.

Construye la tabla de personas adultas con las dos llaves de identidad que
usa todo el tablero (sexo y discapacidad) más las dimensiones de filtro
(año, entidad, rango de edad, tipo de discapacidad).

Regla que atraviesa todo el archivo: cada indicador se reporta como
numerador ponderado / denominador ponderado, y por separado el número de
casos SIN expandir. El porcentaje se calcula al final, nunca promediando
porcentajes de subgrupos, y la suficiencia de muestra se juzga con los casos
crudos, no con la cifra expandida.

Diferencias de cuestionario entre ediciones que hay que respetar:

  - Discapacidad. Las dos ediciones NO usan la misma escala, y esto se
    verificó contra los microdatos, no contra el cuestionario:

      2017 (p4_2_1..8): escala binaria. Valores observados {1, 2},
           donde 1 = sí tiene la dificultad y 2 = no.
      2022 (p3_6_1..8): escala de severidad de cuatro puntos. Valores
           observados {1, 2, 3, 4, 9}, donde 1 = "no puede hacerlo",
           2 = "mucha dificultad", 3 = "poca dificultad", 4 = "sin
           dificultad" y 9 = no especificado.

    Por eso el criterio de positividad es distinto por año: {1} en 2017 y
    {1, 2} en 2022. Aplicar {1, 2} a 2017 contaría como discapacidad
    justamente a quienes respondieron "no", y duplicaría la prevalencia.
    Con el criterio correcto la prevalencia en población de 18 años o más
    queda en 6.11% (2017) y 6.44% (2022), cifras del orden que publica el
    INEGI y comparables entre sí.

    Consecuencia para la lectura: la serie 2017-2022 es indicativa, no una
    medición estrictamente homogénea. Un cambio de uno o dos puntos entre
    ediciones puede venir del instrumento y no de la realidad. Las
    comparaciones ENTRE grupos dentro de un mismo año sí son limpias, y son
    las que sostienen el tablero.

  - Factor de expansión de la tabla sociodemográfica: `factor` en 2017,
    `fac_per` en 2022.
"""

import os
import pandas as pd

# Los microdatos crudos no se versionan (pesan y son públicos). Se leen de la
# carpeta local del analista; ver README para la ruta de descarga del INEGI.
BASE_ENADIS = os.environ.get(
    "ENADIS_DIR",
    r"Z:\SocialDataIbero\AnalisisSueltos\Enadis",
)

ANIOS = [2017, 2022]

# --- Nivel de desagregación admisible ---------------------------------------
# ENADIS tiene representatividad NACIONAL únicamente: su diseño muestral no
# está construido para estimaciones por entidad federativa. Esto no se detecta
# contando casos (hay entre 53 y 147 casos por entidad en el cruce de mujeres
# con discapacidad, todos por encima del umbral de 30), y por eso es una
# trampa: las cifras estatales se ven perfectamente sólidas y no lo son. La
# diferencia entre Coahuila (9.4%) y Quintana Roo (23.4%) en ocupación de
# mujeres con discapacidad es ruido de diseño, no un hallazgo.
#
# La columna `entidad` se conserva en la salida porque el tablero la usa para
# construir el agregado nacional, pero NINGUNA página debe ofrecer ENADIS
# desagregada por entidad. El mapa y el ranking estatal salen del Censo 2020,
# que sí es representativo a nivel municipal y estatal.
NIVEL_MAXIMO = "nacional"

ENTIDADES = {
    1: "Aguascalientes", 2: "Baja California", 3: "Baja California Sur",
    4: "Campeche", 5: "Coahuila", 6: "Colima", 7: "Chiapas", 8: "Chihuahua",
    9: "Ciudad de México", 10: "Durango", 11: "Guanajuato", 12: "Guerrero",
    13: "Hidalgo", 14: "Jalisco", 15: "México", 16: "Michoacán",
    17: "Morelos", 18: "Nayarit", 19: "Nuevo León", 20: "Oaxaca",
    21: "Puebla", 22: "Querétaro", 23: "Quintana Roo", 24: "San Luis Potosí",
    25: "Sinaloa", 26: "Sonora", 27: "Tabasco", 28: "Tamaulipas",
    29: "Tlaxcala", 30: "Veracruz", 31: "Yucatán", 32: "Zacatecas",
}

# Los ocho dominios de dificultad del cuestionario, en el orden en que vienen
# numerados. Se conservan por separado para el filtro de tipo de discapacidad.
TIPOS_DISC = [
    "Ver", "Oír", "Caminar", "Recordar o concentrarse",
    "Bañarse o vestirse", "Hablar o comunicarse", "Mental", "Brazos o manos",
]

# Rangos de edad. El corte a los 60 separa a la población en edad de trabajar
# de la adulta mayor, donde la prevalencia de discapacidad se dispara y
# mezclarla borraría el efecto que se quiere medir.
RANGOS_EDAD = [
    (18, 29, "18-29"),
    (30, 44, "30-44"),
    (45, 59, "45-59"),
    (60, 200, "60+"),
]


def _ruta(year, tabla):
    return os.path.join(BASE_ENADIS, f"Enadis{year}", "Bases", f"{tabla}_{year}.csv")


def cargar(year, tabla):
    """Lee una tabla de ENADIS con las columnas en minúsculas."""
    df = pd.read_csv(_ruta(year, tabla), encoding="latin-1", low_memory=False)
    df.columns = df.columns.str.lower().str.strip()
    return df


def _rango_edad(edad):
    for lo, hi, etiqueta in RANGOS_EDAD:
        if lo <= edad <= hi:
            return etiqueta
    return None


def preparar_sdem(year):
    """
    Tabla sociodemográfica de personas de 18 años o más, con sexo,
    discapacidad (global y por tipo), entidad, rango de edad y factor.

    Es el denominador de casi todo el tablero: cualquier módulo temático se
    une contra esta tabla para heredar las llaves de identidad.
    """
    sdem = cargar(year, "tsdem")

    # --- Discapacidad -------------------------------------------------------
    # Ver la nota del encabezado: las escalas difieren entre ediciones y el
    # criterio de positividad NO es intercambiable.
    if year == 2017:
        cols_disc = [f"p4_2_{i}" for i in range(1, 9)]
        positivos = [1]          # binaria: 1 = sí, 2 = no
    else:
        cols_disc = [f"p3_6_{i}" for i in range(1, 9)]
        positivos = [1, 2]       # severidad: "no puede" + "mucha dificultad"

    presentes = [c for c in cols_disc if c in sdem.columns]
    if not presentes:
        raise KeyError(
            f"ENADIS {year}: no se encontraron las columnas de discapacidad "
            f"{cols_disc}. Revisa que la base sea la edición correcta."
        )

    marca = sdem[presentes].isin(positivos)
    sdem["discapacidad"] = marca.any(axis=1)
    sdem["disc"] = sdem["discapacidad"].map(
        {True: "Con discapacidad", False: "Sin discapacidad"}
    )
    # Una columna booleana por tipo, para el filtro de tipo de discapacidad.
    # Una misma persona puede tener varias: son categorías NO excluyentes, y
    # por eso el total por tipo no suma al total de personas con discapacidad.
    for i, col in enumerate(presentes):
        sdem[f"disc_tipo_{i}"] = sdem[col].isin(positivos)

    # --- Sexo, edad, entidad ------------------------------------------------
    sdem["sexo"] = sdem["sexo"].map({1: "Hombres", 2: "Mujeres"})
    sdem["edad"] = pd.to_numeric(sdem["edad"], errors="coerce")
    sdem["entidad"] = sdem["ent"].map(ENTIDADES).fillna("No especificado")

    # El factor de expansión cambia de nombre entre ediciones: en 2017 la
    # tabla sociodemográfica lo trae como `factor` y en 2022 como `fac_per`.
    factor_col = next(
        (c for c in ("fac_per", "factor_per", "factor") if c in sdem.columns), None
    )
    if factor_col is None:
        raise KeyError(f"ENADIS {year}: no se encontró el factor de expansión.")
    sdem["factor"] = pd.to_numeric(sdem[factor_col], errors="coerce").fillna(0)

    # Población objetivo del tablero: adultos. Los módulos de niñez y
    # adolescencia viven en el sitio hermano y tienen otro cuestionario.
    sdem = sdem[sdem["edad"] >= 18].copy()
    sdem["rango_edad"] = sdem["edad"].apply(_rango_edad)
    sdem = sdem.dropna(subset=["sexo", "rango_edad"])

    sdem["anio"] = year
    return sdem


# --- Mapa de preguntas por edición ------------------------------------------
# El cuestionario se renumeró entre 2017 y 2022: el mismo concepto vive en
# columnas distintas, y peor, una misma columna cambia de significado. `p3_18`
# es alfabetismo en 2022 pero un seguimiento del bloque laboral en 2017.
# Por eso NUNCA se busca una columna por nombre directo: se pide el concepto y
# este mapa resuelve la columna del año. Si un concepto no existe en una
# edición, se declara None explícitamente y el indicador se omite con aviso,
# en vez de desaparecer en silencio.
#
# Numeración verificada contra los prontuarios oficiales del INEGI
# (Prontuario2017.ipynb y Prontuario2022.ipynb).
PREGUNTAS = {
    2017: {
        "alfabetismo": "p3_14",       # ¿sabe leer y escribir?
        "condicion_actividad": "p3_17",  # ¿la semana pasada...?
        "asistencia_escolar": None,   # no disponible en la tabla sdem 2017
    },
    2022: {
        "alfabetismo": "p3_18",
        "condicion_actividad": "p3_21",
        "asistencia_escolar": "p3_19",
    },
}


def col(year, concepto, sdem=None):
    """
    Devuelve el nombre de columna de un concepto en la edición dada.

    Falla ruidosamente si el concepto no está registrado o si la columna que
    el mapa promete no existe en los datos: un indicador que se calcula sobre
    la columna equivocada es peor que un indicador que no se calcula.
    """
    if concepto not in PREGUNTAS[year]:
        raise KeyError(f"Concepto '{concepto}' no registrado para ENADIS {year}.")
    nombre = PREGUNTAS[year][concepto]
    if nombre is None:
        return None
    if sdem is not None and nombre not in sdem.columns:
        raise KeyError(
            f"ENADIS {year}: se esperaba la columna '{nombre}' para "
            f"'{concepto}' y no está en los datos. Revisa PREGUNTAS."
        )
    return nombre


LLAVES_UNION = ["upm", "viv_sel", "hogar", "n_ren"]


def unir_con_sdem(df, sdem):
    """
    Une un módulo temático con la tabla sociodemográfica para heredar sexo,
    discapacidad, entidad, rango de edad y factor.

    Las llaves se normalizan a texto sin espacios en ambos lados: vienen como
    enteros en una tabla y como texto con ceros a la izquierda en otra, y una
    unión sin normalizar pierde filas en silencio.
    """
    cols = LLAVES_UNION + [
        "sexo", "disc", "entidad", "rango_edad", "edad", "factor", "anio",
    ] + [c for c in sdem.columns if c.startswith("disc_tipo_")]

    izq = df.copy()
    der = sdem[cols].copy()

    # Los módulos temáticos traen su propia copia de algunas columnas
    # sociodemográficas (tadulto, por ejemplo, ya incluye `sexo`). Sin quitarlas
    # antes de unir, pandas las renombra a sexo_x y sexo_y y la agregación
    # posterior falla con KeyError buscando `sexo`. La versión que manda es
    # siempre la de TSDEM, que es donde se construyeron las llaves de identidad.
    duplicadas = [c for c in der.columns
                  if c not in LLAVES_UNION and c in izq.columns]
    if duplicadas:
        izq = izq.drop(columns=duplicadas)

    for k in LLAVES_UNION:
        izq[k] = izq[k].astype(str).str.strip()
        der[k] = der[k].astype(str).str.strip()

    antes = len(izq)
    out = izq.merge(der, on=LLAVES_UNION, how="inner")
    if antes and len(out) / antes < 0.5:
        raise ValueError(
            f"La unión con TSDEM conservó {len(out)} de {antes} filas "
            "(menos de la mitad). Revisa las llaves antes de publicar."
        )
    return out


def indicador(df, condicion, tema, indicador_nombre, fuente,
              universo="Personas de 18 años o más"):
    """
    Convierte una condición booleana en filas largas listas para el tablero.

    Devuelve una fila por cada combinación de las dimensiones de filtro, con
    numerador y denominador ponderados y el conteo de casos sin expandir. El
    porcentaje NO se calcula aquí: se calcula en el navegador después de
    sumar, para que agregar entidades o rangos de edad nunca promedie tasas.

    `condicion` es una Serie booleana alineada con df. Los no especificados
    deben quedar fuera del denominador antes de llamar a esta función, no
    contarse como "no".
    """
    d = df.copy()
    d["_num"] = condicion.fillna(False).astype(bool)

    llaves = ["anio", "sexo", "disc", "entidad", "rango_edad"]
    g = d.groupby(llaves, dropna=True, observed=True)

    out = g.apply(
        lambda x: pd.Series({
            "num": float(x.loc[x["_num"], "factor"].sum()),
            "den": float(x["factor"].sum()),
            "casos": int(len(x)),
        }),
        include_groups=False,
    ).reset_index()

    out["tema"] = tema
    out["indicador"] = indicador_nombre
    out["fuente"] = fuente
    out["universo"] = universo
    return out


def escribir(dfs):
    """
    Concatena los indicadores y los imprime como CSV a stdout.

    La salida se fuerza a UTF-8: en Windows la codificación por defecto de
    stdout es cp1252 y los nombres de entidad con acento (Michoacán,
    Querétaro, México) llegan rotos al navegador.
    """
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", newline="")

    todo = pd.concat(dfs, ignore_index=True)
    # tipo_discapacidad y decil son opcionales: por ahora solo ENIGH los
    # produce (ver enigh.csv.py, explotar_dimensiones). Los loaders que
    # todavía no los tienen quedan en "Todos", que es exactamente su
    # comportamiento de hoy sin desagregar por dominio ni por decil — así
    # este cambio no les rompe nada.
    if "tipo_discapacidad" not in todo.columns:
        todo["tipo_discapacidad"] = "Todos"
    todo["tipo_discapacidad"] = todo["tipo_discapacidad"].fillna("Todos")
    if "decil" not in todo.columns:
        todo["decil"] = "Todos"
    todo["decil"] = todo["decil"].fillna("Todos")
    columnas = [
        "tema", "indicador", "anio", "sexo", "disc", "entidad", "rango_edad",
        "tipo_discapacidad", "decil", "num", "den", "casos", "fuente", "universo",
    ]
    todo = todo[columnas]
    todo.to_csv(sys.stdout, index=False)

"""
enigh.csv.py: Indicadores de trabajo e ingreso de la ENIGH.

Cubre 2020, 2022 y 2024, que son las ediciones cuya tabla de población trae
las ocho columnas de discapacidad. Las ediciones 2016 y 2018 están en disco
pero solo con `concentradohogar` e `ingresos`: sin tabla de población no hay
forma de cruzar sexo con discapacidad a nivel persona, así que quedan fuera.
Incluirlas produciría una serie que cambia de universo a la mitad.

Emite la misma tabla larga que el resto de los data loaders: numerador y
denominador ponderados más casos sin expandir, por año, sexo, discapacidad,
entidad, rango de edad y decil de ingreso.

Notas de los microdatos, verificadas contra las bases:
  - Discapacidad (`disc_*`): escala de severidad de cuatro puntos, igual que
    ENADIS 2022, con "&" como no aplica/no especificado. Se cuenta como
    discapacidad el 1 ("no puede hacerlo") y el 2 ("mucha dificultad"), que
    es el criterio del INEGI y el mismo que usa el loader de ENADIS.
  - `factor` es el factor de expansión de persona.
  - La entidad NO viene como columna: son los dos primeros dígitos de
    `folioviv`, que hay que leer con ceros a la izquierda.
  - `ing_cor` (en `concentradohogar`) es el ingreso corriente TRIMESTRAL del
    hogar, no anual (mediana ~$46,074 por hogar en 2022, consistente con esa
    unidad). `tot_integ` es el número de integrantes del hogar. Ambos se usan
    para el decil de ingreso per cápita (ver `_calcular_decil`).
"""

import sys
import os
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils_enadis import ENTIDADES, RANGOS_EDAD, TIPOS_DISC, escribir  # noqa: E402
import deflactor  # noqa: E402

BASE_ENIGH = os.environ.get(
    "ENIGH_DIR",
    r"Z:\SocialDataIbero\AnalisisSueltos\Obindi\enigh",
)

# Solo las ediciones con tabla de población (ver encabezado).
ANIOS_ENIGH = [2020, 2022, 2024]

COLS_DISC = [
    "disc_ver", "disc_oir", "disc_camin", "disc_brazo",
    "disc_apren", "disc_vest", "disc_habla", "disc_acti",
]

# Etiqueta de cada columna, en el mismo vocabulario que TIPOS_DISC de ENADIS
# (utils_enadis.py) para que "tipo de discapacidad" signifique lo mismo en
# las dos encuestas aunque el orden de las columnas en el cuestionario sea
# distinto. Mapeo por significado del dominio, no por posición:
#   disc_acti (dificultad para actividades cotidianas) = dominio "Mental" de
#   ENADIS, que en ese cuestionario también agrupa lo mental/emocional.
ETIQUETA_TIPO_DISC = {
    "disc_ver": "Ver",
    "disc_oir": "Oír",
    "disc_camin": "Caminar",
    "disc_brazo": "Brazos o manos",
    "disc_apren": "Recordar o concentrarse",
    "disc_vest": "Bañarse o vestirse",
    "disc_habla": "Hablar o comunicarse",
    "disc_acti": "Mental",
}
assert set(ETIQUETA_TIPO_DISC.values()) == set(TIPOS_DISC), (
    "ETIQUETA_TIPO_DISC debe usar exactamente el vocabulario de TIPOS_DISC "
    "(utils_enadis.py) para que el filtro de tipo signifique lo mismo en "
    "ENIGH y ENADIS."
)

# --- Escala de discapacidad: NO es la misma en todas las ediciones ----------
# Verificado contando frecuencias en los microdatos, no leyendo el diccionario:
#
#   2020 y 2022: el código dominante es 4 (290,280 casos en disc_ver 2020),
#     es decir la escala va 1 = "no puede hacerlo" ... 4 = "sin dificultad".
#     Positivos = {1, 2}.
#   2024: el código dominante es 1 (269,718 casos), o sea INEGI invirtió la
#     escala: 1 = "sin dificultad" ... 4 = "no puede hacerlo".
#     Positivos = {3, 4}.
#
# Aplicar {1, 2} a 2024 clasifica como "con discapacidad" a la población sin
# ninguna dificultad: da 115 mil personas con discapacidad y 294 sin ella, un
# resultado absurdo que además invierte todos los indicadores. El error no es
# hipotético: esta primera versión lo produjo.
DISC_POSITIVOS_POR_ANIO = {
    2020: {"1", "2"},
    2022: {"1", "2"},
    2024: {"3", "4"},
}


def _rango_edad(edad):
    for lo, hi, etiqueta in RANGOS_EDAD:
        if lo <= edad <= hi:
            return etiqueta
    return None


def _calcular_decil(ing_cor_percapita, factor):
    """
    Decil ponderado de una serie de ingreso per cápita del hogar, usando el
    factor de expansión. Devuelve una Serie de enteros 1-10 alineada con la
    entrada (1 = 10% más pobre, 10 = 10% más rico), calculado por corte de
    percentiles ponderados de la distribución NACIONAL de ESE año — nunca se
    deflacta entre ediciones porque el decil es un ranking dentro del propio
    año, no una comparación de montos (ver docstring del módulo).

    Se ordena por ingreso, se acumula el factor, y se corta en los diez
    percentiles de masa ponderada equivalente (10%, 20%... 90%). Con
    ~90 mil hogares por edición los empates en el corte son marginales; no
    hace falta un método más sofisticado que ordenar y acumular.
    """
    orden = ing_cor_percapita.sort_values().index
    factor_ordenado = factor.loc[orden]
    acumulado = factor_ordenado.cumsum()
    total = factor_ordenado.sum()
    # corte[i] es la masa acumulada al final del decil i (i=1..10).
    cortes = [total * i / 10 for i in range(1, 11)]
    decil_ordenado = pd.Series(1, index=orden)
    for i, corte in enumerate(cortes[:-1], start=1):
        decil_ordenado[acumulado > corte] = i + 1
    return decil_ordenado.reindex(ing_cor_percapita.index)


def cargar_poblacion(year):
    ruta = os.path.join(BASE_ENIGH, f"Bases{year}", f"poblacion{year}.csv")
    df = pd.read_csv(ruta, low_memory=False, dtype={"folioviv": str})
    # El BOM del archivo se pega a la primera columna y rompe `folioviv`.
    df.columns = (df.columns.str.replace("\ufeff", "", regex=False)
                  .str.lower().str.strip())

    # --- Identidad ---------------------------------------------------------
    # Codificación del INEGI: 1 = hombre, 2 = mujer. Se confirmó con las
    # frecuencias (el código 2 es mayoritario, ~51%, consistente con la
    # composición por sexo del país).
    df["sexo"] = df["sexo"].map({1: "Hombres", 2: "Mujeres"})

    presentes = [c for c in COLS_DISC if c in df.columns]
    if len(presentes) < len(COLS_DISC):
        raise KeyError(
            f"ENIGH {year}: faltan columnas de discapacidad "
            f"{set(COLS_DISC) - set(presentes)}."
        )
    if year not in DISC_POSITIVOS_POR_ANIO:
        raise KeyError(
            f"ENIGH {year}: no está registrada la orientación de la escala de "
            "discapacidad. Revisa las frecuencias antes de agregar el año."
        )
    positivos = DISC_POSITIVOS_POR_ANIO[year]
    marca = df[presentes].astype(str).apply(lambda s: s.str.strip().isin(positivos))
    df["disc"] = marca.any(axis=1).map(
        {True: "Con discapacidad", False: "Sin discapacidad"}
    )

    # Una columna booleana por dominio, no excluyentes entre sí (una persona
    # puede tener dificultad para ver Y para caminar). Mismo patrón que
    # preparar_sdem() en utils_enadis.py, para que el filtro de tipo de
    # discapacidad exista igual en ENIGH y ENADIS.
    for c in presentes:
        df[f"disc_tipo_{ETIQUETA_TIPO_DISC[c]}"] = marca[c]

    # Guardia de sanidad: la prevalencia de discapacidad en población adulta
    # ronda el 5-15% según el instrumento. Si sale fuera de ese rango, casi
    # siempre significa que la escala está invertida para ese año. Vale más
    # detener el build que publicar un tablero con los grupos intercambiados.
    prev = marca.any(axis=1).mean() * 100
    if not 2 <= prev <= 25:
        raise ValueError(
            f"ENIGH {year}: prevalencia de discapacidad de {prev:.1f}%, fuera "
            f"del rango plausible. Revisa la orientación de la escala "
            f"(positivos usados: {sorted(positivos)})."
        )

    # --- Dimensiones de filtro ---------------------------------------------
    # La entidad son los dos primeros dígitos de folioviv. Sin zfill, los
    # folios de las entidades 1 a 9 pierden el cero inicial y todas las
    # cifras de esos estados se van al estado equivocado.
    df["cve_ent"] = df["folioviv"].astype(str).str.zfill(10).str[:2].astype(int)
    df["entidad"] = df["cve_ent"].map(ENTIDADES).fillna("No especificado")

    df["edad"] = pd.to_numeric(df["edad"], errors="coerce")

    # concentradohogar aporta dos cosas: el `factor` de persona cuando falta
    # (solo 2020, que lo hereda a nivel hogar) y SIEMPRE `ing_cor`/`tot_integ`
    # para calcular el decil de ingreso (ver _calcular_decil más abajo). Antes
    # este merge era condicional a que faltara `factor`; ahora es incondicional
    # porque el decil se necesita en las 3 ediciones.
    ruta_hog = os.path.join(
        BASE_ENIGH, f"Bases{year}", f"concentradohogar{year}.csv")
    hog = pd.read_csv(ruta_hog, low_memory=False, dtype={"folioviv": str})
    hog.columns = (hog.columns.str.replace("﻿", "", regex=False)
                   .str.lower().str.strip())
    for c in ("factor", "ing_cor", "tot_integ"):
        if c not in hog.columns:
            raise KeyError(
                f"ENIGH {year}: falta la columna '{c}' en concentradohogar."
            )
    for k in ("folioviv", "foliohog"):
        df[k] = df[k].astype(str).str.strip()
        hog[k] = hog[k].astype(str).str.strip()
    antes = len(df)

    tiene_factor_persona = "factor" in df.columns
    cols_hog = ["folioviv", "foliohog", "ing_cor", "tot_integ"]
    if not tiene_factor_persona:
        cols_hog.append("factor")
    df = df.merge(hog[cols_hog], on=["folioviv", "foliohog"], how="left")

    sin_datos_hog = df["ing_cor"].isna().sum()
    if sin_datos_hog:
        raise ValueError(
            f"ENIGH {year}: {sin_datos_hog} de {antes} personas quedaron sin "
            "datos de concentradohogar (ing_cor) tras la unión."
        )

    df["factor"] = pd.to_numeric(df["factor"], errors="coerce").fillna(0)

    # --- Decil de ingreso ---------------------------------------------------
    # Per cápita del hogar: ing_cor (ya trimestral, ver docstring) entre
    # tot_integ. Es el criterio oficial del INEGI para deciles de ingreso —
    # ajusta por tamaño de hogar, a diferencia de usar ing_cor sin dividir.
    df["ing_cor"] = pd.to_numeric(df["ing_cor"], errors="coerce")
    df["tot_integ"] = pd.to_numeric(df["tot_integ"], errors="coerce")
    df["_ing_percapita"] = df["ing_cor"] / df["tot_integ"]

    # Guardia de completitud, aparte de la de ing_cor de arriba: si tot_integ
    # viniera nulo o en cero en una futura edición (ing_cor por sí solo ya se
    # verificó y no lo detectaría), _ing_percapita sale NaN/inf, y
    # sort_values() manda esos casos al final — _calcular_decil los
    # clasificaría en silencio como decil 10 (el más rico), un sesgo real que
    # la guardia de participación de abajo NO garantiza atrapar (una
    # contaminación de hasta ~5% del decil 10 todavía cabe dentro de su
    # tolerancia 5%-15%). Se verifica aquí, antes de calcular el decil, en vez
    # de confiar en que la guardia de participación lo detecte después.
    sin_percapita = (~df["_ing_percapita"].notna() | (df["tot_integ"] <= 0)).sum()
    if sin_percapita:
        raise ValueError(
            f"ENIGH {year}: {sin_percapita} personas quedaron sin ingreso per "
            "cápita calculable (tot_integ nulo, cero, o ing_cor no numérico). "
            "Revisa las columnas de concentradohogar antes de continuar."
        )

    df["decil"] = _calcular_decil(df["_ing_percapita"], df["factor"])

    # Guardia de sanidad: cada decil debe concentrar ~10% de la población
    # ponderada. Un decil muy chico o muy grande indicaría un error en el
    # cálculo (por ejemplo, ing_cor sin convertir a numérico, o un corte mal
    # indexado). Tolerancia amplia (5%-15%) porque los deciles no son
    # exactamente iguales por los empates en el corte.
    participacion = (df.groupby("decil")["factor"].sum() / df["factor"].sum() * 100)
    fuera_de_rango = participacion[(participacion < 5) | (participacion > 15)]
    if len(fuera_de_rango):
        raise ValueError(
            f"ENIGH {year}: decil(es) {fuera_de_rango.index.tolist()} concentran "
            f"{fuera_de_rango.round(1).to_dict()}% de la población, fuera del "
            "rango 5%-15% esperado. Revisa el cálculo de _calcular_decil."
        )

    df = df[df["edad"] >= 18].copy()
    df["rango_edad"] = df["edad"].apply(_rango_edad)
    df = df.dropna(subset=["sexo", "rango_edad"])
    df["anio"] = year
    return df


COLS_TIPO_DISC = [f"disc_tipo_{v}" for v in ETIQUETA_TIPO_DISC.values()]


def explotar_tipo_discapacidad(df):
    """
    Convierte las columnas `disc_tipo_*` (una por dominio, no excluyentes) en
    una sola dimensión larga `tipo_discapacidad`, lista para entrar al mismo
    groupby que las demás llaves.

    Cada persona CON discapacidad produce una fila por cada dominio en el que
    tiene dificultad (puede ser más de uno) MÁS una fila con
    tipo_discapacidad="Todos" que reproduce el indicador sin desagregar — es
    el comportamiento de hoy, así que un panel que deja el filtro en "Todos"
    ve exactamente lo mismo que antes de este cambio.
    Cada persona SIN discapacidad produce solo la fila "Todos": no tiene
    dominio que reportar, y agregarla a cada dominio inflaría el denominador
    de "sin discapacidad" en la vista por dominio sin ninguna razón real.

    OJO al usar esto antes de un groupby por persona (num = suma de factor):
    una persona con 3 dominios aporta 3 filas a "Todos" + 3 filas propias, así
    que "Todos" tiene que construirse ANTES de explotar, no sumando las filas
    por dominio (por eso esta función agrega la fila "Todos" explícita en vez
    de dejar que el groupby posterior la reconstruya).
    """
    presentes = [c for c in COLS_TIPO_DISC if c in df.columns]
    if not presentes:
        raise KeyError(
            "explotar_tipo_discapacidad: no hay columnas disc_tipo_* en el "
            "dataframe. ¿Se llamó antes de cargar_poblacion()?"
        )

    todos = df.copy()
    todos["tipo_discapacidad"] = "Todos"

    con_disc = df[df["disc"] == "Con discapacidad"]
    partes_dominio = []
    for c in presentes:
        etiqueta = c.replace("disc_tipo_", "")
        sub = con_disc[con_disc[c]].copy()
        if sub.empty:
            continue
        sub["tipo_discapacidad"] = etiqueta
        partes_dominio.append(sub)

    return pd.concat([todos] + partes_dominio, ignore_index=True)


def cargar_ingresos_laborales(year):
    """
    Ingreso mensual por trabajo a nivel persona.

    La tabla `ingresos` viene en formato largo: una fila por clave de ingreso
    y hasta seis meses de captación. Las claves P001 a P009 son ingresos por
    trabajo subordinado e independiente. Se promedia sobre los meses con
    captación para llegar a un mensual comparable.
    """
    ruta = os.path.join(BASE_ENIGH, f"Bases{year}", f"ingresos{year}.csv")
    ing = pd.read_csv(ruta, low_memory=False, dtype={"folioviv": str})
    ing.columns = (ing.columns.str.replace("\ufeff", "", regex=False)
                   .str.lower().str.strip())

    ing = ing[ing["clave"].astype(str).str.upper().str.match(r"^P00[1-9]$", na=False)]
    if ing.empty:
        return None

    cols_mes = [c for c in ing.columns if c.startswith("ing_")]
    for c in cols_mes:
        ing[c] = pd.to_numeric(ing[c], errors="coerce")

    # Promedio mensual: total captado entre los meses con dato. Dividir
    # siempre entre 6 subestimaría a quien solo reportó algunos meses.
    validos = ing[cols_mes].notna().sum(axis=1).replace(0, pd.NA)
    ing["ing_mensual"] = ing[cols_mes].sum(axis=1) / validos

    llaves = ["folioviv", "foliohog", "numren"]
    for k in llaves:
        ing[k] = ing[k].astype(str).str.strip()

    return (ing.groupby(llaves, dropna=False)["ing_mensual"]
            .sum().reset_index())


def indicadores(pob, ing, year):
    # Sin el año: lo aporta el filtro de edición.
    fuente = "ENIGH (INEGI)"
    llaves = ["anio", "sexo", "disc", "entidad", "rango_edad", "tipo_discapacidad"]
    pob = explotar_tipo_discapacidad(pob)
    filas = []

    # --- Participación en el trabajo remunerado ----------------------------
    # `trabajo_mp` = 1 si la persona trabajó al menos una hora en el mes de
    # referencia. El blanco es "no aplica" (menores del corte) y sale del
    # denominador en vez de contarse como "no trabajó".
    if "trabajo_mp" in pob.columns:
        base = pob[pob["trabajo_mp"].astype(str).str.strip().isin(["1", "2"])].copy()
        base["_num"] = base["trabajo_mp"].astype(str).str.strip().eq("1")
        g = base.groupby(llaves, dropna=True, observed=True).apply(
            lambda x: pd.Series({
                "num": float(x.loc[x["_num"], "factor"].sum()),
                "den": float(x["factor"].sum()),
                "casos": int(len(x)),
            }), include_groups=False).reset_index()
        g["tema"] = "trabajo"
        g["indicador"] = "Participación en el trabajo remunerado"
        g["fuente"] = fuente
        g["universo"] = "Personas de 18 años o más"
        filas.append(g)

    # --- Ingreso laboral promedio ------------------------------------------
    # Este indicador NO es un porcentaje: `num` es la masa de ingreso
    # ponderada y `den` la población ocupada ponderada, de modo que num/den
    # es el ingreso promedio en pesos. La misma división que usa el resto del
    # tablero da aquí un peso mensual en vez de un por ciento, y por eso la
    # página lo formatea distinto. Se calcula solo sobre quienes perciben
    # ingreso laboral: incluir ceros de la población no ocupada mezclaría la
    # brecha de participación con la brecha salarial, que son dos cosas.
    if ing is not None:
        p = pob.copy()
        for k in ["folioviv", "foliohog", "numren"]:
            p[k] = p[k].astype(str).str.strip()
        p = p.merge(ing, on=["folioviv", "foliohog", "numren"], how="left")
        con_ing = p[p["ing_mensual"].fillna(0) > 0].copy()

        # A pesos constantes ANTES de ponderar. Cada edición viene en pesos
        # nominales de su propio año, así que sin esto la serie mezcla
        # unidades: el ingreso "creció" 56% de 2020 a 2024 y casi todo era
        # inflación. El factor es común dentro del año, de modo que las
        # brechas y razones no cambian; lo que se corrige son los niveles.
        defl = deflactor.factor(year)
        con_ing["ing_mensual"] = con_ing["ing_mensual"] * defl

        con_ing["_masa"] = con_ing["ing_mensual"] * con_ing["factor"]

        g = con_ing.groupby(llaves, dropna=True, observed=True).apply(
            lambda x: pd.Series({
                "num": float(x["_masa"].sum()),
                "den": float(x["factor"].sum()),
                "casos": int(len(x)),
            }), include_groups=False).reset_index()
        g["tema"] = "trabajo"
        g["indicador"] = "Ingreso laboral mensual promedio"
        g["fuente"] = fuente
        g["universo"] = "Personas de 18 años o más con ingreso por trabajo"
        filas.append(g)

    return filas


def main():
    filas = []
    for year in ANIOS_ENIGH:
        pob = cargar_poblacion(year)
        ing = cargar_ingresos_laborales(year)
        filas.extend(indicadores(pob, ing, year))
        print(f"[ok] ENIGH {year}: {len(pob):,} personas", file=sys.stderr)

    if not filas:
        raise SystemExit("No se generó ningún indicador de ENIGH.")
    escribir(filas)


if __name__ == "__main__":
    main()

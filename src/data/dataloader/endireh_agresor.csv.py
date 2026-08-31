"""
endireh_agresor.csv.py: Quién ejerce la violencia, por su relación con ella.

Complementa a endireh_ambito.csv.py. Ese loader dice EN QUÉ ÁMBITO ocurre la
violencia; este dice QUIÉN la ejerce dentro de cada ámbito: el padre, la
pareja, el patrón, un maestro, un compañero.

Para el argumento del tablero la diferencia es sustantiva. Que una mujer con
discapacidad viva más violencia familiar ya dice algo; que la ejerza quien la
cuida —el padre, la madre, el hijo, la pareja de quien depende para bañarse,
comer o salir— dice por qué denunciar es tan difícil y por qué salir del
hogar no siempre es una opción disponible. La relación con el agresor es,
para esta población, la variable que separa un dato de un diagnóstico.

--- Cómo pregunta la ENDIREH por el agresor -------------------------------

No hay una sola columna "quién fue". Por CADA acto de violencia (te insultó,
te empujó, te vigiló...) la encuesta admite hasta TRES agresores, en columnas
separadas con el patrón `P{sección}_{pregunta}_{acto}_{n}`, donde `n` va de 1
a 3. Verificado en los microdatos 2021:

  Ámbito familiar (TB_SEC_XI)    60 columnas de agresor  (P11_2_*_1..3)
  Ámbito laboral  (TB_SEC_VIII) 114 columnas             (P8_*_*_1..3)
  Ámbito escolar  (TB_SEC_VII)  108 columnas             (P7_*_*_1..3)

Este loader las APLANA: una mujer cuenta como "violentada por su padre" si el
código de padre aparece en cualquiera de las columnas de agresor de su
ámbito, sin importar en qué acto ni en qué posición. La cifra se lee como
"porcentaje de mujeres que sufrieron violencia de esta persona en los últimos
12 meses", no como número de incidentes: una mujer agredida por su padre en
cinco actos distintos cuenta una vez, no cinco.

Consecuencia importante: los porcentajes de un mismo ámbito NO suman 100 ni
suman la prevalencia del ámbito. Una misma mujer puede haber sido violentada
por su padre Y por su hermano, y aparece en ambas barras. La pregunta que
responde cada barra es "¿qué proporción de mujeres sufrió violencia de esta
persona?", no "¿qué reparto tiene el total de la violencia?".

--- El ámbito de pareja no entra aquí, y no es un olvido ------------------

En los ámbitos familiar, laboral y escolar la pregunta "¿quién?" tiene
sentido porque hay muchas personas posibles. En el ámbito de pareja el
agresor ES la pareja por definición: la sección XIV no trae catálogo de
agresor, y no lo trae porque no hay nada que preguntar. La violencia de
pareja ya está publicada como ámbito en endireh_ambito.csv.py.

--- Universo: el mismo criterio que el loader de ámbitos ------------------

Cada ámbito tiene su propia población expuesta, y quien no lo está queda
FUERA del denominador, no contada como "sin violencia":

  familiar   todas las mujeres (todas tienen o tuvieron familia)
  laboral    solo quienes trabajaron en los últimos 12 meses (POB_L_12M = 1)
  escolar    solo quienes asistieron a la escuela   (POB_E_12M = 1)

Códigos verificados contra los catálogos oficiales de cada sección y contra
las frecuencias reales, no contra el nombre de la columna:

  familiar  01 Padre · 02 Madre · 03 Padrastro/madrastra · 04 Abuelo(a) ·
            05 Hijo(a) · 06 Hermano(a) · 07 Tío(a) · 08 Primo(a) ·
            09 Suegro(a) · 10 Cuñado(a) · 11 Sobrino(a) · 12 Yerno ·
            13 Otro familiar
  laboral   1 Patrón(a) o jefe(a) · 2 Supervisor(a) · 3 Gerente o directivo ·
            4 Compañero(a) · 5 Cliente · 6 Persona desconocida del trabajo ·
            7 Familiar del patrón · 8 Otra persona del trabajo
  escolar   1 Maestro · 2 Maestra · 3 Compañero · 4 Compañera ·
            5 Director(a) · 6 Trabajador de la escuela · 7 Trabajadora de la
            escuela · 8 Persona desconocida de la escuela · 9 Otra persona
            de la escuela
  99 = no especificado en los tres; se ignora, no se cuenta como agresor.

Maestro/maestra y compañero/compañera vienen separados por sexo en el
catálogo escolar. Se conservan separados: en una encuesta sobre violencia de
género, colapsarlos borraría justo la variable de interés.
"""

import sys
import os
import importlib.util
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils_enadis import escribir  # noqa: E402

_ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "endireh.csv.py")
_spec = importlib.util.spec_from_file_location("endireh_base", _ruta)
_endireh = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_endireh)

ANIO = _endireh.ANIO
COLS_DISC = _endireh.COLS_DISC
DISC_POSITIVOS = _endireh.DISC_POSITIVOS
BASE_ENDIREH = _endireh.BASE_ENDIREH

# Un ámbito por bloque: la sección de donde salen las columnas de agresor, el
# prefijo con el que empiezan, el catálogo de códigos, la columna que define
# la población expuesta (None = todas) y cómo se nombra en el tablero.
AMBITOS = [
    {
        "clave": "familiar",
        "seccion": "TB_SEC_XI",
        "prefijo": "P11_2_",
        "universo": None,
        "universo_texto": "Mujeres de 15 años o más",
        "etiqueta": "Violencia familiar de {agresor} en los últimos 12 meses",
        # Palabras que solo aparecen en el catálogo de AGRESOR de este
        # ámbito, nunca en los de lugar o de sí/no (ver _cols_agresor).
        "palabras_agresor": ["padrastro", "abuelo", "cuñado", "yerno"],
        "agresores": {
            1: "su padre", 2: "su madre", 3: "su padrastro o madrastra",
            4: "un abuelo o abuela", 5: "un hijo o hija",
            6: "un hermano o hermana", 7: "un tío o tía",
            8: "un primo o prima", 9: "un suegro o suegra",
            10: "un cuñado o cuñada", 11: "un sobrino o sobrina",
            12: "un yerno", 13: "otro familiar",
        },
    },
    {
        "clave": "laboral",
        "seccion": "TB_SEC_VIII",
        "prefijo": "P8_",
        "universo": "POB_L_12M",
        "universo_texto": "Mujeres de 15 años o más que trabajaron en los últimos 12 meses",
        "etiqueta": "Violencia en el trabajo de {agresor} en los últimos 12 meses",
        "palabras_agresor": ["patr", "supervisor", "capataz", "gerente"],
        "agresores": {
            1: "su patrón o jefe", 2: "un supervisor o capataz",
            3: "un gerente o directivo", 4: "un compañero de trabajo",
            5: "un cliente", 6: "una persona desconocida del trabajo",
            7: "un familiar del patrón", 8: "otra persona del trabajo",
        },
    },
    {
        "clave": "escolar",
        "seccion": "TB_SEC_VII",
        "prefijo": "P7_",
        "universo": "POB_E_12M",
        "universo_texto": "Mujeres de 15 años o más que asistieron a la escuela en los últimos 12 meses",
        "etiqueta": "Violencia en la escuela de {agresor} en los últimos 12 meses",
        "palabras_agresor": ["maestro", "maestra", "director"],
        "agresores": {
            1: "un maestro", 2: "una maestra", 3: "un compañero",
            4: "una compañera", 5: "el director o directora",
            6: "un trabajador de la escuela",
            7: "una trabajadora de la escuela",
            8: "una persona desconocida de la escuela",
            9: "otra persona de la escuela",
        },
    },
]

# Mínimo de casos sin expandir para publicar un agresor. Con 13 parentescos
# por ámbito, los más raros (yerno, sobrino) se quedan con un puñado de
# observaciones, y una tasa calculada sobre eso es ruido con apariencia de
# dato. Se omiten en vez de publicarlos con una advertencia que nadie lee.
MIN_CASOS_AGRESOR = 30


def _a_numero(serie):
    """
    Normaliza una columna a numérico. Varias columnas de ENDIREH llegan como
    texto con un retorno de carro pegado ('1\\r'); comparar contra el entero
    1 las descartaría en silencio (ver endireh_ambito.csv.py).
    """
    return pd.to_numeric(
        serie.astype(str).str.strip().str.replace("\r", "", regex=False),
        errors="coerce")


def _cols_agresor(df, amb):
    """
    Columnas de agresor de un ámbito, identificadas por su CATÁLOGO y no por
    el patrón del nombre.

    El patrón `P{sec}_{preg}_{acto}_{1..3}` no basta: en la sección laboral
    56 de las 170 columnas que lo cumplen son preguntas de sí/no (P8_3_*),
    no listas de agresores. Y como el código 1 significa "Sí" ahí pero
    "Patrón(a) o jefe(a)" en el catálogo de agresor, incluirlas inflaba al
    primer agresor de cada ámbito con respuestas que no nombran a nadie —un
    error silencioso, porque el tipo de dato es el mismo.

    Una columna es de agresor solo si su catálogo contiene EXACTAMENTE las
    etiquetas esperadas para ese ámbito (las de `amb["agresores"]`). Se
    compara contra el catálogo oficial de la sección, que es la única fuente
    que distingue una lista de personas de una escala de sí/no.
    """
    dir_cat = os.path.join(BASE_ENDIREH, str(ANIO),
                           f"conjunto_de_datos_{amb['seccion']}", "catalogos")
    cols = []
    for c in df.columns:
        if not (c.startswith(amb["prefijo"]) and c.count("_") == 3
                and c.rsplit("_", 1)[-1] in ("1", "2", "3")):
            continue
        ruta = os.path.join(dir_cat, f"{c}.csv")
        if not os.path.exists(ruta):
            continue
        with open(ruta, encoding="latin-1") as fh:
            texto = fh.read()
        # Los códigos no bastan para reconocer un catálogo de agresor: en la
        # sección laboral, P8_13_* usa exactamente los mismos números 1-8
        # para el LUGAR del incidente ("en las instalaciones del trabajo",
        # "en la calle"), y en P8_3_* significan sí/no. Tres catálogos
        # distintos, idéntico rango numérico y tipo de dato.
        #
        # Lo único que los distingue es el TEXTO de las etiquetas, así que
        # se compara contra las palabras clave del catálogo de agresor de
        # ese ámbito. No se exige el catálogo completo: algunos actos traen
        # una versión recortada a los agresores efectivamente observados
        # (P11_2_2_2 lista seis de los trece parentescos).
        if any(p in texto.lower() for p in amb["palabras_agresor"]):
            cols.append(c)
    return cols


def main():
    disc = _endireh._tabla(ANIO, "TB_SEC_XIX")
    sdem = _endireh._tabla(ANIO, "TSDem")
    vd = _endireh._tabla(ANIO, "TB_VD")

    llaves = ["ID_VIV", "ID_PER", "UPM", "VIV_SEL", "HOGAR", "N_REN"]

    presentes = [c for c in COLS_DISC if c in disc.columns]
    if not presentes:
        raise SystemExit(
            f"ENDIREH {ANIO}: no se encontraron las columnas {COLS_DISC}.")
    marca = disc[presentes].isin(DISC_POSITIVOS).any(axis=1)
    disc_min = disc[llaves].copy()
    disc_min["disc"] = marca.map({True: "Con discapacidad",
                                  False: "Sin discapacidad"})

    # De TB_VD salen el factor, la entidad y las columnas de población
    # expuesta; de TSDem, la edad.
    cols_vd = llaves + ["FAC_MUJ", "NOM_ENT", "POB_L_12M", "POB_E_12M"]
    persona = vd[[c for c in cols_vd if c in vd.columns]].copy()
    persona = persona.merge(disc_min, on=llaves, how="inner")
    persona = persona.merge(sdem[llaves + ["EDAD"]], on=llaves, how="left")

    if len(persona) != len(vd):
        raise SystemExit(
            f"ENDIREH {ANIO}: la unión dejó {len(persona)} de {len(vd)} "
            "mujeres. Revisa las llaves antes de publicar.")

    persona["EDAD"] = pd.to_numeric(persona["EDAD"], errors="coerce")
    persona["rango_edad"] = persona["EDAD"].apply(_endireh._rango_edad)
    persona["factor"] = pd.to_numeric(persona["FAC_MUJ"],
                                      errors="coerce").fillna(0)
    persona["entidad"] = (persona["NOM_ENT"].astype(str).str.strip()
                          .map(_endireh._normalizar_entidad))
    persona["sexo"] = "Mujeres"
    persona["anio"] = ANIO

    llaves_grupo = ["anio", "sexo", "disc", "entidad", "rango_edad"]
    salida = []

    for amb in AMBITOS:
        tabla = _endireh._tabla(ANIO, amb["seccion"])
        cols = _cols_agresor(tabla, amb)
        if not cols:
            print(f"[aviso] {amb['clave']}: sin columnas de agresor con "
                  f"prefijo {amb['prefijo']}; se omite.", file=sys.stderr)
            continue

        # Se normalizan las 60-114 columnas de una vez y se unen a la persona.
        agres = tabla[llaves].copy()
        for c in cols:
            agres[c] = _a_numero(tabla[c])

        base = persona.merge(agres, on=llaves, how="left")

        # Universo del ámbito: quien no está expuesta sale del denominador,
        # no cuenta como "sin violencia" (ver docstring).
        if amb["universo"] and amb["universo"] in base.columns:
            base = base[_a_numero(base[amb["universo"]]).eq(1)]

        if not len(base):
            raise SystemExit(
                f"ENDIREH {ANIO}: el ámbito {amb['clave']} se quedó sin "
                "filas tras aplicar su universo. Revisa la columna "
                f"{amb['universo']} en los microdatos.")

        marcas = base[cols]
        for codigo, nombre in amb["agresores"].items():
            # Aplanado: la mujer cuenta una vez si el código aparece en
            # CUALQUIERA de las columnas de agresor, sin importar el acto ni
            # la posición.
            sub = base.copy()
            sub["_num"] = marcas.eq(codigo).any(axis=1)

            casos_positivos = int(sub["_num"].sum())
            if casos_positivos < MIN_CASOS_AGRESOR:
                print(f"[aviso] {amb['clave']}/{nombre}: solo "
                      f"{casos_positivos} casos, por debajo del mínimo de "
                      f"{MIN_CASOS_AGRESOR}; se omite.", file=sys.stderr)
                continue

            g = sub.groupby(llaves_grupo, dropna=True, observed=True).apply(
                lambda x: pd.Series({
                    "num": float(x.loc[x["_num"], "factor"].sum()),
                    "den": float(x["factor"].sum()),
                    "casos": int(len(x)),
                }), include_groups=False).reset_index()
            g["tema"] = "agresor"
            g["indicador"] = amb["etiqueta"].format(agresor=nombre)
            g["fuente"] = "ENDIREH (INEGI)"
            g["universo"] = amb["universo_texto"]
            salida.append(g)

        pct = (base.loc[marcas.notna().any(axis=1), "factor"].sum()
               / base["factor"].sum() * 100) if base["factor"].sum() else 0
        print(f"[ok] ENDIREH {ANIO}: ámbito {amb['clave']}, {len(cols)} "
              f"columnas de agresor, {len(base):,} mujeres en universo "
              f"({pct:.0f}% con algún dato)", file=sys.stderr)

    if not salida:
        raise SystemExit("ENDIREH agresores: no se generó ningún indicador.")

    escribir(salida)


if __name__ == "__main__":
    main()

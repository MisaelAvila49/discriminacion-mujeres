"""
censo.csv.py: Indicadores del Censo 2020, cuestionario ampliado.

Es la única fuente del tablero con representatividad municipal, y por eso de
aquí sale el mapa y el ranking territorial, Y AHORA TAMBIÉN la numeralia de
portada (antes construida desde ENIGH en enigh_distribucion.csv.py, retirado
en esta ronda). La muestra ampliada son ~15 millones de registros de persona
(3.3 GB en CSV), así que se procesa con DuckDB en una sola pasada agregada:
cargarla a pandas no cabe en memoria.

Semántica de los códigos, tomada de los scripts de análisis ya validados del
equipo (AnalisisSueltos/Obindi/inegi/censo_2020) y confirmada contra las
frecuencias de los propios microdatos:

  SEXO      1 = hombre, 3 = mujer.  OJO: no es 1/2 como en ENADIS y ENIGH.
            Confundirlo deja a las mujeres fuera de todo el tablero.
  DIS_*     1 = sin dificultad, 2 = limitación (lo hace con dificultad),
            3 = mucha dificultad, 4 = no puede hacerlo, 8/9 = no especificado.
            Discapacidad = 3 o 4. La "limitación" (2) NO se cuenta: es una
            categoría intermedia que el propio INEGI reporta aparte, y
            sumarla dispararía la prevalencia por encima del 10%.
  CONACT    10-19 = trabajó, 30 = buscó trabajo, 60 = quehaceres del hogar,
            50 = estudia. Es un código de dos dígitos, no de uno.

Códigos de educación, verificados por CONSISTENCIA CRUZADA contra las
frecuencias — no existe un diccionario oficial del Censo 2020 localmente
(se buscó exhaustivamente en el árbol Z:\\SocialDataIbero\\ antes de fijar
estos valores; ver docs/superpowers/specs/2026-08-29-filtros-y-censo-design.md
sección 2.4 para el detalle de la verificación):

  ALFABET   1 = sabe leer y escribir (89.5% de adultos), 3 = no (10.4%),
            9 = no especificado (0.13%). Mismo patrón 1=sí/3=no que SEXO.
  ASISTEN   1 = asiste a la escuela (5.1% en 18+), 3 = no (94.9%),
            9 = no especificado (0.06%).
  ESCOLARI  '00' a '08', escala ASCENDENTE de nivel aprobado (verificado
            cruzando contra ALFABET y edad promedio: '00' tiene 17.1% de
            alfabetismo y 59.7 años de edad promedio — sin escolaridad,
            población de mayor edad; '03' en adelante ya 98-100% alfabeta).
            El mapeo fino nivel-por-nivel (01=preescolar, 02=primaria...)
            NO está confirmado contra texto oficial, pero el UMBRAL que usa
            el indicador de abajo sí: educación media superior o más =
            ESCOLARI >= '04', análogo al corte NIVEL_MEDIA_SUPERIOR=4 que
            usa ENIGH sobre su propia escala 0-9 (enigh_educacion.csv.py).
            '99' = no especificado, sale del denominador.
"""

import sys
import os
import duckdb

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils_enadis import ENTIDADES, TIPOS_DISC, escribir  # noqa: E402

RUTA_CENSO = os.environ.get(
    "CENSO_PERSONAS",
    r"Z:\SocialDataIbero\AnalisisSueltos\JCF\data\raw\censo2020\Personas00.CSV",
)

COLS_DIS = [
    "DIS_VER", "DIS_OIR", "DIS_CAMINAR", "DIS_RECORDAR",
    "DIS_BANARSE", "DIS_HABLAR", "DIS_MENTAL",
]

# Etiqueta de cada columna, mismo vocabulario que TIPOS_DISC (utils_enadis.py)
# y que ETIQUETA_TIPO_DISC de ENIGH (enigh.csv.py), para que "dominio de
# dificultad" signifique lo mismo en las tres fuentes. El Censo NO tiene un
# dominio equivalente a "Brazos o manos" (disc_brazo de ENIGH): son 7
# dominios, no 8.
ETIQUETA_DOMINIO = {
    "DIS_VER": "Ver",
    "DIS_OIR": "Oír",
    "DIS_CAMINAR": "Caminar",
    "DIS_RECORDAR": "Recordar o concentrarse",
    "DIS_BANARSE": "Bañarse o vestirse",
    "DIS_HABLAR": "Hablar o comunicarse",
    "DIS_MENTAL": "Mental",
}
assert set(ETIQUETA_DOMINIO.values()) <= set(TIPOS_DISC), (
    "ETIQUETA_DOMINIO debe usar un subconjunto del vocabulario de TIPOS_DISC "
    "(utils_enadis.py) para que el filtro de dominio signifique lo mismo en "
    "todas las fuentes."
)

# DuckDB no acepta un alias de columna sin comillas si trae espacios (tres
# de las siete etiquetas los tienen: "Recordar o concentrarse", "Bañarse o
# vestirse", "Hablar o comunicarse"). El alias SQL usa un slug ASCII propio
# (sin espacios ni acentos); la etiqueta legible de ETIQUETA_DOMINIO NUNCA
# cambia — solo se usa para nombrar columnas intermedias del DataFrame, no
# para lo que termina en el CSV (`tipo_discapacidad` sigue llevando la
# etiqueta completa, ver el loop de "Distribución por dominio de
# dificultad" más abajo).
_TRANS_ACENTOS = str.maketrans("áéíóúÁÉÍÓÚñÑ", "aeiouAEIOUnN")


def _slug_sql(etiqueta):
    return etiqueta.translate(_TRANS_ACENTOS).replace(" ", "_")


SLUG_DOMINIO = {etq: _slug_sql(etq) for etq in ETIQUETA_DOMINIO.values()}
assert len(set(SLUG_DOMINIO.values())) == len(SLUG_DOMINIO), (
    "Dos etiquetas de dominio produjeron el mismo slug SQL; revisa "
    "ETIQUETA_DOMINIO por posibles colisiones tras quitar espacios/acentos."
)

# Discapacidad = mucha dificultad (3) o no puede hacerlo (4).
COND_DISC = " OR ".join(f"{c} IN (3, 4)" for c in COLS_DIS)

# Los mismos rangos de edad que el resto del tablero.
CASE_EDAD = """
  CASE
    WHEN EDAD BETWEEN 18 AND 29 THEN '18-29'
    WHEN EDAD BETWEEN 30 AND 44 THEN '30-44'
    WHEN EDAD BETWEEN 45 AND 59 THEN '45-59'
    WHEN EDAD >= 60 AND EDAD < 999 THEN '60+'
  END
"""

CASE_ENT = "\n".join(
    f"    WHEN ENT = {k} THEN '{v}'" for k, v in ENTIDADES.items()
)

# Columnas de dominio de dificultad, cada una 1/0 según si la persona marcó
# discapacidad (3 o 4) en ESE dominio específico. Se seleccionan aparte del
# indicador binario `disc` porque el filtro de dominio necesita saber CUÁL
# dominio, no solo si hay alguno.
SELECT_DOMINIOS = ",\n    ".join(
    f"CASE WHEN {col} IN (3, 4) THEN 1 ELSE 0 END AS dom_{SLUG_DOMINIO[etiqueta]}"
    for col, etiqueta in ETIQUETA_DOMINIO.items()
)

# Un solo barrido del archivo produce todos los indicadores a la vez: agrupa
# por las llaves del tablero y suma FACTOR de forma condicional. Recorrer
# 3.3 GB una vez por indicador costaría varias veces más sin ganar nada.
CONSULTA = f"""
WITH base AS (
  SELECT
    CASE WHEN SEXO = 1 THEN 'Hombres' WHEN SEXO = 3 THEN 'Mujeres' END AS sexo,
    CASE WHEN {COND_DISC} THEN 'Con discapacidad'
         ELSE 'Sin discapacidad' END AS disc,
    CASE
{CASE_ENT}
    END AS entidad,
    {CASE_EDAD} AS rango_edad,
    FACTOR AS factor,
    CONACT,
    ALFABET,
    ASISTEN,
    ESCOLARI,
    {SELECT_DOMINIOS}
  FROM read_csv_auto('{{ruta}}', ignore_errors=true)
  WHERE EDAD >= 18 AND EDAD < 999 AND SEXO IN (1, 3)
)
SELECT
  2020 AS anio, sexo, disc, entidad, rango_edad,
  -- Ocupación: trabajó la semana de referencia.
  SUM(CASE WHEN CONACT BETWEEN 10 AND 19 THEN factor ELSE 0 END) AS ocupada_num,
  -- Trabajo doméstico como actividad principal.
  SUM(CASE WHEN CONACT = 60 THEN factor ELSE 0 END) AS hogar_num,
  -- Denominador común de trabajo: población con condición de actividad
  -- declarada. El no especificado (99) y el nulo salen del denominador en
  -- vez de contarse como "no trabaja".
  SUM(CASE WHEN CONACT IS NOT NULL AND CONACT <> 99 THEN factor ELSE 0 END) AS den_conact,
  COUNT(*) FILTER (WHERE CONACT IS NOT NULL AND CONACT <> 99) AS casos_conact,
  -- Educación: alfabetismo, asistencia, nivel.
  SUM(CASE WHEN ALFABET = 3 THEN factor ELSE 0 END) AS no_alfabeta_num,
  SUM(CASE WHEN ALFABET IN (1, 3) THEN factor ELSE 0 END) AS den_alfabet,
  COUNT(*) FILTER (WHERE ALFABET IN (1, 3)) AS casos_alfabet,
  SUM(CASE WHEN ASISTEN = 1 AND rango_edad = '18-29' THEN factor ELSE 0 END) AS asiste_num,
  SUM(CASE WHEN ASISTEN IN (1, 3) AND rango_edad = '18-29' THEN factor ELSE 0 END) AS den_asisten,
  COUNT(*) FILTER (WHERE ASISTEN IN (1, 3) AND rango_edad = '18-29') AS casos_asisten,
  SUM(CASE WHEN ESCOLARI >= '04' THEN factor ELSE 0 END) AS media_sup_num,
  SUM(CASE WHEN ESCOLARI <> '99' THEN factor ELSE 0 END) AS den_escolari,
  COUNT(*) FILTER (WHERE ESCOLARI <> '99') AS casos_escolari,
  -- Población total del grupo (para distribución/prevalencia de portada).
  SUM(factor) AS poblacion,
  COUNT(*) AS casos_poblacion,
  {", ".join(f"SUM(CASE WHEN dom_{slug} = 1 THEN factor ELSE 0 END) AS dom_{slug}_num" for slug in SLUG_DOMINIO.values())}
FROM base
WHERE sexo IS NOT NULL AND rango_edad IS NOT NULL AND entidad IS NOT NULL
GROUP BY ALL
ORDER BY ALL
"""


def main():
    if not os.path.exists(RUTA_CENSO):
        raise SystemExit(
            f"No se encontró la muestra del Censo en {RUTA_CENSO}. "
            "Define CENSO_PERSONAS o consulta el README."
        )

    con = duckdb.connect()
    con.execute("PRAGMA disable_progress_bar")  # ensucia stderr en el build
    df = con.execute(CONSULTA.format(ruta=RUTA_CENSO.replace("\\", "/"))).df()

    if df.empty:
        raise SystemExit("El Censo no devolvió filas; revisa la ruta y los códigos.")

    # Guardia: prevalencia de discapacidad en adultos. Si SEXO o DIS_* se
    # leyeran mal, este número se dispara o se desploma.
    tot = df["poblacion"].sum()
    cd = df.loc[df["disc"] == "Con discapacidad", "poblacion"].sum()
    prev = cd / tot * 100 if tot else 0
    if not 2 <= prev <= 25:
        raise SystemExit(
            f"Censo 2020: prevalencia de discapacidad de {prev:.1f}%, fuera de "
            "rango. Revisa los códigos de DIS_* y SEXO."
        )
    print(f"[ok] Censo 2020: prevalencia de discapacidad {prev:.1f}% en 18+",
          file=sys.stderr)

    import pandas as pd
    salida = []
    fuente = "Censo de Población y Vivienda, cuestionario ampliado (INEGI)"
    universo_adultos = "Personas de 18 años o más"

    def agrega(col_num, col_den, col_casos, tema, indicador, universo=universo_adultos):
        d = df[["anio", "sexo", "disc", "entidad", "rango_edad"]].copy()
        d["num"] = df[col_num]
        d["den"] = df[col_den]
        d["casos"] = df[col_casos]
        d["tema"] = tema
        d["indicador"] = indicador
        d["fuente"] = fuente
        d["universo"] = universo
        salida.append(d)

    # --- Trabajo (ya existían) ----------------------------------------------
    agrega("ocupada_num", "den_conact", "casos_conact", "trabajo", "Población ocupada")
    agrega("hogar_num", "den_conact", "casos_conact", "trabajo",
           "Se dedica a los quehaceres del hogar")

    # --- Educación (nuevos) --------------------------------------------------
    agrega("no_alfabeta_num", "den_alfabet", "casos_alfabet",
           "educacion-censo", "No sabe leer ni escribir (Censo)")
    agrega("asiste_num", "den_asisten", "casos_asisten",
           "educacion-censo", "Asiste a la escuela (18 a 29 años, Censo)",
           universo="Personas de 18 a 29 años")
    agrega("media_sup_num", "den_escolari", "casos_escolari",
           "educacion-censo", "Educación media superior o más (Censo)")

    # --- Distribución de portada (antes en enigh_distribucion.csv.py) ------
    # Población de cada grupo: num = población del grupo, den = población
    # adulta total (2020), así que num/den es la participación del grupo.
    total_nacional = float(df["poblacion"].sum())
    d = df[["anio", "sexo", "disc", "entidad", "rango_edad"]].copy()
    d["num"] = df["poblacion"]
    d["den"] = total_nacional
    d["casos"] = df["casos_poblacion"]
    d["tema"] = "distribucion"
    d["indicador"] = "Población"
    d["fuente"] = fuente
    d["universo"] = universo_adultos
    salida.append(d)

    # Prevalencia de discapacidad: num = población con discapacidad del
    # grupo (sexo+entidad+edad), den = población total de ESE grupo.
    prev_llaves = ["anio", "sexo", "entidad", "rango_edad"]
    piv = df.groupby(prev_llaves, observed=True).apply(
        lambda x: pd.Series({
            "num": float(x.loc[x["disc"] == "Con discapacidad", "poblacion"].sum()),
            "den": float(x["poblacion"].sum()),
            "casos": int(x["casos_poblacion"].sum()),
        }), include_groups=False).reset_index()
    piv["disc"] = "Total"
    piv["tema"] = "distribucion"
    piv["indicador"] = "Prevalencia de discapacidad"
    piv["fuente"] = fuente
    piv["universo"] = universo_adultos
    salida.append(piv)

    # --- Distribución por dominio de dificultad (entre quienes tienen
    # discapacidad) -----------------------------------------------------------
    con_disc = df[df["disc"] == "Con discapacidad"]
    if len(con_disc) and cd > 0:
        for etiqueta in ETIQUETA_DOMINIO.values():
            col_dom = f"dom_{SLUG_DOMINIO[etiqueta]}_num"
            t = con_disc.groupby(prev_llaves, observed=True).apply(
                lambda x: pd.Series({
                    "num": float(x[col_dom].sum()),
                    "den": float(x["poblacion"].sum()),
                    "casos": int(x["casos_poblacion"].sum()),
                }), include_groups=False).reset_index()
            t["disc"] = "Con discapacidad"
            t["tipo_discapacidad"] = etiqueta
            t["tema"] = "distribucion"
            t["indicador"] = "Distribución por dominio de dificultad"
            t["fuente"] = fuente
            t["universo"] = "Personas de 18 años o más con discapacidad"
            salida.append(t)

    todo = pd.concat(salida, ignore_index=True)
    escribir([todo])


if __name__ == "__main__":
    main()

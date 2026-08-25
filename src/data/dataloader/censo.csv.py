"""
censo.csv.py: Indicadores del Censo 2020, cuestionario ampliado.

Es la única fuente del tablero con representatividad municipal, y por eso de
aquí salen el mapa y el ranking territorial. La muestra ampliada son ~15
millones de registros de persona (3.3 GB en CSV), así que se procesa con
DuckDB en una sola pasada agregada: cargarla a pandas no cabe en memoria.

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
"""

import sys
import os
import duckdb

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils_enadis import ENTIDADES  # noqa: E402

RUTA_CENSO = os.environ.get(
    "CENSO_PERSONAS",
    r"Z:\SocialDataIbero\AnalisisSueltos\JCF\data\raw\censo2020\Personas00.CSV",
)

COLS_DIS = [
    "DIS_VER", "DIS_OIR", "DIS_CAMINAR", "DIS_RECORDAR",
    "DIS_BANARSE", "DIS_HABLAR", "DIS_MENTAL",
]

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

# Un solo barrido del archivo produce los tres indicadores a la vez: agrupa por
# las llaves del tablero y suma FACTOR de forma condicional. Recorrer 3.3 GB
# una vez por indicador costaría el triple sin ganar nada.
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
    CONACT
  FROM read_csv_auto('{{ruta}}', ignore_errors=true)
  WHERE EDAD >= 18 AND EDAD < 999 AND SEXO IN (1, 3)
)
SELECT
  2020 AS anio, sexo, disc, entidad, rango_edad,
  -- Ocupación: trabajó la semana de referencia.
  SUM(CASE WHEN CONACT BETWEEN 10 AND 19 THEN factor ELSE 0 END) AS ocupada_num,
  -- Trabajo doméstico como actividad principal.
  SUM(CASE WHEN CONACT = 60 THEN factor ELSE 0 END) AS hogar_num,
  -- Denominador común: población con condición de actividad declarada. El
  -- no especificado (99) y el nulo salen del denominador en vez de contarse
  -- como "no trabaja".
  SUM(CASE WHEN CONACT IS NOT NULL AND CONACT <> 99 THEN factor ELSE 0 END) AS den,
  COUNT(*) FILTER (WHERE CONACT IS NOT NULL AND CONACT <> 99) AS casos
FROM base
WHERE sexo IS NOT NULL AND rango_edad IS NOT NULL AND entidad IS NOT NULL
GROUP BY ALL
ORDER BY ALL
"""

INDICADORES = [
    ("ocupada_num", "Población ocupada"),
    ("hogar_num", "Se dedica a los quehaceres del hogar"),
]


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
    tot = df["den"].sum()
    cd = df.loc[df["disc"] == "Con discapacidad", "den"].sum()
    prev = cd / tot * 100 if tot else 0
    if not 2 <= prev <= 25:
        raise SystemExit(
            f"Censo 2020: prevalencia de discapacidad de {prev:.1f}%, fuera de "
            "rango. Revisa los códigos de DIS_* y SEXO."
        )
    print(f"[ok] Censo 2020: prevalencia de discapacidad {prev:.1f}% en 18+",
          file=sys.stderr)

    # Formato largo, igual que los demás loaders.
    import pandas as pd
    salida = []
    for col, nombre in INDICADORES:
        d = df[["anio", "sexo", "disc", "entidad", "rango_edad", "den", "casos"]].copy()
        d["num"] = df[col]
        d["tema"] = "trabajo"
        d["indicador"] = nombre
        d["fuente"] = "Censo de Población y Vivienda, cuestionario ampliado (INEGI)"
        d["universo"] = "Personas de 18 años o más"
        salida.append(d)

    todo = pd.concat(salida, ignore_index=True)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", newline="")
    todo[[
        "tema", "indicador", "anio", "sexo", "disc", "entidad", "rango_edad",
        "num", "den", "casos", "fuente", "universo",
    ]].to_csv(sys.stdout, index=False)


if __name__ == "__main__":
    main()

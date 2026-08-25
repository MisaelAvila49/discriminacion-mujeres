"""
enadis.csv.py: Indicadores de ENADIS 2017 y 2022 para el tablero.

Emite una tabla larga: una fila por (tema, indicador, año, sexo, discapacidad,
entidad, rango de edad) con numerador y denominador ponderados y el número de
casos sin expandir. El porcentaje se calcula en el navegador, después de
agregar, para no promediar tasas nunca.

La semántica de cada pregunta se verificó contra el prontuario oficial de
INEGI que acompaña a cada edición (Prontuario2017/2022.ipynb), no se dedujo
de los nombres de columna.
"""

import sys
import os
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils_enadis import (  # noqa: E402
    ANIOS, preparar_sdem, indicador, escribir, col,
)

# El nombre de la fuente NO lleva el año: la edición ya la elige el usuario
# en el filtro, y repetirla en el pie de la gráfica la contradecía cuando se
# comparaban varias ediciones en paneles.
FUENTE = "ENADIS (INEGI)"


def indicadores_sdem(sdem, year):
    """
    Indicadores que salen de la tabla sociodemográfica y por lo tanto existen
    para toda la población adulta, con la muestra más grande disponible.
    """
    fuente = FUENTE
    filas = []

    # --- Alfabetismo -------------------------------------------------------
    # Se invierte a "no sabe leer ni escribir": el indicador que interesa es
    # la carencia, y así la barra más alta es siempre la peor situación.
    # El 9 (no especificado) sale del denominador; contarlo como "sí sabe"
    # inventaría alfabetismo que nadie declaró.
    col_alfa = col(year, "alfabetismo", sdem)
    base = sdem[sdem[col_alfa].isin([1, 2])]
    filas.append(indicador(
        base, base[col_alfa].eq(2),
        tema="educacion",
        indicador_nombre="No sabe leer ni escribir",
        fuente=fuente,
    ))

    # --- Condición de actividad --------------------------------------------
    # Códigos verificados en el prontuario (idénticos en ambas ediciones,
    # aunque la pregunta cambie de número):
    #   1 trabajó al menos una hora   2 tenía trabajo pero no trabajó
    #   3 buscó trabajo               6 se dedicó a los quehaceres del hogar
    # Ocupación = 1 o 2. Es la comparación central de "oportunidades de
    # trabajo": la brecha de participación entre mujeres y hombres es una de
    # las más grandes del país, y crece con la discapacidad.
    col_act = col(year, "condicion_actividad", sdem)
    base = sdem[sdem[col_act].between(1, 8)]
    filas.append(indicador(
        base, base[col_act].isin([1, 2]),
        tema="trabajo",
        indicador_nombre="Población ocupada",
        fuente=fuente,
    ))
    # Trabajo doméstico no remunerado como actividad principal. Es el
    # contrapeso de la barra anterior: donde la ocupación de las mujeres
    # baja, esta sube, y esa simetría es el hallazgo.
    filas.append(indicador(
        base, base[col_act].eq(6),
        tema="trabajo",
        indicador_nombre="Se dedica a los quehaceres del hogar",
        fuente=fuente,
    ))

    # --- Asistencia escolar, solo en edad típica de estudio ----------------
    # No existe en la tabla sociodemográfica de 2017: el indicador queda solo
    # para 2022 y el aviso deja constancia de por qué la serie no es continua.
    col_esc = col(year, "asistencia_escolar", sdem)
    if col_esc is None:
        print(f"[aviso] ENADIS {year}: sin asistencia escolar en TSDEM; "
              "el indicador se omite para este año.", file=sys.stderr)
    else:
        base = sdem[(sdem[col_esc].isin([1, 2])) & (sdem["edad"].between(18, 29))]
        filas.append(indicador(
            base, base[col_esc].eq(1),
            tema="educacion",
            indicador_nombre="Asiste a la escuela (18 a 29 años)",
            fuente=fuente,
            universo="Personas de 18 a 29 años",
        ))

    return filas


def main():
    filas = []
    for year in ANIOS:
        sdem = preparar_sdem(year)
        filas.extend(indicadores_sdem(sdem, year))

    if not filas:
        raise SystemExit("No se generó ningún indicador de ENADIS.")
    escribir(filas)


if __name__ == "__main__":
    main()

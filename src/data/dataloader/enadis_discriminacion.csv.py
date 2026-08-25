"""
enadis_discriminacion.csv.py: Discriminación vivida y negación de derechos.

Es el módulo por el que existe la ENADIS y el único indicador del tablero que
mide discriminación de forma directa, en vez de inferirla de una brecha entre
grupos. Todo lo demás del sitio (ocupación, ingreso, analfabetismo) muestra
desigualdades de resultado; esto muestra el trato reportado por las personas.

Preguntas, verificadas contra los prontuarios oficiales del INEGI:

  "En los últimos cinco años, ¿le han negado injustificadamente...?"
  seguida de una batería de derechos y servicios.

    2017: pm8_1_1 .. pm8_1_7   (tabla tadulto, columnas en minúsculas)
    2022: PM9_1_1 .. PM9_1_8   (tabla tadulto, columnas en mayúsculas)

  Códigos: 1 = sí se lo negaron, 2 = no, 3 = no aplica / no solicitó,
  9 = no especificado (solo aparece en 2022).

Dos cuidados que definen el indicador:

  1. LA BATERÍA CAMBIÓ DE TAMAÑO. En 2017 se preguntaron seis reactivos
     (1, 2, 3, 4, 6, 7) y en 2022 ocho (se agregaron el 5 y el 8). Un índice
     de "al menos un derecho negado" calculado sobre todos los reactivos
     disponibles NO es comparable entre ediciones: 2022 tendría dos
     oportunidades más de salir positivo solo por tener más preguntas.
     Por eso el indicador se restringe a los SEIS reactivos comunes.

  2. El código 3 ("no aplica") sale del denominador. Quien nunca solicitó un
     servicio no pudo ser discriminado al solicitarlo, y contarlo como "no me
     lo negaron" diluiría la tasa con personas que nunca estuvieron expuestas.
"""

import sys
import os
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils_enadis import (  # noqa: E402
    ANIOS, preparar_sdem, cargar, unir_con_sdem, indicador, escribir,
)

# Prefijo de la batería en cada edición y los reactivos comunes a ambas.
BATERIA = {2017: "pm8_1", 2022: "pm9_1"}
REACTIVOS_COMUNES = ["1", "2", "3", "4", "6", "7"]


def indicadores_discriminacion(year, sdem):
    fuente = "ENADIS (INEGI)"
    adulto = cargar(year, "tadulto")
    df = unir_con_sdem(adulto, sdem)

    pref = BATERIA[year]
    cols = [f"{pref}_{r}" for r in REACTIVOS_COMUNES]
    faltan = [c for c in cols if c not in df.columns]
    if faltan:
        raise KeyError(
            f"ENADIS {year}: faltan reactivos de la batería de negación de "
            f"derechos: {faltan}."
        )

    filas = []

    # --- Al menos un derecho negado ----------------------------------------
    # Denominador: quienes contestaron sí o no en al menos un reactivo. Se
    # excluye a quien respondió "no aplica" en todos, que nunca estuvo
    # expuesto a la situación.
    expuesto = df[cols].isin([1, 2]).any(axis=1)
    base = df[expuesto].copy()
    negado = base[cols].eq(1).any(axis=1)
    filas.append(indicador(
        base, negado,
        tema="discriminacion",
        indicador_nombre="Le negaron injustificadamente algún derecho",
        fuente=fuente,
        universo="Personas de 18 años o más que solicitaron el servicio",
    ))

    # --- Negación de atención médica o medicamentos ------------------------
    # El primer reactivo de la batería en ambas ediciones. Se reporta aparte
    # porque la salud es el derecho donde la discriminación por discapacidad
    # tiene consecuencias más directas.
    col_salud = f"{pref}_1"
    base_s = df[df[col_salud].isin([1, 2])].copy()
    filas.append(indicador(
        base_s, base_s[col_salud].eq(1),
        tema="discriminacion",
        indicador_nombre="Le negaron atención médica o medicamentos",
        fuente=fuente,
        universo="Personas de 18 años o más que solicitaron el servicio",
    ))

    # --- Negación de apoyos de programas sociales --------------------------
    col_apoyo = f"{pref}_2"
    base_a = df[df[col_apoyo].isin([1, 2])].copy()
    filas.append(indicador(
        base_a, base_a[col_apoyo].eq(1),
        tema="discriminacion",
        indicador_nombre="Le negaron apoyos de programas sociales",
        fuente=fuente,
        universo="Personas de 18 años o más que solicitaron el apoyo",
    ))

    return filas


def main():
    filas = []
    for year in ANIOS:
        sdem = preparar_sdem(year)
        filas.extend(indicadores_discriminacion(year, sdem))
        print(f"[ok] ENADIS {year}: discriminación vivida", file=sys.stderr)

    if not filas:
        raise SystemExit("No se generó ningún indicador de discriminación.")
    escribir(filas)


if __name__ == "__main__":
    main()

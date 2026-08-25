# -*- coding: utf-8 -*-
"""
Deflactor del INPC: lleva los indicadores monetarios a pesos constantes.

POR QUÉ EXISTE
--------------
Las tres ediciones de la ENIGH venían en pesos nominales de su propio año, de
modo que el ingreso laboral promedio de mujeres con discapacidad "creció" de
$8,617 en 2020 a $13,444 en 2024: un 56 por ciento que es casi todo inflación
acumulada, no poder adquisitivo. Comparar montos entre ediciones sin deflactar
sobreestima cualquier mejora y produce una serie que no significa nada.

Las BRECHAS no estaban mal: el deflactor es un factor común dentro de un mismo
año, así que se cancela en la razón (65 centavos por peso siguen siendo 65
centavos, deflactado o no). Lo que arregla este módulo son los NIVELES y su
comparación en el tiempo.

QUÉ MÉTODO USA Y POR QUÉ
------------------------
INPC promedio del PERIODO DE LEVANTAMIENTO de cada edición (agosto a noviembre),
no promedio del año calendario. La ENIGH capta el ingreso de los meses previos
a la entrevista, así que un promedio anual incluiría enero a julio, meses que
ningún ingreso captado refleja. La diferencia entre ambos métodos ronda punto y
medio porcentual, pero el criterio correcto no cuesta más.

El año base es el más reciente del tablero, de modo que las cifras se leen en
pesos de hoy: "pesos constantes de 2024" es una unidad que el lector entiende
sin convertir nada.

DE DÓNDE SALEN LOS ÍNDICES
--------------------------
De `src/data/inpc.csv`, que se llena a mano desde INEGI y se versiona. NO se
codifican aquí: un índice hardcodeado sin fuente es exactamente el tipo de dato
que nadie vuelve a verificar. El archivo tiene tres columnas:

    anio,mes,inpc

con `mes` numérico (8 a 11) e `inpc` el índice nacional mensual, base segunda
quincena de julio de 2018 = 100.

Descarga: https://www.inegi.org.mx/temas/inpc/  →  Tabulados  →  INPC mensual
nacional. También sirve el SIE de Banxico (serie SP1) o la calculadora de
inflación del INEGI.

Si el archivo está vacío o le faltan meses de alguna edición, `factor()` lanza
una excepción con el detalle: es preferible que el data loader se caiga a que
publique una serie que mezcla pesos de años distintos sin avisar.
"""
import os

import pandas as pd

# Meses del levantamiento de la ENIGH. El INEGI aplica el cuestionario entre
# agosto y noviembre; el periodo de referencia del ingreso son los meses
# previos a la entrevista.
MESES_LEVANTAMIENTO = [8, 9, 10, 11]

# Año al que se llevan todas las cifras. Es la edición más reciente del
# tablero: cambiarlo re-expresa toda la serie, así que vive aquí y no
# disperso en cada loader.
ANIO_BASE = 2024

RUTA_INPC = os.path.join(os.path.dirname(__file__), "..", "inpc.csv")

# Etiqueta de unidad que consume el catálogo del tablero.
UNIDAD = f"pesos constantes de {ANIO_BASE}"


def _cargar():
    """Lee el CSV del INPC. Devuelve {anio: promedio del levantamiento}."""
    ruta = os.path.abspath(RUTA_INPC)
    if not os.path.exists(ruta):
        raise FileNotFoundError(
            f"No existe {ruta}. Es el archivo con la serie del INPC que "
            "necesita el deflactor; se llena desde "
            "https://www.inegi.org.mx/temas/inpc/ (tabulados, INPC mensual "
            "nacional, base 2Q julio 2018 = 100) con columnas anio,mes,inpc."
        )

    df = pd.read_csv(ruta)
    faltantes = {"anio", "mes", "inpc"} - set(df.columns)
    if faltantes:
        raise ValueError(f"{ruta}: faltan columnas {sorted(faltantes)}")

    df = df.dropna(subset=["anio", "mes", "inpc"])
    if df.empty:
        raise ValueError(
            f"{ruta} está vacío. Hay que capturar el INPC mensual de los "
            f"meses {MESES_LEVANTAMIENTO} para cada edición de la ENIGH "
            "antes de poder deflactar. Ver el encabezado de deflactor.py."
        )

    df["anio"] = df["anio"].astype(int)
    df["mes"] = df["mes"].astype(int)
    df = df[df["mes"].isin(MESES_LEVANTAMIENTO)]

    return df.groupby("anio")["inpc"].mean().to_dict()


def factor(anio, anio_base=ANIO_BASE):
    """
    Factor que multiplica un monto nominal de `anio` para expresarlo en pesos
    de `anio_base`. Mayor que 1 para años anteriores a la base.

    Lanza si falta el índice de alguno de los dos años: es la salvaguarda que
    evita publicar una serie con pesos mezclados.
    """
    indices = _cargar()
    for a in (int(anio), int(anio_base)):
        if a not in indices:
            raise KeyError(
                f"Falta el INPC de {a} en {os.path.abspath(RUTA_INPC)}. "
                f"Se necesitan los meses {MESES_LEVANTAMIENTO} de cada "
                "edición para deflactar."
            )
    return indices[int(anio_base)] / indices[int(anio)]


def deflactar(serie, anio, anio_base=ANIO_BASE):
    """Aplica el factor a una serie o escalar de montos nominales."""
    return serie * factor(anio, anio_base)


def disponible():
    """¿Se puede deflactar? Para que un loader decida sin atrapar excepciones."""
    try:
        indices = _cargar()
    except (FileNotFoundError, ValueError):
        return False
    return ANIO_BASE in indices


if __name__ == "__main__":
    # `python deflactor.py` imprime la tabla de factores, que es la forma
    # rápida de verificar que el CSV quedó bien capturado.
    try:
        indices = _cargar()
    except (FileNotFoundError, ValueError) as e:
        raise SystemExit(f"No se pudo leer el INPC:\n  {e}")

    print(f"INPC promedio de {MESES_LEVANTAMIENTO} por edición")
    print(f"Base: pesos de {ANIO_BASE}\n")
    print(f"{'año':>6}  {'INPC':>9}  {'factor':>8}")
    for anio in sorted(indices):
        print(f"{anio:>6}  {indices[anio]:>9.3f}  {factor(anio):>8.4f}")

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

DE DÓNDE SALEN LOS DATOS
------------------------
De `src/data/inpc.csv`, que se descarga del INEGI y se versiona. NO se
codifican aquí: un dato hardcodeado sin fuente es exactamente el tipo de cifra
que nadie vuelve a verificar. El archivo tiene tres columnas:

    anio,mes,inflacion_anual

`inflacion_anual` es la variación porcentual del INPC general respecto al mismo
mes del año anterior, que es la serie que el Banco de Indicadores del INEGI
entrega directamente:

    https://www.inegi.org.mx/app/indicadores/  →  Índices de precios  →  INPC,
    base 2Q julio 2018  →  Mensual  →  Inflación mensual interanual  →
    Índice general (Variación Porcentual)

Se usa la tasa interanual y no el nivel del índice porque es lo que esa consulta
exporta, y porque para deflactar solo hace falta la RAZÓN de precios entre dos
años: encadenar las tasas interanuales del mismo mes la reconstruye exactamente,
sin necesidad del nivel. El archivo descargado viene en UTF-16 con una columna
de área geográfica; `scripts/importar_inpc.py` lo normaliza.

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
    """Lee el CSV del INPC. Devuelve {(anio, mes): inflación anual en %}."""
    ruta = os.path.abspath(RUTA_INPC)
    if not os.path.exists(ruta):
        raise FileNotFoundError(
            f"No existe {ruta}. Es la serie de inflación interanual del INPC "
            "que necesita el deflactor; se descarga del Banco de Indicadores "
            "del INEGI y se normaliza con scripts/importar_inpc.py. Ver el "
            "encabezado de este módulo."
        )

    df = pd.read_csv(ruta)
    faltantes = {"anio", "mes", "inflacion_anual"} - set(df.columns)
    if faltantes:
        raise ValueError(f"{ruta}: faltan columnas {sorted(faltantes)}")

    df = df.dropna(subset=["anio", "mes", "inflacion_anual"])
    if df.empty:
        raise ValueError(
            f"{ruta} está vacío. Hay que descargar la serie de inflación "
            "interanual del INPC. Ver el encabezado de deflactor.py."
        )

    df["anio"] = df["anio"].astype(int)
    df["mes"] = df["mes"].astype(int)

    return {(int(r.anio), int(r.mes)): float(r.inflacion_anual)
            for r in df.itertuples()}


def factor(anio, anio_base=ANIO_BASE):
    """
    Factor que multiplica un monto nominal de `anio` para expresarlo en pesos
    de `anio_base`. Mayor que 1 para años anteriores a la base.

    Se calcula encadenando las tasas de inflación interanuales del mismo mes:
    el precio de agosto de 2024 respecto al de agosto de 2020 es el producto de
    (1 + inflación de agosto) de 2021, 2022, 2023 y 2024. Se promedian los
    cuatro meses del levantamiento.

    Lanza si falta algún mes intermedio: es la salvaguarda que evita publicar
    una serie con pesos mezclados.
    """
    anio, anio_base = int(anio), int(anio_base)
    if anio == anio_base:
        return 1.0

    tasas = _cargar()
    ruta = os.path.abspath(RUTA_INPC)
    inicio, fin = min(anio, anio_base), max(anio, anio_base)

    factores = []
    for mes in MESES_LEVANTAMIENTO:
        r = 1.0
        for y in range(inicio + 1, fin + 1):
            if (y, mes) not in tasas:
                raise KeyError(
                    f"Falta la inflación de {y}/{mes:02d} en {ruta}. "
                    f"Para deflactar de {anio} a {anio_base} se necesita la "
                    f"serie completa del mes {mes} en ese rango."
                )
            r *= 1 + tasas[(y, mes)] / 100
        factores.append(r)

    razon = sum(factores) / len(factores)
    # Si el año a convertir es POSTERIOR a la base, la razón se invierte.
    return razon if anio < anio_base else 1 / razon


def deflactar(serie, anio, anio_base=ANIO_BASE):
    """Aplica el factor a una serie o escalar de montos nominales."""
    return serie * factor(anio, anio_base)


def disponible(anios):
    """¿Se puede deflactar esta lista de años? Sin atrapar excepciones fuera."""
    try:
        for a in anios:
            factor(a)
    except (FileNotFoundError, ValueError, KeyError):
        return False
    return True


if __name__ == "__main__":
    # `python deflactor.py` imprime la tabla de factores, que es la forma
    # rápida de verificar que el CSV quedó bien capturado.
    try:
        tasas = _cargar()
    except (FileNotFoundError, ValueError) as e:
        raise SystemExit(f"No se pudo leer el INPC:\n  {e}")

    anios = sorted({a for a, _ in tasas})
    print("Deflactor por encadenamiento de inflación interanual")
    print(f"Meses del levantamiento: {MESES_LEVANTAMIENTO}")
    print(f"Base: pesos de {ANIO_BASE}")
    print(f"Serie disponible: {anios[0]}-{anios[-1]}\n")
    print(f"{'año':>6}  {'factor':>8}   equivale a")
    for anio in (2020, 2022, 2024):
        try:
            f = factor(anio)
        except KeyError as e:
            print(f"{anio:>6}  {'s/d':>8}   {e}")
            continue
        print(f"{anio:>6}  {f:>8.4f}   $1,000 de {anio} = ${1000 * f:,.0f} de {ANIO_BASE}")

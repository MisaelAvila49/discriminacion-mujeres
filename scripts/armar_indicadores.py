# -*- coding: utf-8 -*-
"""
Concatena la salida de los data loaders en los dos CSV que consume el sitio.

    src/data/indicadores.csv           sin desglose por dominio de dificultad
    src/data/indicadores_tipo_disc.csv con el desglose

Los loaders emiten un esquema largo común; unos traen la columna
`tipo_discapacidad` y otros no (Censo y ENDIREH no la tienen). Este script:

1. Agrega la columna `encuesta`, derivada del nombre del archivo: `enigh_apoyos`
   y `enigh_jornada` son partes de la ENIGH, no encuestas distintas.
2. Parte en dos: las filas con `tipo_discapacidad == "Todos"` van al archivo
   principal (sin esa columna, que ahí no aporta), y TODAS las filas van al de
   desglose. Un loader sin la columna cuenta como "Todos".

USO
---
    python scripts/armar_indicadores.py <directorio con los .csv generados>

Los loaders se corren antes, uno por uno, redirigiendo a ese directorio:

    python src/data/dataloader/enigh.csv.py > /tmp/gen/enigh.csv
    ...
"""
import glob
import io
import os
import sys

import pandas as pd

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDA_PRINCIPAL = os.path.join(RAIZ, "src", "data", "indicadores.csv")
SALIDA_TIPO = os.path.join(RAIZ, "src", "data", "indicadores_tipo_disc.csv")

# Nombre de archivo -> encuesta. Lo que no esté aquí usa el nombre tal cual.
ENCUESTA = {
    "enigh_apoyos": "enigh",
    "enigh_jornada": "enigh",
    "enigh_educacion": "enigh",
    "enigh_tecnologia": "enigh",
    "enigh_distribucion": "enigh",
    "enadis_discriminacion": "enadis",
}

COLS = ["tema", "indicador", "anio", "sexo", "disc", "entidad", "rango_edad",
        "tipo_discapacidad", "num", "den", "casos", "fuente", "universo",
        "encuesta"]


def main():
    if len(sys.argv) != 2:
        raise SystemExit(f"uso: python {sys.argv[0]} <directorio>")

    archivos = sorted(glob.glob(os.path.join(sys.argv[1], "*.csv")))
    if not archivos:
        raise SystemExit(f"No hay .csv en {sys.argv[1]}")

    partes = []
    for ruta in archivos:
        nombre = os.path.splitext(os.path.basename(ruta))[0]
        df = pd.read_csv(ruta, low_memory=False)
        if df.empty:
            print(f"  [aviso] {nombre} salió vacío, se omite")
            continue
        # Censo y ENDIREH no desagregan por dominio: cuentan como "Todos".
        if "tipo_discapacidad" not in df.columns:
            df["tipo_discapacidad"] = "Todos"
        df["encuesta"] = ENCUESTA.get(nombre, nombre)
        partes.append(df)
        print(f"  {nombre:24} {len(df):>7,} filas -> {df['encuesta'].iloc[0]}")

    todo = pd.concat(partes, ignore_index=True)
    for c in COLS:
        if c not in todo.columns:
            raise SystemExit(f"Falta la columna {c} tras concatenar")
    todo = todo[COLS]

    # Desglose completo.
    todo.to_csv(SALIDA_TIPO, index=False, encoding="utf-8")

    # Principal: solo el agregado, y sin la columna que ahí no dice nada.
    principal = todo[todo["tipo_discapacidad"] == "Todos"].drop(
        columns=["tipo_discapacidad"])
    principal.to_csv(SALIDA_PRINCIPAL, index=False, encoding="utf-8")

    print(f"\n{len(principal):>8,} filas -> {SALIDA_PRINCIPAL}")
    print(f"{len(todo):>8,} filas -> {SALIDA_TIPO}")


if __name__ == "__main__":
    main()

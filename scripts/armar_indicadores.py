# -*- coding: utf-8 -*-
"""
Concatena la salida de los data loaders en los TRES CSV que consume el sitio.

    src/data/indicadores.csv           sin desglose (dominio=Todos, decil=Todos)
    src/data/indicadores_tipo_disc.csv desglose por dominio de dificultad
    src/data/indicadores_decil.csv     desglose por decil de ingreso

Los loaders emiten un esquema largo común; unos traen las columnas
`tipo_discapacidad`/`decil` y otros no (Censo y ENDIREH no las tienen; ni
siquiera los loaders de ENIGH que no calculan decil, como tecnología). Este
script:

1. Agrega la columna `encuesta`, derivada del nombre del archivo: `enigh_apoyos`
   y `enigh_jornada` son partes de la ENIGH, no encuestas distintas.
2. Parte en TRES: las filas con AMBAS columnas en "Todos" van al archivo
   principal (sin esas columnas, que ahí no aportan); las filas con
   tipo_discapacidad != "Todos" van al archivo de dominio; las filas con
   decil != "Todos" van al archivo de decil. Un loader sin alguna columna
   cuenta como "Todos" en ella — nunca aparece en el archivo de desglose
   correspondiente.

Las dos dimensiones de desglose son MUTUAMENTE EXCLUYENTES por diseño de los
loaders (ver enigh.csv.py, explotar_dimensiones): ninguna fila real tiene
ambas columnas distintas de "Todos" a la vez, así que separarlas en dos
archivos en vez de uno no pierde ninguna combinación que el tablero use.

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
SALIDA_DECIL = os.path.join(RAIZ, "src", "data", "indicadores_decil.csv")
# Un archivo por tema, para que cada página cargue solo lo suyo.
DIR_TIPO = os.path.join(RAIZ, "src", "data", "tipo_disc")
DIR_DECIL = os.path.join(RAIZ, "src", "data", "decil")
DIR_PRINCIPAL = os.path.join(RAIZ, "src", "data", "principal")

# Nombre de archivo -> encuesta. Lo que no esté aquí usa el nombre tal cual.
ENCUESTA = {
    "enigh_apoyos": "enigh",
    "enigh_jornada": "enigh",
    "enigh_educacion": "enigh",
    "enigh_tecnologia": "enigh",
    "enigh_transporte": "enigh",
    "enigh_ingreso": "enigh",
    "enigh_jefatura": "enigh",
    "enadis_discriminacion": "enadis",
    "endireh_ambito": "endireh",
    "endireh_agresor": "endireh",
    "endireh_agresor_tipo": "endireh",
}

COLS = ["tema", "indicador", "anio", "sexo", "disc", "entidad", "rango_edad",
        "tipo_discapacidad", "decil", "num", "den", "casos", "ee", "fuente",
        "universo", "encuesta"]


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
        # Los loaders que no desagregan por dominio o por decil cuentan como
        # "Todos" en la columna que les falte.
        for col in ("tipo_discapacidad", "decil"):
            if col not in df.columns:
                df[col] = "Todos"
        # `ee` falta en las encuestas sin diseño muestral publicado y en
        # cualquier loader que todavía no lo calcule. Se rellena vacío, no
        # en cero: un cero se leería como estimación sin incertidumbre.
        if "ee" not in df.columns:
            df["ee"] = pd.NA
        df["encuesta"] = ENCUESTA.get(nombre, nombre)
        partes.append(df)
        print(f"  {nombre:24} {len(df):>7,} filas -> {df['encuesta'].iloc[0]}")

    todo = pd.concat(partes, ignore_index=True)
    for c in COLS:
        if c not in todo.columns:
            raise SystemExit(f"Falta la columna {c} tras concatenar")
    todo = todo[COLS]

    # Guardia: ninguna fila real debería tener AMBAS columnas distintas de
    # "Todos" a la vez (ver docstring). Si aparece una, algún loader está
    # generando la explosión cruzada que este diseño evita a propósito.
    cruzadas = todo[(todo["tipo_discapacidad"] != "Todos") &
                     (todo["decil"] != "Todos")]
    if len(cruzadas):
        raise SystemExit(
            f"{len(cruzadas)} filas tienen tipo_discapacidad Y decil "
            "distintos de 'Todos' a la vez — revisa el loader que las "
            "generó, la explosión cruzada no está soportada."
        )

    dominio = todo[todo["tipo_discapacidad"] != "Todos"].drop(columns=["decil"])
    dominio.to_csv(SALIDA_TIPO, index=False, encoding="utf-8")

    decil = todo[todo["decil"] != "Todos"].drop(columns=["tipo_discapacidad"])
    decil.to_csv(SALIDA_DECIL, index=False, encoding="utf-8")

    # Además del archivo completo, una copia POR TEMA de cada desglose.
    #
    # El archivo entero de deciles pesa 37 MB y el de dominio 22, y hasta
    # ahora cada página cargaba los dos completos para usar solo su tema:
    # Trabajo bajaba 60 MB para pintar 27 mil filas suyas. Con la partición
    # cada página pide su tema y nada más.
    #
    # Los archivos completos se siguen escribiendo: `docs/` y cualquier
    # análisis que cruce temas los usa, y son la fuente de la que salen
    # estas partes.
    for etiqueta, tabla, carpeta in (
        ("dominio", dominio, DIR_TIPO),
        ("decil", decil, DIR_DECIL),
    ):
        os.makedirs(carpeta, exist_ok=True)
        # Se limpian los .csv previos: si un tema desaparece del catálogo, su
        # archivo viejo se quedaría ahí y el sitio seguiría sirviéndolo.
        for viejo_csv in glob.glob(os.path.join(carpeta, "*.csv")):
            os.remove(viejo_csv)
        for tema, sub in tabla.groupby("tema"):
            destino = os.path.join(carpeta, f"{tema}.csv")
            sub.to_csv(destino, index=False, encoding="utf-8")
        print(f"  {etiqueta}: {tabla['tema'].nunique()} archivos por tema "
              f"-> {carpeta}")

    # Principal: solo el agregado real, sin las columnas que ahí no aportan.
    principal = todo[
        (todo["tipo_discapacidad"] == "Todos") & (todo["decil"] == "Todos")
    ].drop(columns=["tipo_discapacidad", "decil"])
    principal.to_csv(SALIDA_PRINCIPAL, index=False, encoding="utf-8")

    # El principal también se parte, pero por ENCUESTA y no por tema: una
    # página necesita todos los indicadores de su fuente (el principal del
    # tema y los secundarios, que pueden ser de otros temas de la misma
    # encuesta), pero nunca los de otra fuente.
    os.makedirs(DIR_PRINCIPAL, exist_ok=True)
    for viejo_csv in glob.glob(os.path.join(DIR_PRINCIPAL, "*.csv")):
        os.remove(viejo_csv)
    for enc, sub in principal.groupby("encuesta"):
        sub.to_csv(os.path.join(DIR_PRINCIPAL, f"{enc}.csv"),
                   index=False, encoding="utf-8")
    print(f"  principal: {principal['encuesta'].nunique()} archivos por "
          f"encuesta -> {DIR_PRINCIPAL}")

    print(f"\n{len(principal):>8,} filas -> {SALIDA_PRINCIPAL}")
    print(f"{len(dominio):>8,} filas -> {SALIDA_TIPO}")
    print(f"{len(decil):>8,} filas -> {SALIDA_DECIL}")


if __name__ == "__main__":
    main()

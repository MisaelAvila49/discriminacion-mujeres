# -*- coding: utf-8 -*-
"""
Normaliza la descarga del INPC del INEGI a `src/data/inpc.csv`.

El Banco de Indicadores exporta un CSV en UTF-16 con una columna de área
geográfica y el encabezado partido en varias líneas, que pandas no lee de
frente. Este script lo aplana a tres columnas:

    anio,mes,inflacion_anual

QUÉ DESCARGAR
-------------
https://www.inegi.org.mx/app/indicadores/

    Índices de precios
      → Índice Nacional de Precios al Consumidor, base 2Q julio 2018
        → Mensual
          → Inflación mensual interanual
            → Índice general (Variación Porcentual)

Exportar como CSV. NO sirven las variantes "por ciudades", "por sus
componentes" ni "por clasificación del objeto del gasto": esas desagregan el
índice y aquí hace falta el general, un solo número por mes.

USO
---
    python scripts/importar_inpc.py <archivo descargado>
    python src/data/dataloader/deflactor.py     # verifica los factores
"""
import csv
import io
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDA = os.path.join(RAIZ, "src", "data", "inpc.csv")


def leer(ruta):
    """Devuelve [(anio, mes, inflacion)] del CSV del Banco de Indicadores."""
    crudo = io.open(ruta, "rb").read()

    # El export viene en UTF-16; si alguien lo reguarda desde Excel puede
    # quedar en UTF-8. Se intentan ambos antes de rendirse.
    texto = None
    for codec in ("utf-16", "utf-8-sig", "latin-1"):
        try:
            texto = crudo.decode(codec)
            if texto.count(",") > 10:
                break
        except (UnicodeDecodeError, UnicodeError):
            continue
    if texto is None:
        raise SystemExit(f"No se pudo decodificar {ruta}")

    filas = []
    for linea in texto.splitlines():
        partes = [p.strip() for p in linea.split(",")]
        # Las filas de datos son "AAAA/MM, <área>, <valor>".
        if len(partes) < 3 or "/" not in partes[0]:
            continue
        try:
            anio, mes = partes[0].split("/")
            filas.append((int(anio), int(mes), float(partes[2])))
        except ValueError:
            continue

    if not filas:
        raise SystemExit(
            f"{ruta} no trae filas con el patrón AAAA/MM,área,valor. "
            "¿Es el export correcto del Banco de Indicadores?"
        )
    return sorted(filas)


def main():
    if len(sys.argv) != 2:
        raise SystemExit(f"uso: python {sys.argv[0]} <archivo descargado>")

    filas = leer(sys.argv[1])
    with io.open(SALIDA, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["anio", "mes", "inflacion_anual"])
        w.writerows(filas)

    print(f"{len(filas)} filas -> {SALIDA}")
    print(f"cobertura: {filas[0][0]}/{filas[0][1]:02d} a "
          f"{filas[-1][0]}/{filas[-1][1]:02d}")


if __name__ == "__main__":
    main()

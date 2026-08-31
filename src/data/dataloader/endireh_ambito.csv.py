"""
endireh_ambito.csv.py: Quién ejerce la violencia, por ámbito de la relación.

Complementa a endireh.csv.py. Ese loader responde QUÉ tipo de violencia
(psicológica, física, sexual, económica); este responde DÓNDE y, por lo
tanto, QUIÉN la ejerce: la pareja, alguien en la escuela, alguien en el
trabajo, o un desconocido en la calle y el transporte.

La distinción importa para el argumento del tablero. "Las mujeres con
discapacidad viven más violencia" es un enunciado que no dice qué hacer;
"la viven sobre todo de su pareja, en un hogar del que dependen para
cuidados, y menos en la calle porque salen menos" sí orienta una política.
La dependencia de cuidados y la menor exposición al espacio público son dos
rasgos que atraviesan la vida de muchas mujeres con discapacidad, y el
ámbito es la variable que los vuelve visibles.

Se usa la clasificación por ámbito que el propio INEGI publica en TB_VD
(VESC/VLAB/VCOM/VPAR), no una reconstrucción desde las preguntas sueltas de
cada sección — mismo criterio que endireh.csv.py con los tipos de violencia.

--- Cada ámbito tiene su propio universo, y ahí está la trampa -----------

No todas las mujeres están expuestas a todos los ámbitos, y la propia ENDIREH
lo marca:

  VESC_12M  violencia escolar     universo: mujeres que asistieron a la
                                  escuela en los últimos 12 meses
                                  (POB_E_12M = 1, n=11,092 de 110,127)
  VLAB_12M  violencia laboral     universo: mujeres que trabajaron en los
                                  últimos 12 meses (POB_L_12M = 1, n=55,328)
  VPAR_12M  violencia de pareja   universo: mujeres con pareja actual o
                                  pasada (las de vacío no tuvieron)
  VCOM_12M  violencia comunitaria universo: todas (el espacio público no
                                  requiere haber "participado" en él)

Quien no asistió a la escuela tiene la celda VACÍA, no un 2 ("no sufrió").
Contar ese vacío como "no" diluiría la tasa escolar entre 110 mil mujeres
cuando el denominador real son 11 mil, y publicaría una violencia escolar
diez veces menor de la real. Por eso cada indicador filtra su universo antes
de agregar, y el `universo` que viaja al tablero lo dice explícitamente en
la tabla de respaldo.

--- La trampa de tipos: '1\\r' no es 1 -----------------------------------

Verificado contra los microdatos, no contra el diccionario: en el CSV de
TB_VD las columnas de ámbito ESCOLAR, LABORAL y PAREJA llegan como TEXTO con
un retorno de carro pegado ('1\\r', '2\\r', '\\r' para el vacío), mientras
que las de tipo de violencia (VTOT, VPSI, VFIS, VSEX, VECO) y la comunitaria
llegan como int64 limpio. En el mismo archivo, en la misma fila.

Consecuencia concreta: el `.isin([1, 2])` que usa endireh.csv.py —correcto
para las columnas que ese loader lee— devuelve CERO filas en las tres
columnas de texto. No lanza error, no avisa: publica un indicador vacío. Por
eso aquí las columnas se normalizan a numérico explícitamente antes de
cualquier filtro, y hay una guardia que aborta si un ámbito se queda sin
filas.

Códigos verificados en los microdatos:
  1 = sí sufrió violencia en ese ámbito en los últimos 12 meses
  2 = no
  9 = no especificado (sale del denominador)
  vacío = no aplica, no está expuesta a ese ámbito (sale del universo)
"""

import sys
import os
import glob
import importlib.util
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils_enadis import RANGOS_EDAD, escribir  # noqa: E402

# Se reutiliza la normalización de entidad y las constantes del loader
# principal de ENDIREH en vez de duplicarlas: si el catálogo de entidades
# cambia, cambia en un solo lugar.
_ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "endireh.csv.py")
_spec = importlib.util.spec_from_file_location("endireh_base", _ruta)
_endireh = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_endireh)

BASE_ENDIREH = _endireh.BASE_ENDIREH
ANIO = _endireh.ANIO
COLS_DISC = _endireh.COLS_DISC
DISC_POSITIVOS = _endireh.DISC_POSITIVOS

# (columna, nombre en el tablero, columna de universo o None si es universal)
AMBITOS = [
    ("VPAR_12M", "Violencia de la pareja en los últimos 12 meses", None),
    ("VCOM_12M", "Violencia comunitaria (calle, transporte) en los últimos 12 meses", None),
    ("VLAB_12M", "Violencia en el trabajo en los últimos 12 meses", "POB_L_12M"),
    ("VESC_12M", "Violencia en la escuela en los últimos 12 meses", "POB_E_12M"),
]

UNIVERSO_TEXTO = {
    "VPAR_12M": "Mujeres de 15 años o más con pareja actual o pasada",
    "VCOM_12M": "Mujeres de 15 años o más",
    "VLAB_12M": "Mujeres de 15 años o más que trabajaron en los últimos 12 meses",
    "VESC_12M": "Mujeres de 15 años o más que asistieron a la escuela en los últimos 12 meses",
}


def _a_numero(serie):
    """
    Normaliza una columna de TB_VD a numérico. Indispensable: tres de las
    cuatro columnas de ámbito llegan como texto con '\\r' pegado (ver
    docstring). `errors="coerce"` manda el vacío/no-aplica a NaN, que es
    justo lo que se quiere: sale del universo sin contarse como "no".
    """
    return pd.to_numeric(
        serie.astype(str).str.strip().str.replace("\r", "", regex=False),
        errors="coerce")


def main():
    disc = _endireh._tabla(ANIO, "TB_SEC_XIX")
    vd = _endireh._tabla(ANIO, "TB_VD")
    sdem = _endireh._tabla(ANIO, "TSDem")

    llaves = ["ID_VIV", "ID_PER", "UPM", "VIV_SEL", "HOGAR", "N_REN"]

    presentes = [c for c in COLS_DISC if c in disc.columns]
    if not presentes:
        raise SystemExit(
            f"ENDIREH {ANIO}: no se encontraron las columnas {COLS_DISC}.")
    marca = disc[presentes].isin(DISC_POSITIVOS).any(axis=1)
    disc = disc[llaves + ["CVE_ENT", "NOM_ENT"]].copy()
    disc["disc"] = marca.map({True: "Con discapacidad", False: "Sin discapacidad"})

    sdem_m = sdem[llaves + ["EDAD"]].copy()

    base = vd.merge(disc, on=llaves, how="inner", suffixes=("", "_d"))
    base = base.merge(sdem_m, on=llaves, how="left")

    if len(base) != len(vd):
        raise SystemExit(
            f"ENDIREH {ANIO}: la unión dejó {len(base)} de {len(vd)} mujeres. "
            "Revisa las llaves antes de publicar.")

    base["EDAD"] = pd.to_numeric(base["EDAD"], errors="coerce")
    base["rango_edad"] = base["EDAD"].apply(_endireh._rango_edad)
    base["factor"] = pd.to_numeric(base["FAC_MUJ"], errors="coerce").fillna(0)
    base["entidad"] = (base["NOM_ENT"].astype(str).str.strip()
                       .map(_endireh._normalizar_entidad))
    base["sexo"] = "Mujeres"
    base["anio"] = ANIO

    llaves_grupo = ["anio", "sexo", "disc", "entidad", "rango_edad"]
    salida = []

    for col, nombre, col_universo in AMBITOS:
        if col not in base.columns:
            print(f"[aviso] {col} no está en TB_VD; se omite.", file=sys.stderr)
            continue

        sub = base.copy()
        sub[col] = _a_numero(sub[col])

        # Universo del ámbito: quien no está expuesta no entra al
        # denominador (ver docstring). Se aplica ANTES del filtro de 1/2.
        if col_universo and col_universo in sub.columns:
            expuesta = _a_numero(sub[col_universo]).eq(1)
            sub = sub[expuesta]

        # El 9 (no especificado) y el vacío (NaN, no aplica) salen del
        # denominador; solo se agregan respuestas efectivas.
        sub = sub[sub[col].isin([1, 2])].copy()

        # Guardia contra el fallo silencioso que motivó este loader: si la
        # normalización de tipos se rompiera en una edición futura, el
        # indicador saldría vacío sin avisar. Mejor abortar que publicar
        # una gráfica en blanco.
        if not len(sub):
            raise SystemExit(
                f"ENDIREH {ANIO}: {col} se quedó sin filas tras filtrar. "
                "Revisa el tipo de la columna en los microdatos (¿texto con "
                "retorno de carro?) antes de publicar.")

        sub["_num"] = sub[col].eq(1)
        g = sub.groupby(llaves_grupo, dropna=True, observed=True).apply(
            lambda x: pd.Series({
                "num": float(x.loc[x["_num"], "factor"].sum()),
                "den": float(x["factor"].sum()),
                "casos": int(len(x)),
            }), include_groups=False).reset_index()
        g["tema"] = "autonomia"
        g["indicador"] = nombre
        g["fuente"] = "ENDIREH (INEGI)"
        g["universo"] = UNIVERSO_TEXTO.get(col, "Mujeres de 15 años o más")
        salida.append(g)

        pct = sub.loc[sub["_num"], "factor"].sum() / sub["factor"].sum() * 100
        print(f"[ok] ENDIREH {ANIO}: {nombre} — {len(sub):,} mujeres en "
              f"universo, {pct:.1f}% afectadas", file=sys.stderr)

    if not salida:
        raise SystemExit("ENDIREH ámbitos: no se generó ningún indicador.")

    escribir(salida)


if __name__ == "__main__":
    main()

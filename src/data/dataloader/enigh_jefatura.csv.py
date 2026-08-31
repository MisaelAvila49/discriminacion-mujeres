"""
enigh_jefatura.csv.py: Quién encabeza el hogar, con qué escolaridad y a qué edad.

`enigh_educacion.csv.py` ya publica cuántas personas de cada grupo encabezan
un hogar. Este loader responde lo que falta: cómo es esa jefatura. Una cifra
de 42.5 % de jefatura femenina entre mujeres con discapacidad no dice si esas
mujeres encabezan hogares porque tienen autonomía económica o porque quedaron
solas, y esas dos lecturas piden políticas opuestas.

Tres cortes, y cada uno se emite sobre el universo de quienes ENCABEZAN un
hogar (parentesco 101), no sobre toda la población adulta. Es un cambio de
denominador respecto a "Es jefa o jefe del hogar", y por eso el texto de
`universo` lo dice explícitamente en cada fila.

--- Escolaridad de quien encabeza ----------------------------------------

`educa_jefe` vive en concentradohogar y trae once códigos que distinguen
nivel incompleto de completo. El mapeo se verificó cruzando `educa_jefe` con
el `nivelaprob` de la persona con parentesco 101 en la tabla de población,
no leyendo el nombre de la variable:

   1 sin instrucción      2 preescolar
   3 primaria incompleta  4 primaria completa
   5 secundaria incompl.  6 secundaria completa
   7 media superior inc.  8 media superior completa
   9 licenciatura incom. 10 licenciatura completa
  11 posgrado

Se agrupan en las mismas siete categorías que usa el resto del tablero para
escolaridad, de modo que las dos páginas se lean con la misma escala. A
diferencia de `nivelaprob`, `educa_jefe` NO cambió de escala en 2024: los
once códigos y su distribución son estables en las tres ediciones,
verificado contra los microdatos.

--- Cuánto aporta al ingreso del hogar -----------------------------------

Se calcula sumando el ingreso trimestral de la persona que encabeza el hogar
(por `numren` en la tabla de ingresos) contra el ingreso total del hogar. El
umbral de "sostiene económicamente" se fija en la mitad o más, que es la
convención habitual para hablar de perceptor principal.

Solo entran hogares con ingreso mayor que cero: en uno sin ingreso
registrado la proporción sería una división entre cero, y contar esos casos
como "no aporta" mezclaría no tener ingreso propio con vivir en un hogar sin
ingreso alguno.

--- Edad de quien encabeza -----------------------------------------------

`edad_jefe` importa aquí más que en otros indicadores porque es la
explicación alternativa de la cifra de jefatura: si la jefatura femenina con
discapacidad se concentra en edades altas, la viudez explica el número tanto
o más que la autonomía. Se publica con los mismos rangos que el resto del
tablero para que sea comparable.

Los montos van deflactados al año base, como el resto de los montos (ver
deflactor.py).
"""

import sys
import os
import importlib.util
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import error_muestral as _em  # noqa: E402
from utils_enadis import RANGOS_EDAD, escribir  # noqa: E402
import deflactor  # noqa: E402

_ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "enigh.csv.py")
_spec = importlib.util.spec_from_file_location("enigh_base", _ruta)
_enigh = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_enigh)

BASE_ENIGH = _enigh.BASE_ENIGH

# Mismas siete categorías que usa la página de Educación, para que las dos
# se lean con la misma escala. Verificado contra los microdatos: cada par
# es incompleto/completo del mismo nivel.
NIVELES_JEFE = [
    ("Sin escolaridad", (1,)),
    ("Primaria", (2, 3, 4)),
    ("Secundaria", (5, 6)),
    ("Media superior", (7, 8)),
    ("Licenciatura", (9, 10)),
    ("Posgrado", (11,)),
]

UNIVERSO = "Personas de 18 años o más que encabezan su hogar"


def _rango_edad(edad):
    for lo, hi, etiqueta in RANGOS_EDAD:
        if lo <= edad <= hi:
            return etiqueta
    return None


def indicadores(pob, year):
    fuente = "ENIGH (INEGI)"
    llaves = ["anio", "sexo", "disc", "entidad", "rango_edad",
              "tipo_discapacidad", "decil"]
    filas = []

    ruta_hog = os.path.join(BASE_ENIGH, f"Bases{year}",
                            f"concentradohogar{year}.csv")
    if not os.path.exists(ruta_hog):
        print(f"[aviso] ENIGH {year}: falta concentradohogar; se omite.",
              file=sys.stderr)
        return filas

    hog = pd.read_csv(ruta_hog, low_memory=False, dtype={"folioviv": str})
    hog.columns = (hog.columns.str.replace("﻿", "", regex=False)
                   .str.lower().str.strip())
    for k in ("folioviv", "foliohog"):
        hog[k] = hog[k].astype(str).str.strip()
    hog["_llave"] = hog["folioviv"] + "|" + hog["foliohog"]

    pob = _enigh.explotar_dimensiones(pob)
    for k in ("folioviv", "foliohog"):
        pob[k] = pob[k].astype(str).str.strip()
    pob["_llave"] = pob["folioviv"] + "|" + pob["foliohog"]

    # El universo de todo este loader: quienes encabezan su hogar.
    if "parentesco" not in pob.columns:
        print(f"[aviso] ENIGH {year}: sin parentesco; se omite jefatura.",
              file=sys.stderr)
        return filas
    par = pd.to_numeric(pob["parentesco"], errors="coerce")
    jefes = pob[par.eq(101)].copy()
    if not len(jefes):
        return filas

    def agrega(base, condicion, indicador):
        b = base.copy()
        b["_num"] = condicion.fillna(False).astype(bool)
        g = b.groupby(llaves, dropna=True, observed=True).apply(
            lambda x: pd.Series({
                "num": float(x.loc[x["_num"], "factor"].sum()),
                "den": float(x["factor"].sum()),
                "casos": int(len(x)),
            }), include_groups=False).reset_index()
        g = _em.agrega_error(g, b, llaves, "_num")
        g["tema"] = "hogar"
        g["indicador"] = indicador
        g["fuente"] = fuente
        g["universo"] = UNIVERSO
        filas.append(g)

    # --- Escolaridad de quien encabeza -------------------------------------
    if "educa_jefe" in hog.columns:
        mapa = hog.set_index("_llave")["educa_jefe"]
        jefes["_educa"] = pd.to_numeric(
            jefes["_llave"].map(mapa), errors="coerce")
        con_educa = jefes[jefes["_educa"].notna()].copy()
        if len(con_educa):
            for etiqueta, codigos in NIVELES_JEFE:
                agrega(con_educa, con_educa["_educa"].isin(codigos),
                       f"Jefatura con escolaridad: {etiqueta}")

    # --- Edad de quien encabeza --------------------------------------------
    if "edad_jefe" in hog.columns:
        mapa = hog.set_index("_llave")["edad_jefe"]
        jefes["_edad_jefe"] = pd.to_numeric(
            jefes["_llave"].map(mapa), errors="coerce")
        con_edad = jefes[jefes["_edad_jefe"].notna()].copy()
        if len(con_edad):
            for lo, hi, etiqueta in RANGOS_EDAD:
                agrega(con_edad,
                       con_edad["_edad_jefe"].between(lo, hi),
                       f"Jefatura de {etiqueta} años")

    # --- Cuánto aporta al ingreso del hogar --------------------------------
    ruta_ing = os.path.join(BASE_ENIGH, f"Bases{year}", f"ingresos{year}.csv")
    if os.path.exists(ruta_ing) and "numren" in jefes.columns:
        ing = pd.read_csv(ruta_ing, low_memory=False, dtype={"folioviv": str})
        ing.columns = (ing.columns.str.replace("﻿", "", regex=False)
                       .str.lower().str.strip())
        for k in ("folioviv", "foliohog"):
            ing[k] = ing[k].astype(str).str.strip()
        ing["_llave"] = ing["folioviv"] + "|" + ing["foliohog"]
        ing["_mensual"] = (pd.to_numeric(ing["ing_tri"], errors="coerce")
                           .fillna(0.0) / 3 * deflactor.factor(year))
        ing["_persona"] = (ing["_llave"] + "|" +
                           ing["numren"].astype(str).str.strip())

        por_persona = ing.groupby("_persona")["_mensual"].sum()
        por_hogar = ing.groupby("_llave")["_mensual"].sum()

        base = jefes.copy()
        base["_persona"] = (base["_llave"] + "|" +
                            base["numren"].astype(str).str.strip())
        base["_ing_jefe"] = base["_persona"].map(por_persona).fillna(0.0)
        base["_ing_hogar"] = base["_llave"].map(por_hogar).fillna(0.0)
        base = base[base["_ing_hogar"] > 0].copy()

        if len(base):
            base["_num"] = (base["_ing_jefe"] / base["_ing_hogar"]) >= 0.5
            g = base.groupby(llaves, dropna=True, observed=True).apply(
                lambda x: pd.Series({
                    "num": float(x.loc[x["_num"], "factor"].sum()),
                    "den": float(x["factor"].sum()),
                    "casos": int(len(x)),
                }), include_groups=False).reset_index()
            g = _em.agrega_error(g, base, llaves, "_num")
            g["tema"] = "hogar"
            # Nombre distinto al del mismo cálculo en enigh_ingreso.csv.py:
            # aquel corre sobre TODA la población y este solo sobre quienes
            # encabezan un hogar, así que dan cifras distintas (26.7 % contra
            # 49.5 %). Con el mismo nombre, cualquier consulta que no filtre
            # por tema los promedia y produce una tercera cifra que no
            # significa nada.
            g["indicador"] = "La jefatura aporta la mitad o más del ingreso"
            g["fuente"] = fuente
            g["universo"] = UNIVERSO + ", en hogar con ingreso"
            filas.append(g)

            # Cuánto aporta en pesos, no solo si pasa el umbral.
            base["_masa"] = base["_ing_jefe"] * base["factor"]
            g = base.groupby(llaves, dropna=True, observed=True).apply(
                lambda x: pd.Series({
                    "num": float(x["_masa"].sum()),
                    "den": float(x["factor"].sum()),
                    "casos": int(len(x)),
                }), include_groups=False).reset_index()
            g = _em.agrega_error(g, base, llaves, "_ing_jefe")
            g["tema"] = "hogar"
            g["indicador"] = "Ingreso mensual de quien encabeza el hogar"
            g["fuente"] = fuente
            g["universo"] = UNIVERSO + ", en hogar con ingreso"
            filas.append(g)

    return filas


def main():
    filas = []
    for year in _enigh.ANIOS_ENIGH:
        pob = _enigh.cargar_poblacion(year)
        filas.extend(indicadores(pob, year))
        print(f"[ok] ENIGH {year}: jefatura", file=sys.stderr)

    if not filas:
        raise SystemExit("No se generó ningún indicador de jefatura.")
    escribir(filas)


if __name__ == "__main__":
    main()

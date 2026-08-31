"""
enigh_ingreso.csv.py: De dónde viene el dinero del hogar, y quién lo aporta.

Responde tres preguntas que el tablero no cubría: cómo se compone el ingreso
del hogar por fuente, cuánto de ese ingreso aporta la persona, y cómo cambia
ese reparto entre los cuatro grupos de la comparación.

Importa para el argumento del proyecto porque un mismo ingreso total no
significa lo mismo según de dónde venga. Un hogar que vive de transferencias
y programas sociales tiene un ingreso condicionado a que esos programas
sigan existiendo; uno que vive de su trabajo, no. La composición dice qué tan
frágil es el ingreso, y el monto por sí solo no.

--- Los cinco macrotemas -------------------------------------------------

La agrupación es la del propio INEGI (columnas Tema y SUBTEMA del catálogo
oficial), no una construida aquí, salvo por una separación deliberada:
`PROGRAMAS SOCIALES BIENESTAR` se reporta aparte de `INGRESOS POR
TRANSFERENCIAS` aunque el catálogo los pone bajo el mismo tema de ingresos
ajenos. La razón es que una pensión contributiva y una beca del gobierno son
cosas distintas para la pregunta del tablero: la primera se ganó trabajando
y la segunda es política social vigente.

  Trabajo         P001-P022   sueldos, salarios, horas extra, aguinaldo
  Negocio         P068-P081   negocio propio, cooperativas, sociedades
  Transferencias  P032-P042   jubilaciones, indemnizaciones, remesas,
                              donativos, becas privadas
  Programas       P043-P048   programas sociales previos
                  P101-P108   programas del Bienestar, que incluyen la
                              pensión de discapacidad (P105) y la de
                              adultos mayores (P104)
  Rentas          P023-P031   alquileres, intereses, rendimientos

Las claves de ingreso NO cambian entre 2020, 2022 y 2024 — verificado
contra el catálogo oficial, columna por columna. Es una diferencia
importante frente a las claves de GASTO, que sí se renumeraron en 2024 y
obligan a un mapeo por edición (ver enigh_apoyos.csv.py).

--- Cómo se lee cada indicador -------------------------------------------

Hay dos formas distintas y conviene no confundirlas:

  "Su hogar recibe ingreso de X"    es una TASA: qué proporción de personas
                                    vive en un hogar con esa fuente.
  "Ingreso mensual del hogar por X" es una MEDIA en pesos: cuánto aporta esa
                                    fuente al mes, entre los hogares que la
                                    tienen.

La composición porcentual (qué parte del total representa cada fuente) NO se
emite como indicador propio: sale de dividir la media de una fuente entre la
suma de todas, y fijarla aquí obligaría a congelar el denominador en el
loader, que es justo lo que el tablero decide al filtrar.

--- Aportación al hogar --------------------------------------------------

`ingresos.csv` trae el renglón de la persona (`numren`), así que el ingreso
sí se puede atribuir individualmente y no solo al hogar. "Aporta la mitad o
más del ingreso de su hogar" se calcula sumando el ingreso trimestral de la
persona contra el del hogar completo.

Ojo con el universo: solo entran personas en hogares con ingreso mayor que
cero. En un hogar sin ingreso registrado la proporción sería una división
entre cero, y contarlos como "no aporta" mezclaría dos situaciones
distintas: no tener ingreso propio, y vivir en un hogar sin ingreso alguno.

--- Los montos van deflactados -------------------------------------------

Como el resto de los montos del tablero, a pesos constantes del año base
(ver deflactor.py). Sin eso el ingreso "crece" entre ediciones por
inflación. Las tasas y las proporciones no se deflactan: no son dinero, y
el factor se cancela al dividir.
"""

import sys
import os
import importlib.util
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import error_muestral as _em  # noqa: E402
from utils_enadis import escribir  # noqa: E402
import deflactor  # noqa: E402

_ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "enigh.csv.py")
_spec = importlib.util.spec_from_file_location("enigh_base", _ruta)
_enigh = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_enigh)

BASE_ENIGH = _enigh.BASE_ENIGH

# Rango de claves por macrotema. Se expresan como rango numérico porque el
# catálogo las numera de corrido dentro de cada tema, y escribir las 87 a
# mano invitaba a que se desincronizaran con el catálogo oficial.
MACROTEMAS = {
    "trabajo": (1, 22),
    "rentas": (23, 31),
    "transferencias": (32, 42),
    "programas": (43, 50),
    "negocio": (68, 81),
}

# Programas del Bienestar: numeración aparte, a partir de P101.
CLAVES_BIENESTAR = [f"P{n}" for n in range(101, 109)]

ETIQUETA = {
    "trabajo": "trabajo",
    "negocio": "negocio propio",
    "transferencias": "transferencias (pensiones, remesas)",
    "programas": "programas sociales",
    "rentas": "rentas y alquileres",
}


def _claves(macro):
    ini, fin = MACROTEMAS[macro]
    claves = [f"P{n:03d}" for n in range(ini, fin + 1)]
    if macro == "programas":
        claves += CLAVES_BIENESTAR
    return claves


def indicadores(pob, year):
    fuente = "ENIGH (INEGI)"
    llaves = ["anio", "sexo", "disc", "entidad", "rango_edad",
              "tipo_discapacidad", "decil"]
    filas = []

    ruta = os.path.join(BASE_ENIGH, f"Bases{year}", f"ingresos{year}.csv")
    if not os.path.exists(ruta):
        print(f"[aviso] ENIGH {year}: falta {ruta}; se omite ingreso.",
              file=sys.stderr)
        return filas

    ing = pd.read_csv(ruta, low_memory=False, dtype={"folioviv": str})
    ing.columns = (ing.columns.str.replace("﻿", "", regex=False)
                   .str.lower().str.strip())
    for k in ("folioviv", "foliohog"):
        ing[k] = ing[k].astype(str).str.strip()
    ing["clave_n"] = ing["clave"].astype(str).str.strip().str.upper()
    # El ingreso trimestral se lleva a mensual para que la cifra se lea con
    # la misma unidad que el resto del tablero, y se deflacta al año base.
    ing["_mensual"] = (pd.to_numeric(ing["ing_tri"], errors="coerce")
                       .fillna(0.0) / 3 * deflactor.factor(year))
    ing["_llave"] = ing["folioviv"] + "|" + ing["foliohog"]

    pob = _enigh.explotar_dimensiones(pob)
    for k in ("folioviv", "foliohog"):
        pob[k] = pob[k].astype(str).str.strip()
    pob["_llave"] = pob["folioviv"] + "|" + pob["foliohog"]

    def agrega_tasa(marcados, indicador, universo):
        base = pob.copy()
        base["_num"] = base["_llave"].isin(marcados)
        g = base.groupby(llaves, dropna=True, observed=True).apply(
            lambda x: pd.Series({
                "num": float(x.loc[x["_num"], "factor"].sum()),
                "den": float(x["factor"].sum()),
                "casos": int(len(x)),
            }), include_groups=False).reset_index()
        g = _em.agrega_error(g, base, llaves, "_num")
        g["tema"] = "ingreso"
        g["indicador"] = indicador
        g["fuente"] = fuente
        g["universo"] = universo
        filas.append(g)

    def agrega_monto(montos, indicador, universo):
        """
        Media en pesos: masa de ingreso sobre población, solo entre quienes
        viven en un hogar con esa fuente. Incluir a los hogares en cero
        diluiría "cuánto aporta esta fuente donde existe" con ceros que no
        responden esa pregunta.
        """
        base = pob.copy()
        base["_monto"] = base["_llave"].map(montos).fillna(0.0)
        base = base[base["_monto"] > 0].copy()
        if not len(base):
            return
        base["_masa"] = base["_monto"] * base["factor"]
        g = base.groupby(llaves, dropna=True, observed=True).apply(
            lambda x: pd.Series({
                "num": float(x["_masa"].sum()),
                "den": float(x["factor"].sum()),
                "casos": int(len(x)),
            }), include_groups=False).reset_index()
        g = _em.agrega_error(g, base, llaves, "_monto")
        g["tema"] = "ingreso"
        g["indicador"] = indicador
        g["fuente"] = fuente
        g["universo"] = universo
        filas.append(g)

    # --- Composición del ingreso del hogar, por fuente ---------------------
    for macro, etiqueta in ETIQUETA.items():
        sel = ing[ing["clave_n"].isin(_claves(macro))]
        if not len(sel):
            print(f"[aviso] ENIGH {year}: sin claves de {macro}.",
                  file=sys.stderr)
            continue
        por_hogar = sel.groupby("_llave")["_mensual"].sum()
        con_fuente = set(por_hogar[por_hogar > 0].index)
        agrega_tasa(con_fuente,
                    f"Su hogar recibe ingreso de {etiqueta}",
                    "Personas de 18 años o más")
        agrega_monto(
            por_hogar.to_dict(),
            f"Ingreso mensual del hogar por {etiqueta}",
            f"Personas de 18 años o más en hogar con ingreso de {etiqueta}")

    # --- Aportación de la persona al ingreso de su hogar -------------------
    # `numren` identifica el renglón de la persona dentro del hogar, así que
    # aquí el ingreso SÍ es individual y no heredado del hogar.
    if "numren" in ing.columns and "numren" in pob.columns:
        ing["_persona"] = (ing["_llave"] + "|" +
                           ing["numren"].astype(str).str.strip())
        por_persona = ing.groupby("_persona")["_mensual"].sum()
        por_hogar_total = ing.groupby("_llave")["_mensual"].sum()

        base = pob.copy()
        base["_persona"] = (base["_llave"] + "|" +
                            base["numren"].astype(str).str.strip())
        base["_ing_persona"] = base["_persona"].map(por_persona).fillna(0.0)
        base["_ing_hogar"] = base["_llave"].map(por_hogar_total).fillna(0.0)
        # Solo hogares con ingreso: la proporción no existe si el
        # denominador es cero (ver docstring).
        base = base[base["_ing_hogar"] > 0].copy()

        if len(base):
            base["_num"] = (base["_ing_persona"] / base["_ing_hogar"]) >= 0.5
            g = base.groupby(llaves, dropna=True, observed=True).apply(
                lambda x: pd.Series({
                    "num": float(x.loc[x["_num"], "factor"].sum()),
                    "den": float(x["factor"].sum()),
                    "casos": int(len(x)),
                }), include_groups=False).reset_index()
            g = _em.agrega_error(g, base, llaves, "_num")
            g["tema"] = "ingreso"
            g["indicador"] = "Aporta la mitad o más del ingreso de su hogar"
            g["fuente"] = fuente
            g["universo"] = "Personas de 18 años o más en hogar con ingreso"
            filas.append(g)

            base["_masa"] = base["_ing_persona"] * base["factor"]
            g = base.groupby(llaves, dropna=True, observed=True).apply(
                lambda x: pd.Series({
                    "num": float(x["_masa"].sum()),
                    "den": float(x["factor"].sum()),
                    "casos": int(len(x)),
                }), include_groups=False).reset_index()
            g = _em.agrega_error(g, base, llaves, "_ing_persona")
            g["tema"] = "ingreso"
            g["indicador"] = "Ingreso mensual propio"
            g["fuente"] = fuente
            g["universo"] = "Personas de 18 años o más en hogar con ingreso"
            filas.append(g)

    return filas


def main():
    filas = []
    for year in _enigh.ANIOS_ENIGH:
        pob = _enigh.cargar_poblacion(year)
        filas.extend(indicadores(pob, year))
        print(f"[ok] ENIGH {year}: ingreso", file=sys.stderr)

    if not filas:
        raise SystemExit("No se generó ningún indicador de ingreso.")
    escribir(filas)


if __name__ == "__main__":
    main()

"""
enigh_apoyos.csv.py: Becas y gasto asociado a la discapacidad, por persona.

Vuelve al patrón de persona que usan los otros cuatro loaders de ENIGH
(trabajo, jornada, educación, tecnología), para que esta página use el mismo
motor compartido (dashboardTema/filtros.js) y los mismos cuatro filtros
(año, entidad, edad, dominio de dificultad) en vez de un panel propio.

La beca, la pensión y el gasto se registran en la ENIGH a nivel HOGAR (una
fila de ingreso o de gasto por hogar, nunca "esta persona recibió/gastó"). El
indicador se construye igual que "Hogar con conexión a internet" en
enigh_tecnologia.csv.py: se marca el HOGAR que cumple la condición y esa
marca se hereda a cada persona que vive ahí. La cifra se lee como "personas
que viven en un hogar que recibe/gasta en X", agrupadas por su propio sexo y
discapacidad — nunca como "personas con discapacidad que reciben SU beca".

--- Por qué puede haber "recibe la beca" en un hogar sin nadie que          -
--- calce con "discapacidad" en la ENCUESTA ------------------------------

La Pensión para el Bienestar de Personas con Discapacidad Permanente (clave
P105) es una transferencia de INGRESO DEL HOGAR: la ENIGH registra que el
hogar la recibe, no qué integrante específico es el beneficiario ni si esa
persona coincide con quien la ENIGH clasificó como "con discapacidad" en las
ocho preguntas de dificultad (disc_ver, disc_oir, etcétera). Dos causas
reales, no un error de captura:

  1. El programa lo cobra o administra otro integrante del hogar (un
     cuidador, madre o padre), que es quien aparece como perceptor del
     ingreso en la entrevista, aunque el beneficiario legal sea otra
     persona.
  2. El criterio de discapacidad de la ENIGH (ocho preguntas de dificultad
     funcional) y el criterio de elegibilidad del programa (discapacidad
     PERMANENTE certificada) no son la misma definición.

--- Claves verificadas contra el catálogo oficial (Claves ENIGH.xlsx) -----

Ingreso (no cambia de formato entre ediciones):
  P105    Pensión para el Bienestar de Personas con Discapacidad Permanente
  P104    Programa para el Bienestar de las Personas Adultas Mayores
          (contraste: programa social de mayor cobertura)

Gasto. La familia completa J065-J069 (2022) / 6131x-6140x (2024) es el
subtema "APARATOS ORTOPÉDICOS" del catálogo INEGI, acotado arriba por J064
(medicina alternativa, genérico) y abajo por J070 (seguro médico, genérico)
— confirmado que no falta ningún código intermedio. Cambia de formato
alfanumérico a numérico en 2024, y varios conceptos son EXCLUSIVOS de esa
edición porque el INEGI amplió el desglose ese año (no porque el gasto haya
cambiado de golpe). Frecuencias verificadas contra los microdatos 2022/2024,
no contra el nombre de la clave:

  J065 / 61311   anteojos y lentes de contacto e intraoculares      (n=2920/2005)
  J066 / 61320   aparatos para sordera                              (n=63/41)
  J067 / 61331   aparatos ortopédicos, silla de ruedas, andadera    (n=555/459)
  J068 / 61401   reparación de aparatos ortopédicos                 (n=94/16)
  J069 / 62321   cuidado de enfermos, terapeutas, glucómetro, etc.  (n=438/88)
  E010 / 101015  educación especial para discapacidad (general)
  --   / 101025  educación especial, discapacidad, PRIMARIA (2024)
  --   / 102005  educación especial, discapacidad, SECUNDARIA (2024)
  --   / 103005  educación especial, discapacidad, BACHILLERATO (2024)
  --   / 61312   otros productos de apoyo para la visión (2024, n=37)
  --   / 61332   calzado terapéutico (2024, n=152)
  --   / 61333   dispositivos médicos de soporte / ortesis (2024, n=233)
  --   / 61334   dispositivos y productos de asistencia (2024, n=78)
  --   / 61335   prótesis (2024, n=24)
  --   / 61336   sillas de ruedas y camas especiales (2024, n=167)
  --   / 61337   vehículos para personas con discapacidad (2024, n=1)
  --   / 61338   otros productos de apoyo (2024, n=433)
  --   / 61402   alquiler de productos médicos y auxiliares (2024, n=10)
  --   / 133022  residencias no médicas para personas con discapacidad (2024)
  --   / 133092  otros servicios de protección social: escuelas para
                  personas con discapacidad (2024)

Deliberadamente EXCLUIDOS, aunque suenan relacionados:
  - Medicamentos (recetados o no) por diabetes, presión arterial, dolor,
    etc: son gasto de salud GENERAL, no específico de discapacidad.
  - Seguro médico, hospitalización general, medicina alternativa: mismo
    argumento.
  - 133030 ("ayuda para el mantenimiento del hogar de las personas ADULTAS
    MAYORES Y personas con discapacidad"): mezcla dos poblaciones en una
    sola clave, y separarlas no es posible con estos datos.

OJO con el cero a la izquierda: en 2024 las claves de gasto son de SEIS
dígitos y las de la familia 6 empiezan con cero (061331, no 61331). El
catálogo las lista sin él.

--- El monto promedio no es una tasa -------------------------------------

"Gasto trimestral promedio" usa el mismo truco que "Ingreso laboral mensual
promedio" en enigh.csv.py: num = masa de gasto ponderada, den = población
ponderada de quienes SÍ gastaron algo, así que num/den da un promedio en
pesos, no un porcentaje. Se calcula solo entre personas cuyo hogar gastó
más de cero: incluir en el denominador a quienes viven en un hogar sin
gasto diluiría "cuánto gasta el que gasta" con ceros que no corresponden
a la pregunta.
"""

import sys
import os
import importlib.util
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils_enadis import escribir  # noqa: E402
import deflactor  # noqa: E402

_ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "enigh.csv.py")
_spec = importlib.util.spec_from_file_location("enigh_base", _ruta)
_enigh = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_enigh)

BASE_ENIGH = _enigh.BASE_ENIGH
BASE_GASTOS = os.environ.get(
    "ENIGH_GASTOS_DIR",
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "..", "raw", "enigh_gastos"),
)

BECAS = {
    "Recibe la beca de discapacidad": {
        2020: ["P105"], 2022: ["P105"], 2024: ["P105"],
    },
    "Recibe la pensión de adultos mayores": {
        2020: ["P104"], 2022: ["P104"], 2024: ["P104"],
    },
}

# Desglose por concepto: agrupa las claves finas bajo un nombre legible.
CONCEPTOS_GASTO = {
    "Lentes y apoyos visuales": {
        2022: ["J065"], 2024: ["061311", "061312"],
    },
    "Aparatos para sordera": {
        2022: ["J066"], 2024: ["061320"],
    },
    "Sillas de ruedas, andaderas y movilidad": {
        2022: ["J067"], 2024: ["061331", "061332", "061336", "061337"],
    },
    "Prótesis, ortesis y otros dispositivos de apoyo": {
        2022: [], 2024: ["061333", "061334", "061335", "061338"],
    },
    "Reparación y renta de aparatos": {
        2022: ["J068"], 2024: ["061401", "061402"],
    },
    "Cuidado de enfermos y terapias": {
        2022: ["J069"], 2024: ["062321"],
    },
    "Educación especial": {
        2022: ["E010"], 2024: ["101015", "101025", "102005", "103005"],
    },
    "Residencias y protección social": {
        2022: [], 2024: ["133022", "133092"],
    },
}

# El indicador combinado ("gasta en algo asociado a discapacidad") es la
# unión de todas las claves de todos los conceptos de arriba: se arma solo,
# para que nunca quede desincronizado si se agrega o quita un concepto.
GASTOS_DISC = {
    year: sorted({c for porAnio in CONCEPTOS_GASTO.values()
                  for c in porAnio.get(year, [])})
    for year in (2020, 2022, 2024)
}


def _norm_claves(serie):
    return serie.astype(str).str.strip().str.upper()


def _marcar_persona(pob, llaves_hogar):
    """
    `llaves_hogar` es un set de 'folioviv|foliohog' que cumplen una condición
    de hogar. Devuelve una Serie booleana alineada con `pob`: True si la
    PERSONA vive en uno de esos hogares. Así la condición de hogar se hereda
    a cada persona, sin cambiar la unidad de análisis del resto del tablero.
    """
    llave_persona = pob["folioviv"] + "|" + pob["foliohog"]
    return llave_persona.isin(llaves_hogar)


def indicadores(pob, year):
    fuente = "ENIGH (INEGI)"
    llaves = ["anio", "sexo", "disc", "entidad", "rango_edad", "tipo_discapacidad"]
    pob = _enigh.explotar_tipo_discapacidad(pob)
    filas = []

    for k in ("folioviv", "foliohog"):
        pob[k] = pob[k].astype(str).str.strip()

    def agrega(marcados, indicador, universo):
        base = pob.copy()
        base["_num"] = _marcar_persona(base, marcados)
        g = base.groupby(llaves, dropna=True, observed=True).apply(
            lambda x: pd.Series({
                "num": float(x.loc[x["_num"], "factor"].sum()),
                "den": float(x["factor"].sum()),
                "casos": int(len(x)),
            }), include_groups=False).reset_index()
        g["tema"] = "apoyos"
        g["indicador"] = indicador
        g["fuente"] = fuente
        g["universo"] = universo
        filas.append(g)

    def agrega_monto(montos_por_hogar, indicador):
        """
        `montos_por_hogar`: dict {'folioviv|foliohog': monto_trimestral}.
        num = masa de gasto ponderada, den = población ponderada, ambos
        calculados SOLO entre personas cuyo hogar gastó más de cero: es el
        mismo criterio que "Ingreso laboral mensual promedio" en
        enigh.csv.py, para que num/den dé "cuánto gasta el que gasta".
        """
        llave_persona = pob["folioviv"] + "|" + pob["foliohog"]
        monto = llave_persona.map(montos_por_hogar).fillna(0.0)
        base = pob[monto > 0].copy()
        if not len(base):
            return
        base["_masa"] = monto[monto > 0] * base["factor"]
        g = base.groupby(llaves, dropna=True, observed=True).apply(
            lambda x: pd.Series({
                "num": float(x["_masa"].sum()),
                "den": float(x["factor"].sum()),
                "casos": int(len(x)),
            }), include_groups=False).reset_index()
        g["tema"] = "apoyos"
        g["indicador"] = indicador
        g["fuente"] = fuente
        g["universo"] = "Personas de 18 años o más cuyo hogar gasta en esto"
        filas.append(g)

    # --- Becas, desde la tabla de ingresos ---------------------------------
    ruta_ing = os.path.join(BASE_ENIGH, f"Bases{year}", f"ingresos{year}.csv")
    if os.path.exists(ruta_ing):
        ing = pd.read_csv(ruta_ing, low_memory=False, dtype={"folioviv": str})
        ing.columns = (ing.columns.str.replace("﻿", "", regex=False)
                       .str.lower().str.strip())
        ing["clave_n"] = _norm_claves(ing["clave"])
        for k in ("folioviv", "foliohog"):
            ing[k] = ing[k].astype(str).str.strip()
        ing["_llave"] = ing["folioviv"] + "|" + ing["foliohog"]

        for nombre, porAnio in BECAS.items():
            claves = [c.upper() for c in porAnio.get(year, [])]
            marcados = set(ing.loc[ing["clave_n"].isin(claves), "_llave"])
            if not marcados:
                print(f"[aviso] ENIGH {year}: sin registros de {claves} "
                      f"para '{nombre}'.", file=sys.stderr)
                continue
            agrega(marcados, nombre, "Personas de 18 años o más")
    else:
        print(f"[aviso] ENIGH {year}: falta {ruta_ing}; se omiten becas.",
              file=sys.stderr)

    # --- Gasto asociado a la discapacidad: tasa + monto promedio -----------
    ruta_gas = os.path.join(BASE_GASTOS, str(year), "gastoshogar.csv")
    claves_g = [c.upper() for c in GASTOS_DISC.get(year, [])]
    if claves_g and os.path.exists(ruta_gas):
        gas = pd.read_csv(ruta_gas, low_memory=False, dtype={"folioviv": str})
        gas.columns = (gas.columns.str.replace("﻿", "", regex=False)
                       .str.lower().str.strip())
        gas["clave_n"] = _norm_claves(gas["clave"])
        for k in ("folioviv", "foliohog"):
            gas[k] = gas[k].astype(str).str.strip()
        gas["_llave"] = gas["folioviv"] + "|" + gas["foliohog"]

        sel = gas[gas["clave_n"].isin(claves_g)]
        if len(sel):
            agrega(
                set(sel["_llave"]),
                "Su hogar gasta en aparatos o cuidados por discapacidad",
                "Personas de 18 años o más")
            # gasto_tri: gasto trimestral estandarizado por la ENIGH a precios
            # de AGOSTO DE SU PROPIA EDICIÓN. Eso lo deja comparable dentro de
            # un año pero NO entre ediciones, así que aquí se lleva al año base
            # como el resto de los montos. Viene como texto (a veces con
            # blancos): forzar a numérico o el groupby suma cadenas.
            sel = sel.copy()
            sel["gasto_tri"] = pd.to_numeric(sel["gasto_tri"], errors="coerce").fillna(0.0)
            sel["gasto_tri"] = sel["gasto_tri"] * deflactor.factor(year)
            montos = sel.groupby("_llave")["gasto_tri"].sum().to_dict()
            agrega_monto(
                montos, "Gasto trimestral en aparatos o cuidados por discapacidad")
        else:
            print(f"[aviso] ENIGH {year}: ninguna clave de gasto "
                  f"{claves_g} apareció en los datos.", file=sys.stderr)

        # Desglose por concepto: mismo patrón, una tasa por concepto.
        for concepto, porAnio in CONCEPTOS_GASTO.items():
            claves_c = [c.upper() for c in porAnio.get(year, [])]
            if not claves_c:
                continue
            sel_c = gas[gas["clave_n"].isin(claves_c)]
            if len(sel_c):
                agrega(set(sel_c["_llave"]), f"Gasto en: {concepto}",
                       "Personas de 18 años o más")
    elif claves_g:
        print(f"[aviso] ENIGH {year}: falta la tabla de gastos; "
              "se omite el gasto por discapacidad.", file=sys.stderr)

    return filas


def main():
    filas = []
    for year in _enigh.ANIOS_ENIGH:
        pob = _enigh.cargar_poblacion(year)
        filas.extend(indicadores(pob, year))
        print(f"[ok] ENIGH {year}: apoyos y gasto", file=sys.stderr)

    if not filas:
        raise SystemExit("No se generó ningún indicador de apoyos.")
    escribir(filas)


if __name__ == "__main__":
    main()

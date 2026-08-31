"""
enigh_transporte.csv.py: Gasto en taxi, apps de viaje y transporte público.

Por qué este tema tiene sentido en un tablero de discapacidad y género: para
una persona con discapacidad el taxi no siempre es una alternativa cara al
camión, sino el ÚNICO medio utilizable cuando el transporte público de su
ciudad no es accesible (sin rampa, sin espacio para silla, con escalones al
abordar). Cuando eso pasa, el gasto en taxi deja de ser un lujo y se vuelve
un sobrecosto forzado de moverse — un costo que quien no tiene discapacidad
simplemente no paga. Por eso aquí el transporte público se reporta al lado,
como contraste: la pregunta no es "¿quién gasta más en taxi?" sino "¿quién
sustituye transporte público por taxi, y cuánto le cuesta eso?".

Igual que en enigh_apoyos.csv.py, el gasto se registra a nivel HOGAR (una
fila de gasto por hogar, nunca "esta persona pagó este viaje"). La condición
del hogar se hereda a cada persona que vive ahí, y la cifra se lee como
"personas que viven en un hogar que gasta en X", agrupadas por su propio
sexo y discapacidad — nunca como "personas con discapacidad que pagaron su
propio taxi".

--- Claves verificadas contra el catálogo oficial (Claves ENIGH.xlsx) -----

Subtema TRANSPORTE PÚBLICO. El catálogo mapea la clave alfanumérica de
2020/2022 con la numérica de seis dígitos de 2024. Frecuencias verificadas
contra los microdatos (número de registros de gasto, no de hogares):

  TAXI Y APPS
  B005   / 073221   Taxi, radio-taxi (sitio)             (n=3392 / 2299)
  --     / 073222   Uber, DiDi y similares               (n=  -- /  855)

  TRANSPORTE PÚBLICO (contraste)
  B001   / 073121   Metro o tren ligero                  (n=  66 /  171)
  --     / 073122   Tren ligero (desglosado en 2024)     (n=  -- /   20)
  --     / 073111   Tren suburbano (nuevo en 2024)       (n=  -- /   11)
  B002   / 073213   Autobús                              (n=1732 / 1787)
  B003   / 073123   Trolebús o metrobús                  (n=  56 /   58)
  --     / 073214   Metrobús (desglosado en 2024)        (n=  -- /  257)
  B004   / 073215   Colectivo, combi o microbús          (n=1931 / 1627)

OJO — la ruptura de serie de 2024, que NO se puede ignorar al leer la
gráfica: la clave de Uber/DiDi (073222) EXISTE SOLO DESDE 2024. El INEGI la
separó ese año; antes, un viaje de aplicación se capturaba dentro de "taxi"
o no se distinguía del todo. Por eso:

  - "Gasta en taxi o aplicación de viaje" une taxi + apps en las tres
    ediciones. Es el indicador comparable en el tiempo, porque en 2020 y
    2022 la unión es simplemente B005 y en 2024 es 073221 + 073222.
  - "Gasta en aplicación de viaje (Uber, DiDi)" se publica SOLO para 2024,
    sin serie histórica. No se rellena con ceros hacia atrás: un cero
    inventado diría "nadie usaba apps en 2022", que es falso — lo que pasa
    es que la encuesta no lo preguntaba por separado.

Deliberadamente EXCLUIDOS del transporte público de contraste:
  - Autobús foráneo (B006 / 073212) y otros transportes (B007 / 073290):
    son viajes entre ciudades o medios sueltos (lancha, peaje), no el
    traslado cotidiano urbano que compite con el taxi.
  - Todo el subtema TRANSPORTE genérico (avión, mudanza, autopista,
    ferroviario): no es movilidad cotidiana.
  - Funicular/teleférico/cablebús (073600, n=4): frecuencia demasiado baja
    para sostener una estimación, y no existe antes de 2024.

--- El monto del taxi vive en OTRA columna, y eso dice algo ---------------

Verificado contra los microdatos 2024: la ENIGH parte el monto del gasto en
dos columnas según `tipo_gasto`. G1 (gasto monetario, lo que el hogar pagó
de su bolsillo) va en `gasto_tri`; G3 y G5 (no monetario: lo pagó otra
persona, vino como prestación del trabajo o como regalo) van en
`gas_nm_tri`; G6 puede traer ambas.

Para el taxi la proporción es contundente: de 3,154 registros en 2024, solo
4 tienen `gasto_tri` y 2,497 son G5. Leer únicamente `gasto_tri` —que es lo
que basta en el gasto por discapacidad de enigh_apoyos.csv.py, casi todo
G1— dejaría este indicador prácticamente vacío sin lanzar ningún error.

Que el taxi sea mayoritariamente no monetario no es ruido a corregir: es
parte del hallazgo. Buena parte de los viajes de quien no puede usar el
transporte público los paga alguien más — un familiar, un programa, el
trabajo. Por eso el monto suma AMBAS columnas: la pregunta es cuánto cuesta
mover a esa persona, no solo cuánto salió de su propia cartera.

--- El monto promedio no es una tasa -------------------------------------

"Gasto trimestral promedio en taxi o aplicación" usa el mismo criterio que
el gasto por discapacidad en enigh_apoyos.csv.py: num = masa de gasto
ponderada, den = población ponderada de quienes SÍ gastaron, así que num/den
da un promedio en pesos, no un porcentaje. Se calcula solo entre personas
cuyo hogar gastó más de cero, porque la pregunta es "cuánto gasta el que
gasta", no "cuánto gasta la población en promedio".

Los montos van DEFLACTADOS al año base (ver deflactor.py): cada edición trae
pesos de su propio año y compararlos sin ajustar convierte inflación en
"aumento del gasto". Las tasas (porcentaje de hogares que gastan) no se
deflactan: no son dinero.
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

BASE_GASTOS = os.environ.get(
    "ENIGH_GASTOS_DIR",
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "..", "raw", "enigh_gastos"),
)

# Taxi de sitio y aplicaciones de viaje. La unión es el indicador comparable
# entre ediciones (ver la nota de ruptura de serie en el docstring).
TAXI_Y_APPS = {
    2020: ["B005"], 2022: ["B005"], 2024: ["073221", "073222"],
}

# Solo aplicaciones, exclusivo de 2024: antes no existía la clave.
SOLO_APPS = {
    2020: [], 2022: [], 2024: ["073222"],
}

# Transporte público urbano cotidiano, como contraste del taxi.
TRANSPORTE_PUBLICO = {
    2020: ["B001", "B002", "B003", "B004"],
    2022: ["B001", "B002", "B003", "B004"],
    2024: ["073121", "073122", "073111", "073213", "073123", "073214",
           "073215"],
}


def _norm_claves(serie):
    return serie.astype(str).str.strip().str.upper()


def _marcar_persona(pob, llaves_hogar):
    """
    `llaves_hogar` es un set de 'folioviv|foliohog' que cumplen la condición
    de hogar. Devuelve una Serie booleana alineada con `pob`: True si la
    PERSONA vive en uno de esos hogares. Mismo patrón que enigh_apoyos.
    """
    llave_persona = pob["folioviv"] + "|" + pob["foliohog"]
    return llave_persona.isin(llaves_hogar)


def indicadores(pob, year):
    fuente = "ENIGH (INEGI)"
    llaves = ["anio", "sexo", "disc", "entidad", "rango_edad",
              "tipo_discapacidad", "decil"]
    pob = _enigh.explotar_dimensiones(pob)
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
        g = _em.agrega_error(g, base, llaves, "_num")
        g["tema"] = "gastos"
        g["indicador"] = indicador
        g["fuente"] = fuente
        g["universo"] = universo
        filas.append(g)

    def agrega_monto(montos_por_hogar, indicador):
        """
        num = masa de gasto ponderada, den = población ponderada, ambos solo
        entre personas cuyo hogar gastó más de cero, para que num/den dé
        "cuánto gasta el que gasta" (ver docstring).
        """
        llave_persona = pob["folioviv"] + "|" + pob["foliohog"]
        monto = llave_persona.map(montos_por_hogar).fillna(0.0)
        base = pob[monto > 0].copy()
        if not len(base):
            return
        # `.values` (posicional) y NO `monto[monto > 0] * base["factor"]`
        # (por índice): explotar_dimensiones() duplica el índice de `pob`
        # —cada persona aparece una vez por dominio y una por decil—, así que
        # una multiplicación alineada por índice hace producto cartesiano
        # entre filas homónimas y devuelve una masa que no corresponde a
        # ninguna persona. El síntoma es silencioso: no lanza error, solo
        # colapsa el indicador a un puñado de filas con montos absurdos.
        base["_masa"] = monto[monto > 0].values * base["factor"].values
        # El monto POR PERSONA (sin multiplicar por el factor) es la variable
        # que necesita el estimador de error: la razón que se publica es
        # masa/población, y su varianza se calcula sobre el valor individual,
        # no sobre el producto ya ponderado.
        base["_masa_unit"] = monto[monto > 0].values
        g = base.groupby(llaves, dropna=True, observed=True).apply(
            lambda x: pd.Series({
                "num": float(x["_masa"].sum()),
                "den": float(x["factor"].sum()),
                "casos": int(len(x)),
            }), include_groups=False).reset_index()
        g = _em.agrega_error(g, base, llaves, "_masa_unit")
        g["tema"] = "gastos"
        g["indicador"] = indicador
        g["fuente"] = fuente
        g["universo"] = "Personas de 18 años o más cuyo hogar gasta en esto"
        filas.append(g)

    ruta_gas = os.path.join(BASE_GASTOS, str(year), "gastoshogar.csv")
    if not os.path.exists(ruta_gas):
        print(f"[aviso] ENIGH {year}: falta {ruta_gas}; se omite transporte.",
              file=sys.stderr)
        return filas

    gas = pd.read_csv(ruta_gas, low_memory=False, dtype={"folioviv": str})
    gas.columns = (gas.columns.str.replace("﻿", "", regex=False)
                   .str.lower().str.strip())
    gas["clave_n"] = _norm_claves(gas["clave"])
    for k in ("folioviv", "foliohog"):
        gas[k] = gas[k].astype(str).str.strip()
    gas["_llave"] = gas["folioviv"] + "|" + gas["foliohog"]

    def seleccion(claves_por_anio):
        claves = [c.upper() for c in claves_por_anio.get(year, [])]
        if not claves:
            return None
        return gas[gas["clave_n"].isin(claves)]

    def montos_por_hogar(sel):
        """
        Suma el gasto trimestral por hogar, deflactado al año base.

        Suma DOS columnas, no una: verificado contra los microdatos 2024, la
        ENIGH parte el monto según `tipo_gasto`. G1 (gasto monetario) lo pone
        en `gasto_tri` y deja `gas_nm_tri` vacío; G3 y G5 (no monetario:
        transporte pagado por otra persona, prestación del trabajo, regalo)
        lo ponen en `gas_nm_tri` y dejan `gasto_tri` vacío; G6 puede traer
        ambos. Leer solo `gasto_tri` —lo natural, y lo que hace el loader de
        aparatos, donde sí basta porque ese gasto es casi todo G1— aquí
        vaciaría el indicador: de las 3,154 filas de taxi de 2024, solo 4
        tienen `gasto_tri`, y 2,497 son G5.

        Que el taxi sea mayoritariamente no monetario no es un defecto del
        dato, es parte del hallazgo: buena parte de los viajes de quien no
        puede usar el transporte público los paga alguien más.

        Ambas columnas llegan como texto con blancos: `to_numeric` con
        `coerce` y `fillna(0)` antes de sumar, o el groupby concatena
        cadenas.
        """
        sel = sel.copy()
        monetario = pd.to_numeric(sel["gasto_tri"], errors="coerce").fillna(0.0)
        no_monetario = pd.to_numeric(sel["gas_nm_tri"], errors="coerce").fillna(0.0)
        sel["_total"] = (monetario + no_monetario) * deflactor.factor(year)
        return sel.groupby("_llave")["_total"].sum().to_dict()

    # --- Taxi y aplicaciones: tasa + monto promedio ------------------------
    sel = seleccion(TAXI_Y_APPS)
    if sel is not None and len(sel):
        agrega(set(sel["_llave"]),
               "Su hogar gasta en taxi o aplicación de viaje",
               "Personas de 18 años o más")
        agrega_monto(montos_por_hogar(sel),
                     "Gasto trimestral en taxi o aplicación de viaje")
    elif sel is not None:
        print(f"[aviso] ENIGH {year}: ninguna clave de taxi apareció.",
              file=sys.stderr)

    # --- Solo aplicaciones (2024 en adelante) ------------------------------
    sel_app = seleccion(SOLO_APPS)
    if sel_app is not None and len(sel_app):
        agrega(set(sel_app["_llave"]),
               "Su hogar gasta en aplicación de viaje (Uber, DiDi)",
               "Personas de 18 años o más")

    # --- Transporte público, como contraste --------------------------------
    sel_tp = seleccion(TRANSPORTE_PUBLICO)
    if sel_tp is not None and len(sel_tp):
        agrega(set(sel_tp["_llave"]),
               "Su hogar gasta en transporte público",
               "Personas de 18 años o más")
        agrega_monto(montos_por_hogar(sel_tp),
                     "Gasto trimestral en transporte público")

    return filas


def main():
    filas = []
    for year in _enigh.ANIOS_ENIGH:
        pob = _enigh.cargar_poblacion(year)
        filas.extend(indicadores(pob, year))
        print(f"[ok] ENIGH {year}: transporte", file=sys.stderr)

    if not filas:
        raise SystemExit("No se generó ningún indicador de transporte.")
    escribir(filas)


if __name__ == "__main__":
    main()

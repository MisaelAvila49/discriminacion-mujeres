"""
enigh_educacion.csv.py: Escolaridad y jefatura del hogar según la ENIGH.

Dos bloques que la ENIGH permite y que las demás fuentes no cubren igual:

1. ESCOLARIDAD. La tabla de población trae el nivel aprobado (`nivelaprob`,
   de 0 = ninguno a 9 = doctorado), el alfabetismo y la asistencia escolar.
   A diferencia de la ENADIS, aquí hay tres ediciones y representatividad
   estatal, así que la serie se puede seguir en el tiempo y por entidad.

2. JEFATURA DEL HOGAR. `parentesco = 101` identifica a la persona jefa del
   hogar, y se verificó contra los datos que hay exactamente una por hogar
   (90,102 jefaturas en 90,102 hogares en 2022). El 31.3% son mujeres, cifra
   que coincide con lo que publica el INEGI.

   Este indicador se lee al revés que los demás del tablero: no mide una
   carencia sino una posición. Una jefatura femenina alta no es "mejor" ni
   "peor" por sí sola; en México suele reflejar hogares sin cónyuge varón, y
   por eso la nota del tablero evita interpretarla como logro o como problema.

Códigos verificados contra el diccionario oficial y las frecuencias:
  nivelaprob  0 ninguno · 1 preescolar · 2 primaria · 3 secundaria ·
              4 preparatoria · 5 normal · 6 carrera técnica · 7 profesional ·
              8 maestría · 9 doctorado. El blanco es no especificado.
  alfabetism  1 sabe leer y escribir, 2 no
  asis_esc    1 asiste a la escuela, 2 no
  parentesco  101 = jefe o jefa del hogar
"""

import sys
import os
import importlib.util

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils_enadis import escribir  # noqa: E402

_ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "enigh.csv.py")
_spec = importlib.util.spec_from_file_location("enigh_base", _ruta)
_enigh = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_enigh)

# Nivel aprobado a partir del cual se considera educación media superior
# completa o más. Se toma 4 (preparatoria) como corte porque es el umbral que
# usa la política educativa para hablar de rezago.
NIVEL_MEDIA_SUPERIOR = 4


def main():
    import pandas as pd

    filas = []
    llaves = ["anio", "sexo", "disc", "entidad", "rango_edad", "tipo_discapacidad"]

    def agrega(base, condicion, tema, nombre, universo):
        b = base.copy()
        b["_num"] = condicion.fillna(False).astype(bool)
        g = b.groupby(llaves, dropna=True, observed=True).apply(
            lambda x: pd.Series({
                "num": float(x.loc[x["_num"], "factor"].sum()),
                "den": float(x["factor"].sum()),
                "casos": int(len(x)),
            }), include_groups=False).reset_index()
        g["tema"] = tema
        g["indicador"] = nombre
        g["fuente"] = "ENIGH (INEGI)"
        g["universo"] = universo
        filas.append(g)

    for year in _enigh.ANIOS_ENIGH:
        pob = _enigh.cargar_poblacion(year)
        pob = _enigh.explotar_tipo_discapacidad(pob)

        # --- Escolaridad ---------------------------------------------------
        if "nivelaprob" in pob.columns:
            niv = pd.to_numeric(pob["nivelaprob"], errors="coerce")
            # El no especificado sale del denominador: contarlo como "sin
            # estudios" inventaría rezago que nadie declaró.
            base = pob[niv.notna()].copy()
            nivb = niv[niv.notna()]
            agrega(base, nivb.ge(NIVEL_MEDIA_SUPERIOR),
                   "educacion", "Educación media superior o más",
                   "Personas de 18 años o más")
            agrega(base, nivb.eq(0),
                   "educacion", "Sin ningún grado de escolaridad",
                   "Personas de 18 años o más")

        # Ojo: en 2024 estas columnas llegan como "1.0"/"2.0" porque pandas
        # las infiere como float, mientras que en 2020 y 2022 son "1"/"2".
        # Comparar contra el texto "1" descartaba 2024 entero en silencio, sin
        # error ni advertencia: la conversión numérica evita ese fallo.
        if "alfabetism" in pob.columns:
            alf = pd.to_numeric(pob["alfabetism"], errors="coerce")
            base = pob[alf.isin([1, 2])].copy()
            agrega(base, alf[alf.isin([1, 2])].eq(2),
                   "educacion", "No sabe leer ni escribir (ENIGH)",
                   "Personas de 18 años o más")

        if "asis_esc" in pob.columns:
            asi = pd.to_numeric(pob["asis_esc"], errors="coerce")
            base = pob[asi.isin([1, 2]) & pob["edad"].between(18, 29)].copy()
            if len(base):
                agrega(base, asi[base.index].eq(1),
                       "educacion", "Asiste a la escuela (18 a 29 años, ENIGH)",
                       "Personas de 18 a 29 años")

        # --- Jefatura del hogar --------------------------------------------
        # Universo: TODA la población adulta, para leer la cifra como "qué
        # proporción de cada grupo encabeza un hogar". El denominador no son
        # los hogares sino las personas, que es lo que hace comparable el dato
        # con el resto del tablero.
        if "parentesco" in pob.columns:
            par = pd.to_numeric(pob["parentesco"], errors="coerce")
            base = pob[par.notna()].copy()
            agrega(base, par[par.notna()].eq(101),
                   "hogar", "Es jefa o jefe del hogar",
                   "Personas de 18 años o más")

        print(f"[ok] ENIGH {year}: educación y jefatura", file=sys.stderr)

    if not filas:
        raise SystemExit("No se generó ningún indicador de educación.")
    escribir(filas)


if __name__ == "__main__":
    main()

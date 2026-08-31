"""
endireh_agresor_tipo.csv.py: Cruce de quién agrede con qué tipo de violencia.

Tercera capa sobre los otros dos loaders de ENDIREH. `endireh_ambito` dice
DÓNDE ocurre la violencia; `endireh_agresor` dice QUIÉN la ejerce; este dice
QUÉ TIPO de violencia ejerce cada persona.

La combinación es la que da contenido a una política. "Las mujeres con
discapacidad viven más violencia familiar" no dice qué hacer. "El hijo que
las cuida ejerce sobre todo violencia económica —le usa el dinero, le quita
los bienes— mientras que la pareja ejerce sexual" sí orienta: son dos
problemas distintos, con dos respuestas distintas.

--- Cómo se arma el cruce -------------------------------------------------

La ENDIREH no tiene una columna "tipo de violencia" junto al agresor. Lo que
tiene es una columna de agresor POR CADA ACTO concreto (la manoseó, la
pateó, le quitó bienes), y cada acto pertenece a un tipo. El cruce se
construye mapeando cada acto a su tipo, con el TEXTO del diccionario oficial
de cada sección — no adivinando por el número de la pregunta.

Ejemplo del ámbito familiar (sección XI, 20 actos):

  P11_2_3   violación sexual                      -> sexual
  P11_2_5   la pateó o golpeó                     -> física
  P11_2_15  usó o sustrajo su dinero              -> económica
  P11_2_7   la ofendió o humilló por ser mujer    -> psicológica

Una mujer cuenta en la celda (padre, económica) si el código de padre aparece
en cualquiera de las columnas de agresor de cualquier acto económico. Igual
que en `endireh_agresor`, cuenta UNA vez por celda aunque haya varios actos:
la cifra es "porcentaje de mujeres que sufrieron violencia económica de su
padre", no número de incidentes.

--- Solo la ventana de 12 meses -------------------------------------------

En los ámbitos laboral y escolar la ENDIREH pregunta el agresor DOS veces:
una a lo largo de la vida laboral o escolar, y otra acotada a los últimos
doce meses.

  laboral   P8_10_*  a lo largo de la vida    /  P8_12_*  últimos 12 meses
  escolar   P7_7_*   a lo largo de la vida    /  P7_9_*   últimos 12 meses

Este loader usa SOLO la ventana de doce meses, para que el cruce sea
comparable con el resto del tablero, que trabaja con `*_12M`. Mezclar ambas
ventanas inflaría las cifras y las volvería incomparables con la sección de
ámbitos, además de sesgar por edad: la violencia "a lo largo de la vida"
crece mecánicamente con los años vividos, y la población con discapacidad es
más vieja.

(Nota para una ronda futura: `endireh_agresor.csv.py` sí junta las dos
ventanas, porque detecta las columnas por su catálogo sin distinguir el
periodo. Sus cifras deben leerse como "alguna vez", no como doce meses.)

--- Qué NO se publica -----------------------------------------------------

El ámbito de pareja queda fuera: ahí el agresor es la pareja por definición,
así que el cruce sería una sola fila y no aporta nada que la sección de
tipos no diga ya.

Las celdas con menos de 30 casos sin expandir no se emiten. Con 13 agresores
por 4 tipos, muchas combinaciones (un yerno ejerciendo violencia sexual) se
quedan en un puñado de observaciones, y una tasa calculada sobre eso es
ruido con apariencia de dato.

Códigos de agresor verificados: los mismos de endireh_agresor.csv.py, que se
importan de ahí para no mantener dos listas sincronizadas a mano.
"""

import sys
import os
import importlib.util
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils_enadis import escribir  # noqa: E402

_ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "endireh.csv.py")
_spec = importlib.util.spec_from_file_location("endireh_base", _ruta)
_endireh = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_endireh)

_ruta_ag = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "endireh_agresor.csv.py")
_spec_ag = importlib.util.spec_from_file_location("endireh_ag", _ruta_ag)
_agresor = importlib.util.module_from_spec(_spec_ag)
_spec_ag.loader.exec_module(_agresor)

ANIO = _endireh.ANIO
COLS_DISC = _endireh.COLS_DISC
DISC_POSITIVOS = _endireh.DISC_POSITIVOS

# Mapa acto -> tipo de violencia, hecho leyendo la descripción de cada acto
# en el diccionario oficial de cada sección. La llave es el número del acto
# dentro de su bloque de preguntas.
#
# Ámbito familiar, sección XI (bloque P11_2_*), 20 actos.
ACTOS_FAMILIAR = {
    1: "Psicológica", 7: "Psicológica", 12: "Psicológica",
    14: "Psicológica", 17: "Psicológica", 20: "Psicológica",
    2: "Sexual", 3: "Sexual", 4: "Sexual", 13: "Sexual",
    18: "Sexual", 19: "Sexual",
    5: "Física", 10: "Física", 11: "Física",
    6: "Económica", 8: "Económica", 9: "Económica",
    15: "Económica", 16: "Económica",
}

# Ámbito laboral, sección VIII, bloque P8_12_* (últimos 12 meses).
ACTOS_LABORAL = {
    6: "Psicológica", 7: "Psicológica", 12: "Psicológica",
    17: "Psicológica", 18: "Psicológica",
    4: "Sexual", 5: "Sexual", 10: "Sexual", 11: "Sexual",
    13: "Sexual", 14: "Sexual", 15: "Sexual", 16: "Sexual",
    8: "Física", 9: "Física", 19: "Física",
}

# Ámbito escolar, sección VII, bloque P7_9_* (últimos 12 meses).
ACTOS_ESCOLAR = {
    12: "Psicológica", 13: "Psicológica", 16: "Psicológica",
    18: "Psicológica",
    5: "Sexual", 7: "Sexual", 8: "Sexual", 9: "Sexual", 10: "Sexual",
    11: "Sexual", 14: "Sexual", 15: "Sexual", 17: "Sexual",
    6: "Física",
}

AMBITOS = [
    {
        "clave": "familiar",
        "seccion": "TB_SEC_XI",
        "bloque": "P11_2_",
        "actos": ACTOS_FAMILIAR,
        "universo": None,
        "universo_texto": "Mujeres de 15 años o más",
        "etiqueta": "Violencia {tipo} de {agresor} (familiar)",
        "agresores": _agresor.AMBITOS[0]["agresores"],
    },
    {
        "clave": "laboral",
        "seccion": "TB_SEC_VIII",
        "bloque": "P8_12_",
        "actos": ACTOS_LABORAL,
        "universo": "POB_L_12M",
        "universo_texto": "Mujeres de 15 años o más que trabajaron en los últimos 12 meses",
        "etiqueta": "Violencia {tipo} de {agresor} (trabajo)",
        "agresores": _agresor.AMBITOS[1]["agresores"],
    },
    {
        "clave": "escolar",
        "seccion": "TB_SEC_VII",
        "bloque": "P7_9_",
        "actos": ACTOS_ESCOLAR,
        "universo": "POB_E_12M",
        "universo_texto": "Mujeres de 15 años o más que asistieron a la escuela en los últimos 12 meses",
        "etiqueta": "Violencia {tipo} de {agresor} (escuela)",
        "agresores": _agresor.AMBITOS[2]["agresores"],
    },
]

MIN_CASOS_CELDA = 30


def main():
    disc = _endireh._tabla(ANIO, "TB_SEC_XIX")
    sdem = _endireh._tabla(ANIO, "TSDem")
    vd = _endireh._tabla(ANIO, "TB_VD")

    llaves = ["ID_VIV", "ID_PER", "UPM", "VIV_SEL", "HOGAR", "N_REN"]

    presentes = [c for c in COLS_DISC if c in disc.columns]
    if not presentes:
        raise SystemExit(
            f"ENDIREH {ANIO}: no se encontraron las columnas {COLS_DISC}.")
    marca = disc[presentes].isin(DISC_POSITIVOS).any(axis=1)
    disc_min = disc[llaves].copy()
    disc_min["disc"] = marca.map({True: "Con discapacidad",
                                  False: "Sin discapacidad"})

    cols_vd = llaves + ["FAC_MUJ", "NOM_ENT", "POB_L_12M", "POB_E_12M"]
    persona = vd[[c for c in cols_vd if c in vd.columns]].copy()
    persona = persona.merge(disc_min, on=llaves, how="inner")
    persona = persona.merge(sdem[llaves + ["EDAD"]], on=llaves, how="left")

    if len(persona) != len(vd):
        raise SystemExit(
            f"ENDIREH {ANIO}: la unión dejó {len(persona)} de {len(vd)} "
            "mujeres. Revisa las llaves antes de publicar.")

    persona["EDAD"] = pd.to_numeric(persona["EDAD"], errors="coerce")
    persona["rango_edad"] = persona["EDAD"].apply(_endireh._rango_edad)
    persona["factor"] = pd.to_numeric(persona["FAC_MUJ"],
                                      errors="coerce").fillna(0)
    persona["entidad"] = (persona["NOM_ENT"].astype(str).str.strip()
                          .map(_endireh._normalizar_entidad))
    persona["sexo"] = "Mujeres"
    persona["anio"] = ANIO

    llaves_grupo = ["anio", "sexo", "disc", "entidad", "rango_edad"]
    salida = []

    for amb in AMBITOS:
        tabla = _endireh._tabla(ANIO, amb["seccion"])

        # Columnas de agresor de este ámbito, agrupadas por TIPO de violencia
        # según el acto al que pertenecen. El nombre es
        # {bloque}{acto}_{n_agresor}, así que el número de acto es el
        # penúltimo segmento.
        por_tipo = {}
        for c in tabla.columns:
            if not c.startswith(amb["bloque"]):
                continue
            partes = c[len(amb["bloque"]):].split("_")
            if len(partes) != 2 or partes[1] not in ("1", "2", "3"):
                continue
            try:
                acto = int(partes[0])
            except ValueError:
                continue
            tipo = amb["actos"].get(acto)
            if tipo:
                por_tipo.setdefault(tipo, []).append(c)

        if not por_tipo:
            print(f"[aviso] {amb['clave']}: sin columnas para el bloque "
                  f"{amb['bloque']}; se omite.", file=sys.stderr)
            continue

        cols_todas = sorted({c for v in por_tipo.values() for c in v})
        agres = tabla[llaves].copy()
        for c in cols_todas:
            agres[c] = _agresor._a_numero(tabla[c])

        base = persona.merge(agres, on=llaves, how="left")

        if amb["universo"] and amb["universo"] in base.columns:
            base = base[_agresor._a_numero(base[amb["universo"]]).eq(1)]
        if not len(base):
            raise SystemExit(
                f"ENDIREH {ANIO}: el ámbito {amb['clave']} se quedó sin filas "
                "tras aplicar su universo.")

        emitidas = omitidas = 0
        for tipo, cols in sorted(por_tipo.items()):
            marcas = base[cols]
            for codigo, nombre in amb["agresores"].items():
                sub = base.copy()
                sub["_num"] = marcas.eq(codigo).any(axis=1)

                positivos = int(sub["_num"].sum())
                if positivos < MIN_CASOS_CELDA:
                    omitidas += 1
                    continue

                g = sub.groupby(llaves_grupo, dropna=True,
                                observed=True).apply(
                    lambda x: pd.Series({
                        "num": float(x.loc[x["_num"], "factor"].sum()),
                        "den": float(x["factor"].sum()),
                        "casos": int(len(x)),
                    }), include_groups=False).reset_index()
                g["tema"] = "agresor"
                g["indicador"] = amb["etiqueta"].format(tipo=tipo.lower(),
                                                        agresor=nombre)
                g["fuente"] = "ENDIREH (INEGI)"
                g["universo"] = amb["universo_texto"]
                salida.append(g)
                emitidas += 1

        print(f"[ok] ENDIREH {ANIO}: {amb['clave']}, "
              f"{len(por_tipo)} tipos x {len(amb['agresores'])} agresores, "
              f"{emitidas} celdas emitidas, {omitidas} omitidas por pocos "
              f"casos", file=sys.stderr)

    if not salida:
        raise SystemExit("ENDIREH agresor x tipo: no se generó nada.")

    escribir(salida)


if __name__ == "__main__":
    main()

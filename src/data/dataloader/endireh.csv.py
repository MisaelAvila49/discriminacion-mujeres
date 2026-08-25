"""
endireh.csv.py: Violencia contra las mujeres, por condición de discapacidad.

ENDIREH es la fuente más fuerte del tablero para violencia y autonomía, y la
única con representatividad estatal en esos temas. Tiene una restricción que
define cómo se puede usar:

  ENDIREH entrevista ÚNICAMENTE a mujeres de 15 años o más.

Por eso de las tres comparaciones del tablero, esta fuente solo sostiene una:
mujeres con discapacidad frente a mujeres sin discapacidad. No existe el
hombre como término de comparación, así que las páginas que usan ENDIREH
ocultan los otros dos pares en vez de dibujarlos vacíos (ver FUENTES en
src/components/comparacion.js).

Segunda restricción: el módulo de discapacidad (sección XIX) se levantó por
primera vez en 2021. En 2016 no hay forma de separar a las mujeres con y sin
discapacidad, así que esta fuente aporta un solo año al tablero. Se deja 2016
descargado y documentado porque sirve para la serie de violencia total (sin
corte por discapacidad), pero NO se emite aquí: mezclar un año con corte y
otro sin él en la misma gráfica es justo el error que se quiere evitar.

Códigos verificados contra los microdatos:
  P19_1_1..8  escala de severidad: 1 = no puede hacerlo, 2 = mucha dificultad,
              3 = poca dificultad, 4 = sin dificultad. Positivos = {1, 2},
              el mismo criterio que ENADIS 2022 y ENIGH 2020/2022.
  V*_12M      clasificación de violencia del propio INEGI en los últimos 12
              meses: 1 = sí, 2 = no, 9 = no especificado (sale del
              denominador). Se usa la tabla TB_VD ya clasificada en vez de
              recalcularla desde las preguntas sueltas.
  FAC_MUJ     factor de expansión de la mujer elegida.

Dos cifras de esta fuente que se leen mal si no se advierten:

  1. La prevalencia de discapacidad sale en 12.6%, contra ~6% en ENADIS,
     ENIGH y Censo. No es una contradicción: aquí el universo son mujeres de
     15 años o más (no la población adulta de ambos sexos), la discapacidad
     es más frecuente en mujeres y crece con la edad. Las prevalencias de
     fuentes distintas no son comparables entre sí; las comparaciones entre
     grupos dentro de una misma fuente sí lo son.

  2. La violencia sexual aparece MÁS BAJA en mujeres con discapacidad
     (19.0% contra 22.8%) en el agregado. Es una paradoja de Simpson y leerla
     al pie de la letra invierte la conclusión. Al abrir por rango de edad,
     las mujeres con discapacidad reportan MÁS violencia sexual en todos los
     grupos de edad menores de 60:

         18-29    61.6%  contra  39.1%   (+22.5 puntos)
         30-44    34.6%  contra  24.0%   (+10.6)
         45-59    19.0%  contra  13.2%   (+5.8)
         60+       5.3%  contra   5.6%   (-0.3)

     El agregado se invierte porque la discapacidad se concentra en el grupo
     de 60 y más, que es justo donde la violencia sexual reportada es más
     baja. La composición por edad, no la condición, produce el número.
     Lo mismo ocurre en menor grado con la violencia física.

     Consecuencia de diseño: el rango de edad NO es un filtro opcional en
     este tablero. Las páginas de violencia muestran el desglose por edad de
     forma predeterminada y el agregado sin controlar por edad lleva una
     advertencia, porque es un número que engaña.
"""

import sys
import os
import glob
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils_enadis import RANGOS_EDAD, ENTIDADES  # noqa: E402


def _normalizar_entidad(nombre):
    """
    ENDIREH trae los nombres de entidad en mayúsculas y sin acentos; el resto
    del tablero y el geojson del mapa los usan en formato de título y con
    acentos ("Ciudad de México", "Michoacán", "Nuevo León").

    No se puede resolver con .title(): produciría "Ciudad De México" y perdería
    los acentos que el original no trae. Se compara contra el catálogo oficial
    ignorando acentos, mayúsculas y espacios, y se devuelve la forma canónica.
    """
    import unicodedata

    def plano(t):
        t = unicodedata.normalize("NFD", str(t))
        t = "".join(c for c in t if unicodedata.category(c) != "Mn")
        # El .strip() también quita el \r: la tabla viene con saltos de línea
        # de Windows y el retorno de carro queda pegado al último campo.
        return t.upper().strip()

    objetivo = plano(nombre)
    for canonico in ENTIDADES.values():
        if plano(canonico) == objetivo:
            return canonico

    # Tres entidades vienen con su nombre oficial largo ("COAHUILA DE
    # ZARAGOZA", "MICHOACÁN DE OCAMPO", "VERACRUZ DE IGNACIO DE LA LLAVE"),
    # que no coincide con la forma corta del catálogo. Se resuelven por
    # prefijo antes de fallar.
    #
    # El orden por longitud descendente NO es cosmético: "BAJA CALIFORNIA" es
    # prefijo de "BAJA CALIFORNIA SUR", y probando del más corto al más largo,
    # Baja California Sur se clasificaría como Baja California.
    for canonico in sorted(ENTIDADES.values(), key=len, reverse=True):
        if objetivo.startswith(plano(canonico)):
            return canonico

    # Si aparece una entidad que no está en el catálogo, es mejor enterarse
    # que dejarla pasar y que luego no pinte en el mapa.
    raise ValueError(f"Entidad no reconocida en ENDIREH: {nombre!r}")

BASE_ENDIREH = os.environ.get(
    "ENDIREH_DIR",
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "..", "raw", "endireh"),
)

ANIO = 2021

# Columnas de dificultad de la sección XIX. Son ocho dominios; se toman los
# que existan para no romperse si una edición futura agrega o quita alguno.
COLS_DISC = [f"P19_1_{i}" for i in range(1, 9)]
DISC_POSITIVOS = {1, 2}

# Indicadores de violencia en los últimos 12 meses, con el nombre que se
# muestra en el tablero. Se prefiere el marco de 12 meses sobre "a lo largo de
# la vida" porque el de vida crece mecánicamente con la edad, y la población
# con discapacidad es más vieja: compararlos confundiría edad con condición.
INDICADORES_VD = [
    ("VTOT_12M", "Violencia total en los últimos 12 meses"),
    ("VPSI_12M", "Violencia psicológica en los últimos 12 meses"),
    ("VFIS_12M", "Violencia física en los últimos 12 meses"),
    ("VSEX_12M", "Violencia sexual en los últimos 12 meses"),
    ("VECO_12M", "Violencia económica o patrimonial en los últimos 12 meses"),
]


def _tabla(anio, nombre):
    patron = os.path.join(
        BASE_ENDIREH, str(anio), f"conjunto_de_datos_{nombre}",
        "conjunto_de_datos", "*.csv")
    encontrados = glob.glob(patron)
    if not encontrados:
        raise SystemExit(
            f"No se encontró la tabla {nombre} de ENDIREH {anio}. "
            "Revisa la descarga; ver README."
        )
    return pd.read_csv(encontrados[0], encoding="latin-1", low_memory=False)


def _rango_edad(edad):
    for lo, hi, etiqueta in RANGOS_EDAD:
        if lo <= edad <= hi:
            return etiqueta
    return None


def main():
    disc = _tabla(ANIO, "TB_SEC_XIX")
    vd = _tabla(ANIO, "TB_VD")
    sdem = _tabla(ANIO, "TSDem")

    llaves = ["ID_VIV", "ID_PER", "UPM", "VIV_SEL", "HOGAR", "N_REN"]

    # --- Condición de discapacidad -----------------------------------------
    presentes = [c for c in COLS_DISC if c in disc.columns]
    if not presentes:
        raise SystemExit(
            f"ENDIREH {ANIO}: no se encontraron las columnas {COLS_DISC}."
        )
    marca = disc[presentes].isin(DISC_POSITIVOS).any(axis=1)
    disc = disc[llaves + ["CVE_ENT", "NOM_ENT"]].copy()
    disc["disc"] = marca.map({True: "Con discapacidad", False: "Sin discapacidad"})

    # --- Edad, que vive en la tabla sociodemográfica ------------------------
    # TSDem lista a TODOS los residentes de la vivienda; la unión por las
    # llaves de persona se queda solo con la mujer elegida.
    sdem_m = sdem[llaves + ["EDAD"]].copy()

    base = vd.merge(disc, on=llaves, how="inner", suffixes=("", "_d"))
    base = base.merge(sdem_m, on=llaves, how="left")

    if len(base) != len(vd):
        raise SystemExit(
            f"ENDIREH {ANIO}: la unión dejó {len(base)} de {len(vd)} mujeres. "
            "Revisa las llaves antes de publicar."
        )

    base["EDAD"] = pd.to_numeric(base["EDAD"], errors="coerce")
    base["rango_edad"] = base["EDAD"].apply(_rango_edad)
    base["factor"] = pd.to_numeric(base["FAC_MUJ"], errors="coerce").fillna(0)
    # ENDIREH escribe los nombres de entidad en mayúsculas ("AGUASCALIENTES");
    # el resto de las fuentes y el geojson del mapa los traen en formato de
    # título ("Aguascalientes"). Se normalizan aquí para que el cruce con el
    # mapa y con las demás encuestas sea exacto y no por aproximación.
    base["entidad"] = (base["NOM_ENT"].astype(str).str.strip()
                       .map(_normalizar_entidad))
    # Todas las entrevistadas son mujeres: la llave de sexo es constante y se
    # deja explícita para que la salida tenga el mismo esquema que las demás.
    base["sexo"] = "Mujeres"
    base["anio"] = ANIO

    prev = (base["disc"] == "Con discapacidad").mean() * 100
    if not 2 <= prev <= 30:
        raise SystemExit(
            f"ENDIREH {ANIO}: prevalencia de discapacidad de {prev:.1f}%, "
            "fuera de rango. Revisa la escala de P19_1_*."
        )
    print(f"[ok] ENDIREH {ANIO}: {len(base):,} mujeres, "
          f"prevalencia de discapacidad {prev:.1f}%", file=sys.stderr)

    llaves_grupo = ["anio", "sexo", "disc", "entidad", "rango_edad"]
    salida = []
    for col, nombre in INDICADORES_VD:
        if col not in base.columns:
            print(f"[aviso] {col} no está en TB_VD; se omite.", file=sys.stderr)
            continue
        # El 9 (no especificado) sale del denominador.
        sub = base[base[col].isin([1, 2])].copy()
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
        g["universo"] = "Mujeres de 15 años o más"
        salida.append(g)

    if not salida:
        raise SystemExit("ENDIREH: no se generó ningún indicador.")

    todo = pd.concat(salida, ignore_index=True)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", newline="")
    todo[[
        "tema", "indicador", "anio", "sexo", "disc", "entidad", "rango_edad",
        "num", "den", "casos", "fuente", "universo",
    ]].to_csv(sys.stdout, index=False)


if __name__ == "__main__":
    main()

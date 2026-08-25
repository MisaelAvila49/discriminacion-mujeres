"""
enigh_tecnologia.csv.py: Brecha digital por sexo y condición de discapacidad.

Sustituye a la ENDUTIH para el tema de tecnología, por una razón de fondo:
la ENDUTIH no identifica la discapacidad de la persona. Solo la registra
cuando alguien la señala como LA razón principal para no usar internet,
computadora o celular, lo que deja fuera a quien tiene discapacidad y no usa
internet por falta de dinero. Ese proxy da 1.43% de prevalencia contra el ~6%
real, y no permite las tres comparaciones del tablero.

La ENIGH sí las permite: la tabla de hogares trae las variables de
conectividad y se une con la de población, que ya identifica sexo y
discapacidad a nivel persona. La unión es exacta (0 registros sin pareja en
las tres ediciones).

Lo que se mide es el acceso EN EL HOGAR, no el uso personal. Una persona con
conexión en casa puede no usarla, y una sin conexión puede usar internet en
otro lado. Aun así es la mejor medida disponible que admite el corte por
discapacidad, y para el argumento del tablero (acceso desigual) es la
pertinente.

Variables, verificadas contra el diccionario oficial y los datos:
  conex_inte  1 = el hogar tiene conexión a internet, 2 = no
  celular     1 = algún integrante tiene celular, 2 = no
  telefono    1 = el hogar tiene línea telefónica fija, 2 = no
  tv_paga     1 = el hogar tiene televisión de paga, 2 = no
  num_compu   número de computadoras en el hogar (0, 1, 2...); se usa como
              binario (>0) para que sea comparable con los otros cuatro.

Se revisó la tabla de hogares completa (140 columnas) buscando más variables
de tecnología. Lo único adicional con sentido fue `num_compu`. El resto de
columnas cercanas (er_aparato, er_celular, er_compu, er_aplicac, er_tv,
er_otro) NO son de tecnología: el diccionario las nombra MEDRADIO_1..6, es
decir "por qué medio escucha la radio" (aparato de radio, celular, compu,
app, tv, otro) — no dicen si el hogar tiene o usa esos aparatos.

Se revisó también la tabla de POBLACIÓN completa (todas las columnas) para
ver si existe una variable de uso personal de celular o internet, y no
existe: la única columna cercana es `redsoc_*` (uso de redes sociales, un
código de 1 a 5 por persona), pero el diccionario oficial de INEGI no está
disponible localmente para verificar qué significa cada código, y adivinarlo
arriesga invertir la escala igual que ya pasó con discapacidad (ver
enigh.csv.py). Se deja fuera hasta poder verificarla contra el cuestionario
real, no contra una suposición.
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

BASE_HOG = os.environ.get(
    "ENIGH_HOGARES_DIR",
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "..", "raw", "enigh_hogares"),
)

INDICADORES = [
    ("conex_inte", "Hogar con conexión a internet"),
    ("celular", "Hogar con teléfono celular"),
    ("telefono", "Hogar con línea telefónica fija"),
    ("tv_paga", "Hogar con televisión de paga"),
]

# num_compu es un conteo (0, 1, 2...), no el código binario 1/2 de los demás:
# se trata aparte y se compara como num_compu > 0.
INDICADOR_CONTEO = ("num_compu", "Hogar con computadora")


def main():
    import pandas as pd

    filas = []
    for year in _enigh.ANIOS_ENIGH:
        ruta = os.path.join(BASE_HOG, str(year), "hogares.csv")
        if not os.path.exists(ruta):
            print(f"[aviso] ENIGH {year}: falta {ruta}; se omite.",
                  file=sys.stderr)
            continue

        pob = _enigh.cargar_poblacion(year)
        pob = _enigh.explotar_tipo_discapacidad(pob)
        hog = pd.read_csv(ruta, low_memory=False, dtype=str)
        hog.columns = (hog.columns.str.replace("\ufeff", "", regex=False)
                       .str.lower().str.strip())

        cols = [c for c, _ in INDICADORES if c in hog.columns]
        col_conteo = INDICADOR_CONTEO[0] if INDICADOR_CONTEO[0] in hog.columns else None
        if not cols and not col_conteo:
            print(f"[aviso] ENIGH {year}: sin variables de tecnología.",
                  file=sys.stderr)
            continue

        for k in ("folioviv", "foliohog"):
            pob[k] = pob[k].astype(str).str.strip()
            hog[k] = hog[k].astype(str).str.strip()

        cols_union = cols + ([col_conteo] if col_conteo else [])
        antes = len(pob)
        m = pob.merge(hog[["folioviv", "foliohog"] + cols_union],
                      on=["folioviv", "foliohog"], how="left")
        sin = m[cols_union[0]].isna().sum()
        if sin:
            raise SystemExit(
                f"ENIGH {year}: {sin} de {antes} personas quedaron sin hogar "
                "al unir con la tabla de hogares."
            )

        llaves = ["anio", "sexo", "disc", "entidad", "rango_edad", "tipo_discapacidad"]
        for col, nombre in INDICADORES:
            if col not in cols:
                continue
            v = m[col].astype(str).str.strip()
            # Solo 1 y 2 son respuestas; cualquier otra cosa sale del
            # denominador en vez de contarse como "no tiene".
            base = m[v.isin(["1", "2"])].copy()
            base["_num"] = v[v.isin(["1", "2"])].eq("1")
            g = base.groupby(llaves, dropna=True, observed=True).apply(
                lambda x: pd.Series({
                    "num": float(x.loc[x["_num"], "factor"].sum()),
                    "den": float(x["factor"].sum()),
                    "casos": int(len(x)),
                }), include_groups=False).reset_index()
            g["tema"] = "tecnologia"
            g["indicador"] = nombre
            g["fuente"] = "ENIGH (INEGI)"
            g["universo"] = "Personas de 18 años o más"
            filas.append(g)

        if col_conteo:
            nombre = INDICADOR_CONTEO[1]
            conteo = pd.to_numeric(m[col_conteo], errors="coerce")
            base = m[conteo.notna()].copy()
            base["_num"] = conteo[conteo.notna()] > 0
            g = base.groupby(llaves, dropna=True, observed=True).apply(
                lambda x: pd.Series({
                    "num": float(x.loc[x["_num"], "factor"].sum()),
                    "den": float(x["factor"].sum()),
                    "casos": int(len(x)),
                }), include_groups=False).reset_index()
            g["tema"] = "tecnologia"
            g["indicador"] = nombre
            g["fuente"] = "ENIGH (INEGI)"
            g["universo"] = "Personas de 18 años o más"
            filas.append(g)

        print(f"[ok] ENIGH {year}: tecnología", file=sys.stderr)

    if not filas:
        raise SystemExit("No se generó ningún indicador de tecnología.")
    escribir(filas)


if __name__ == "__main__":
    main()

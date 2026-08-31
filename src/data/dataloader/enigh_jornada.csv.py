"""
enigh_jornada.csv.py: Jornada laboral y remuneración por hora.

Separa dos cosas que el indicador de ingreso mensual mezcla:

  - cuántas horas trabaja cada grupo, y
  - cuánto le pagan por cada una de esas horas.

Sin esta separación, una brecha de ingreso mensual es ambigua: puede venir de
que las mujeres trabajen menos horas o de que les paguen menos por hora, y son
dos problemas distintos con dos respuestas distintas. La remuneración por hora
es la medida más limpia de desigualdad salarial que permiten estos datos.

Sobre las columnas de uso del tiempo:

  La tabla de población trae cinco pares hor_N / min_N con su usotiempoN. El
  diccionario oficial documenta el formato y los códigos de no respuesta
  (8 = no recuerda, 9 = no lo hizo) pero NO nombra a qué actividad corresponde
  cada slot, y no se localizó el cuestionario que lo aclare.

  Solo se usa hor_1, cuya identidad sí se pudo confirmar contra los datos: su
  media es de 42.3 horas semanales entre quienes declararon haber trabajado y
  su cobertura en ese grupo es del 81%, contra 6% entre quienes no trabajaron.
  Ese comportamiento solo es compatible con horas de trabajo remunerado.

  Los slots 2 a 5, que probablemente incluyen quehaceres domésticos y
  cuidados, se dejan fuera a propósito: publicarlos exigiría adivinar cuál es
  cuál, y un indicador de trabajo de cuidados mal etiquetado sería peor que no
  tenerlo. Queda pendiente conseguir el cuestionario para incorporarlos.
"""

import sys
import os
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import error_muestral as _em  # noqa: E402
from utils_enadis import escribir  # noqa: E402
import deflactor  # noqa: E402

# El loader base se llama `enigh.csv.py`, que no es un nombre de módulo válido
# para un import normal (el punto se interpreta como separador de paquete), así
# que se carga por ruta. Reutilizarlo evita duplicar la lectura de microdatos y,
# sobre todo, la orientación de la escala de discapacidad por año, que es donde
# está el riesgo real de equivocarse.
import importlib.util  # noqa: E402

_ruta_base = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "enigh.csv.py")
_spec = importlib.util.spec_from_file_location("enigh_base", _ruta_base)
_enigh = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_enigh)

ANIOS_ENIGH = _enigh.ANIOS_ENIGH
cargar_poblacion = _enigh.cargar_poblacion
cargar_ingresos_laborales = _enigh.cargar_ingresos_laborales
explotar_tipo_discapacidad = _enigh.explotar_tipo_discapacidad


def indicadores(pob, ing, year):
    fuente = "ENIGH (INEGI)"
    llaves = ["anio", "sexo", "disc", "entidad", "rango_edad", "tipo_discapacidad"]
    pob = explotar_tipo_discapacidad(pob)
    filas = []

    p = pob.copy()
    p["horas"] = pd.to_numeric(p.get("hor_1"), errors="coerce")

    # --- Horas de trabajo remunerado a la semana ---------------------------
    # `num` es la masa de horas ponderada y `den` la población ocupada
    # ponderada, de modo que num/den son horas promedio. Se calcula solo entre
    # quienes reportaron horas: incluir ceros de la población no ocupada
    # volvería a mezclar participación con jornada.
    conHoras = p[p["horas"].fillna(0) > 0].copy()
    if len(conHoras):
        conHoras["_masa"] = conHoras["horas"] * conHoras["factor"]
        g = conHoras.groupby(llaves, dropna=True, observed=True).apply(
            lambda x: pd.Series({
                "num": float(x["_masa"].sum()),
                "den": float(x["factor"].sum()),
                "casos": int(len(x)),
            }), include_groups=False).reset_index()
        g = _em.agrega_error(g, conHoras, llaves, "horas")
        g["tema"] = "trabajo"
        g["indicador"] = "Horas de trabajo remunerado a la semana"
        g["fuente"] = fuente
        g["universo"] = "Personas de 18 años o más con trabajo remunerado"
        filas.append(g)

    # --- Ingreso por hora trabajada ----------------------------------------
    # El ingreso mensual se lleva a semanal (entre 4.33, el promedio de semanas
    # por mes) y se divide entre las horas semanales. Es la comparación que
    # aísla el pago del tiempo trabajado.
    if ing is not None:
        for k in ["folioviv", "foliohog", "numren"]:
            p[k] = p[k].astype(str).str.strip()
        m = p.merge(ing, on=["folioviv", "foliohog", "numren"], how="left")
        m = m[(m["ing_mensual"].fillna(0) > 0) & (m["horas"].fillna(0) > 0)].copy()
        if len(m):
            # A pesos constantes ANTES de calcular el valor por hora, para que
            # el recorte del 1% de abajo compare contra un umbral en la misma
            # unidad en todas las ediciones. Deflactar después dejaría el tope
            # calculado sobre pesos nominales de cada año.
            m["ing_mensual"] = m["ing_mensual"] * deflactor.factor(year)
            m["_pph"] = (m["ing_mensual"] / 4.33) / m["horas"]
            # Se recorta el 1% superior: unos pocos registros con muy pocas
            # horas declaradas y un ingreso alto producen valores por hora
            # imposibles que arrastrarían el promedio del grupo.
            tope = m["_pph"].quantile(0.99)
            m = m[m["_pph"] <= tope]
            m["_masa"] = m["_pph"] * m["factor"]
            g = m.groupby(llaves, dropna=True, observed=True).apply(
                lambda x: pd.Series({
                    "num": float(x["_masa"].sum()),
                    "den": float(x["factor"].sum()),
                    "casos": int(len(x)),
                }), include_groups=False).reset_index()
            g = _em.agrega_error(g, m, llaves, "_pph")
            g["tema"] = "trabajo"
            g["indicador"] = "Ingreso por hora trabajada"
            g["fuente"] = fuente
            g["universo"] = "Personas de 18 años o más con ingreso y horas declaradas"
            filas.append(g)

    return filas


def main():
    filas = []
    for year in ANIOS_ENIGH:
        pob = cargar_poblacion(year)
        if "hor_1" not in pob.columns:
            print(f"[aviso] ENIGH {year}: sin hor_1; se omite.", file=sys.stderr)
            continue
        ing = cargar_ingresos_laborales(year)
        filas.extend(indicadores(pob, ing, year))
        print(f"[ok] ENIGH {year}: jornada e ingreso por hora", file=sys.stderr)

    if not filas:
        raise SystemExit("No se generó ningún indicador de jornada.")
    escribir(filas)


if __name__ == "__main__":
    main()

"""
enigh_distribucion.csv.py: Distribución de la población por sexo y discapacidad.

Alimenta la portada del tablero. A diferencia del resto de los loaders, que
emiten TASAS (qué proporción de cada grupo está en cierta situación), este
emite CONTEOS: cuánta gente hay en cada grupo.

Es la diferencia entre "el 29.9% de las mujeres con discapacidad trabaja" y
"hay 4.70 millones de mujeres con discapacidad". La portada necesita lo
segundo para que el lector sepa de qué tamaño es la población de la que habla
el resto del sitio.

El esquema es el mismo que el de los demás loaders para no romper el formato
compartido, pero `num` y `den` se usan distinto:

  num = población del grupo, expandida
  den = población total del universo al que pertenece el grupo

Así num/den da la participación del grupo en el total, y `num` por sí solo da
el conteo absoluto. Las dos lecturas son útiles en la portada.
"""

import sys
import os
import importlib.util

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils_enadis import escribir  # noqa: E402

# Se reutiliza el cargador del loader base: ahí vive la orientación de la
# escala de discapacidad por año, que es donde está el riesgo de equivocarse.
_ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "enigh.csv.py")
_spec = importlib.util.spec_from_file_location("enigh_base", _ruta)
_enigh = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_enigh)


def main():
    import pandas as pd

    filas = []
    for year in _enigh.ANIOS_ENIGH:
        pob = _enigh.cargar_poblacion(year)
        llaves = ["anio", "sexo", "disc", "entidad", "rango_edad"]

        # --- Población de cada grupo ---------------------------------------
        # El denominador es la población adulta total del año, así que
        # num/den es el porcentaje que representa cada grupo del país.
        total = float(pob["factor"].sum())
        g = pob.groupby(llaves, dropna=True, observed=True).apply(
            lambda x: pd.Series({
                "num": float(x["factor"].sum()),
                "den": total,
                "casos": int(len(x)),
            }), include_groups=False).reset_index()
        g["tema"] = "distribucion"
        g["indicador"] = "Población"
        g["fuente"] = "ENIGH (INEGI)"
        g["universo"] = "Personas de 18 años o más"
        filas.append(g)

        # --- Prevalencia de discapacidad -----------------------------------
        # Aquí el denominador es la población del mismo sexo y rango de edad,
        # de modo que num/den es la prevalencia dentro de ese grupo. Es la
        # cifra que explica por qué el tablero insiste con el filtro de edad:
        # pasa de 2.7% en jóvenes a 25.6% en personas de 60 y más.
        base = pob.copy()
        base["_cd"] = base["disc"].eq("Con discapacidad")
        llaves_prev = ["anio", "sexo", "entidad", "rango_edad"]
        p = base.groupby(llaves_prev, dropna=True, observed=True).apply(
            lambda x: pd.Series({
                "num": float(x.loc[x["_cd"], "factor"].sum()),
                "den": float(x["factor"].sum()),
                "casos": int(len(x)),
            }), include_groups=False).reset_index()
        # La prevalencia no distingue por condición de discapacidad: la
        # columna se llena con un valor único para conservar el esquema.
        p["disc"] = "Total"
        p["tema"] = "distribucion"
        p["indicador"] = "Prevalencia de discapacidad"
        p["fuente"] = "ENIGH (INEGI)"
        p["universo"] = "Personas de 18 años o más"
        filas.append(p)

        # --- Distribución por dominio de dificultad --------------------------
        # Entre quienes tienen discapacidad, qué proporción tiene dificultad
        # en cada uno de los ocho dominios que pregunta la ENIGH (ver, oír,
        # caminar...). No son categorías diagnósticas de discapacidad, así
        # que el indicador se llama "dominio de dificultad" y no "tipo de
        # discapacidad". No suma 100%: los dominios no son excluyentes (una
        # persona puede tener dificultad para ver y para caminar a la vez),
        # así que esto es composición dentro de cada dominio, no una
        # repartición del total.
        con_disc = pob[pob["disc"] == "Con discapacidad"].copy()
        total_cd = float(con_disc["factor"].sum())
        if total_cd > 0:
            filas_tipo = []
            for etiqueta in _enigh.ETIQUETA_TIPO_DISC.values():
                marca_col = f"disc_tipo_{etiqueta}"
                if marca_col not in con_disc.columns:
                    continue
                llaves_tipo = ["anio", "sexo", "entidad", "rango_edad"]
                t = con_disc.groupby(llaves_tipo, dropna=True, observed=True).apply(
                    lambda x: pd.Series({
                        "num": float(x.loc[x[marca_col], "factor"].sum()),
                        "den": float(x["factor"].sum()),
                        "casos": int(len(x)),
                    }), include_groups=False).reset_index()
                t["disc"] = "Con discapacidad"
                t["tipo_discapacidad"] = etiqueta
                t["tema"] = "distribucion"
                t["indicador"] = "Distribución por dominio de dificultad"
                t["fuente"] = "ENIGH (INEGI)"
                t["universo"] = "Personas de 18 años o más con discapacidad"
                filas_tipo.append(t)
            if filas_tipo:
                filas.extend(filas_tipo)

        print(f"[ok] ENIGH {year}: distribución "
              f"({total / 1e6:.1f} millones de adultos)", file=sys.stderr)

    if not filas:
        raise SystemExit("No se generó la distribución.")
    escribir(filas)


if __name__ == "__main__":
    main()

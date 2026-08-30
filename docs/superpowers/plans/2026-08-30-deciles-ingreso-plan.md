# Deciles de ingreso en ENIGH — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Agregar un filtro de "Decil de ingreso" (1-10, calculado desde ingreso corriente per cápita del hogar) a las páginas Trabajo, Apoyos y Educación de ENIGH, sustituyendo el eje X cuando está activo y excluyéndose mutuamente con año/edad.

**Architecture:** El decil se calcula UNA vez en `enigh.csv.py` (`cargar_poblacion()`), uniendo con `concentradohogar` (que ya se usa parcialmente para heredar `factor` en 2020). Una función combinada `explotar_dimensiones()` reemplaza a `explotar_tipo_discapacidad()` en los 3 loaders relevantes, produciendo en una sola pasada las filas "Todos"/"Todos" (agregado real), por dominio (decil fijo en "Todos") y por decil (dominio fijo en "Todos") — sin duplicar el agregado ni cruzar ambas dimensiones. `armar_indicadores.py` gana un TERCER archivo de salida, `indicadores_decil.csv`, análogo a `indicadores_tipo_disc.csv` pero partido por `decil != "Todos"`. El front (`filtros.js`/`tablero.js`/`graficas.js`) gana un selector "Decil de ingreso" con exclusión mutua con año/edad, y el decil sustituye el eje X vía el mecanismo `dimX` que ya existe.

**Tech Stack:** Observable Framework (loaders Python/pandas, componentes JS/Plot), sin test runner — verificación por corrida directa del loader + build + revisión manual, mismo patrón que las rondas anteriores.

---

## Este plan cubre EXACTAMENTE lo aprobado en el spec

`docs/superpowers/specs/2026-08-30-deciles-ingreso-design.md`. Fuera de
alcance (confirmado, no tocar en este plan): decil en Tecnología/Jefatura,
aportación al hogar, jefatura cruzada con discapacidad propia,
hogar-vs-persona, gasto en transporte, ENDIREH quién-violenta, dominio de
dificultad en ENADIS/ENDIREH, márgenes de error.

---

## Task 1: Calcular el decil en `enigh.csv.py` — `cargar_poblacion()`

**Files:**
- Modify: `src/data/dataloader/enigh.csv.py:96-189` (`cargar_poblacion`)

- [ ] **Step 1: Verificar una vez más los datos crudos antes de tocar código**

```bash
cd src/data/dataloader
python3 -c "
import pandas as pd
df = pd.read_csv(r'Z:\SocialDataIbero\AnalisisSueltos\Obindi\enigh\Bases2022\concentradohogar2022.csv', low_memory=False)
print('filas:', len(df))
print('ing_cor nulos:', df['ing_cor'].isna().sum())
print('tot_integ==0:', (df['tot_integ']==0).sum())
print('mediana ing_cor:', df.ing_cor.median())
"
```
Esperado (ya confirmado en la fase de spec): 90,102 filas, 0 nulos, 0 con
`tot_integ==0`, mediana ~$46,074. Si estos números difieren
sustancialmente, DETENTE — indicaría que los datos crudos cambiaron desde
la verificación del spec.

- [ ] **Step 2: Reemplazar el merge condicional con `concentradohogar` por uno incondicional**

Ubicar el bloque actual (líneas 154-181 aproximadamente):

```python
    # El factor de expansión no está en la tabla de población de 2020: en esa
    # edición vive solo en `concentradohogar` y se hereda por hogar. En 2022 y
    # 2024 sí viene a nivel persona. Se toma el de persona cuando existe y se
    # recurre al del hogar cuando no; el factor es el mismo para todos los
    # integrantes del hogar, así que la herencia no distorsiona.
    if "factor" not in df.columns:
        ruta_hog = os.path.join(
            BASE_ENIGH, f"Bases{year}", f"concentradohogar{year}.csv")
        hog = pd.read_csv(ruta_hog, low_memory=False, dtype={"folioviv": str})
        hog.columns = (hog.columns.str.replace("﻿", "", regex=False)
                       .str.lower().str.strip())
        if "factor" not in hog.columns:
            raise KeyError(
                f"ENIGH {year}: no hay factor de expansión ni en población ni "
                "en concentradohogar."
            )
        for k in ("folioviv", "foliohog"):
            df[k] = df[k].astype(str).str.strip()
            hog[k] = hog[k].astype(str).str.strip()
        antes = len(df)
        df = df.merge(hog[["folioviv", "foliohog", "factor"]],
                      on=["folioviv", "foliohog"], how="left")
        sin_factor = df["factor"].isna().sum()
        if sin_factor:
            raise ValueError(
                f"ENIGH {year}: {sin_factor} de {antes} personas quedaron sin "
                "factor de expansión tras unir con concentradohogar."
            )

    df["factor"] = pd.to_numeric(df["factor"], errors="coerce").fillna(0)
```

Reemplazar por (el merge con `concentradohogar` ahora SIEMPRE ocurre,
para traer `ing_cor`/`tot_integ` además de `factor` cuando falte):

```python
    # concentradohogar aporta dos cosas: el `factor` de persona cuando falta
    # (solo 2020, que lo hereda a nivel hogar) y SIEMPRE `ing_cor`/`tot_integ`
    # para calcular el decil de ingreso (ver _agregar_decil más abajo). Antes
    # este merge era condicional a que faltara `factor`; ahora es incondicional
    # porque el decil se necesita en las 3 ediciones.
    ruta_hog = os.path.join(
        BASE_ENIGH, f"Bases{year}", f"concentradohogar{year}.csv")
    hog = pd.read_csv(ruta_hog, low_memory=False, dtype={"folioviv": str})
    hog.columns = (hog.columns.str.replace("﻿", "", regex=False)
                   .str.lower().str.strip())
    for c in ("factor", "ing_cor", "tot_integ"):
        if c not in hog.columns:
            raise KeyError(
                f"ENIGH {year}: falta la columna '{c}' en concentradohogar."
            )
    for k in ("folioviv", "foliohog"):
        df[k] = df[k].astype(str).str.strip()
        hog[k] = hog[k].astype(str).str.strip()
    antes = len(df)

    tiene_factor_persona = "factor" in df.columns
    cols_hog = ["folioviv", "foliohog", "ing_cor", "tot_integ"]
    if not tiene_factor_persona:
        cols_hog.append("factor")
    df = df.merge(hog[cols_hog], on=["folioviv", "foliohog"], how="left")

    sin_datos_hog = df["ing_cor"].isna().sum()
    if sin_datos_hog:
        raise ValueError(
            f"ENIGH {year}: {sin_datos_hog} de {antes} personas quedaron sin "
            "datos de concentradohogar (ing_cor) tras la unión."
        )

    df["factor"] = pd.to_numeric(df["factor"], errors="coerce").fillna(0)
```

Nota: cuando `tiene_factor_persona` es `True` (2022, 2024), `hog` NO
aporta una segunda columna `factor` que pudiera pisar la de persona — se
excluye explícitamente de `cols_hog` en ese caso, así que no hay riesgo de
sufijos `_x`/`_y` de pandas ni de perder el factor de persona correcto.

- [ ] **Step 3: Agregar la función de cálculo del decil, antes de `cargar_poblacion`**

Insertar justo antes de `def cargar_poblacion(year):`:

```python
def _calcular_decil(ing_cor_percapita, factor):
    """
    Decil ponderado de una serie de ingreso per cápita del hogar, usando el
    factor de expansión. Devuelve una Serie de enteros 1-10 alineada con la
    entrada (1 = 10% más pobre, 10 = 10% más rico), calculado por corte de
    percentiles ponderados de la distribución NACIONAL de ESE año — nunca se
    deflacta entre ediciones porque el decil es un ranking dentro del propio
    año, no una comparación de montos (ver docstring del módulo).

    Se ordena por ingreso, se acumula el factor, y se corta en los diez
    percentiles de masa ponderada equivalente (10%, 20%... 90%). Con
    ~90 mil hogares por edición los empates en el corte son marginales; no
    hace falta un método más sofisticado que ordenar y acumular.
    """
    orden = ing_cor_percapita.sort_values().index
    factor_ordenado = factor.loc[orden]
    acumulado = factor_ordenado.cumsum()
    total = factor_ordenado.sum()
    # corte[i] es la masa acumulada al final del decil i (i=1..10).
    cortes = [total * i / 10 for i in range(1, 11)]
    decil_ordenado = pd.Series(1, index=orden)
    for i, corte in enumerate(cortes[:-1], start=1):
        decil_ordenado[acumulado > corte] = i + 1
    return decil_ordenado.reindex(ing_cor_percapita.index)
```

- [ ] **Step 4: Llamar el cálculo dentro de `cargar_poblacion`, después del merge de la Step 2**

Insertar inmediatamente después del bloque de la Step 2 (después de
`df["factor"] = pd.to_numeric(...).fillna(0)`), antes del filtro
`df = df[df["edad"] >= 18].copy()`:

```python
    # --- Decil de ingreso ---------------------------------------------------
    # Per cápita del hogar: ing_cor (ya trimestral, ver docstring) entre
    # tot_integ. Es el criterio oficial del INEGI para deciles de ingreso —
    # ajusta por tamaño de hogar, a diferencia de usar ing_cor sin dividir.
    df["ing_cor"] = pd.to_numeric(df["ing_cor"], errors="coerce")
    df["tot_integ"] = pd.to_numeric(df["tot_integ"], errors="coerce")
    df["_ing_percapita"] = df["ing_cor"] / df["tot_integ"]
    df["decil"] = _calcular_decil(df["_ing_percapita"], df["factor"])

    # Guardia de sanidad: cada decil debe concentrar ~10% de la población
    # ponderada. Un decil muy chico o muy grande indicaría un error en el
    # cálculo (por ejemplo, ing_cor sin convertir a numérico, o un corte mal
    # indexado). Tolerancia amplia (5%-15%) porque los deciles no son
    # exactamente iguales por los empates en el corte.
    participacion = (df.groupby("decil")["factor"].sum() / df["factor"].sum() * 100)
    fuera_de_rango = participacion[(participacion < 5) | (participacion > 15)]
    if len(fuera_de_rango):
        raise ValueError(
            f"ENIGH {year}: decil(es) {fuera_de_rango.index.tolist()} concentran "
            f"{fuera_de_rango.round(1).to_dict()}% de la población, fuera del "
            "rango 5%-15% esperado. Revisa el cálculo de _calcular_decil."
        )
```

Nota: esta guardia corre ANTES del filtro `edad >= 18` (la Step 2 y este
bloque insertan sobre `df` completo, que en ese punto todavía incluye
menores) — es deliberado: el decil se calcula sobre la distribución
COMPLETA del ingreso de los hogares, no solo sobre los hogares con adultos,
para no sesgar el corte. El filtro de edad adulta sigue aplicándose
después, sin alterar el decil ya calculado por persona.

- [ ] **Step 5: Correr el loader y verificar la guardia + la distribución real**

```bash
python enigh.csv.py > /tmp/enigh_decil_check.csv 2> /tmp/enigh_decil_check.err
echo "exit:$?"
grep -v "ckanext_duckdb\|addpackage\|module_from_spec\|<frozen\|<string>\|AttributeError: 'NoneType'\|Traceback (most recent" /tmp/enigh_decil_check.err | grep -iE "error|traceback"
tail -10 /tmp/enigh_decil_check.err
```
Esperado: `exit:0`, sin errores reales, sin que la guardia del Step 4
aborte. Si la guardia aborta, revisa el cálculo antes de continuar — no
relajes el rango de tolerancia sin entender la causa.

**IMPORTANTE sobre rutas temporales**: si necesitas leer el CSV generado
con OTRO comando Python después (para inspección con pandas), NO uses
`/tmp/algo.csv` para escribir con un script y leer con otro — esa ruta no
es estable entre invocaciones de Python en Windows/Git Bash. Usa una ruta
Windows real dentro de este mismo worktree, o corre ambos pasos (generar
e inspeccionar) en el MISMO bloque de código Python.

- [ ] **Step 6: Verificar la distribución del decil con pandas, en el mismo bloque que lo genera**

```bash
python3 -c "
import subprocess
import pandas as pd
import io
r = subprocess.run(['python', 'enigh.csv.py'], capture_output=True, text=True)
df = pd.read_csv(io.StringIO(r.stdout))
print(df.columns.tolist())
"
```
Esto solo confirma que la columna `decil` NO se cuela en la salida
todavía (la Step 6 de este task NO explota por decil — eso es Task 2). El
objetivo de este Step es solo confirmar que `cargar_poblacion()` no
truena y que la guardia pasa; no hace falta inspeccionar `decil` en el
CSV de salida aquí porque `indicadores()` (línea 274) todavía no lo usa.

- [ ] **Step 7: Commit**

```bash
git add src/data/dataloader/enigh.csv.py
git commit -m "feat: calcula decil de ingreso per cápita del hogar en enigh.csv.py

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

## Task 2: `explotar_dimensiones()` — reemplaza `explotar_tipo_discapacidad()` en los 3 loaders

**Files:**
- Modify: `src/data/dataloader/enigh.csv.py` (agregar función, actualizar `indicadores()`)
- Modify: `src/data/dataloader/enigh_apoyos.csv.py:184`
- Modify: `src/data/dataloader/enigh_educacion.csv.py:72`

- [ ] **Step 1: Agregar `explotar_dimensiones()` en `enigh.csv.py`, después de `explotar_tipo_discapacidad()`**

```python
def explotar_dimensiones(df):
    """
    Combina en una sola tabla las tres vistas que el tablero necesita por
    indicador: el agregado real (tipo_discapacidad="Todos", decil="Todos",
    UNA sola vez), el desglose por dominio de dificultad (decil fijo en
    "Todos"), y el desglose por decil de ingreso (tipo_discapacidad fijo en
    "Todos"). Reemplaza a explotar_tipo_discapacidad() en los tres loaders
    que la llamaban, para que el agregado real no se duplique: si se
    llamaran las dos explosiones por separado y se concatenaran, cada una
    generaría su propia fila "Todos", inflando el agregado al doble en el
    CSV combinado.

    Las dos dimensiones NUNCA varían a la vez en la misma fila: filtrar por
    dominio Y decil simultáneamente no es un caso que el tablero ofrezca
    (confirmado en el spec), así que no hace falta la explosión cruzada
    (dominio × decil), que multiplicaría las filas ~100 veces sin necesidad.
    """
    presentes = [c for c in COLS_TIPO_DISC if c in df.columns]
    if not presentes:
        raise KeyError(
            "explotar_dimensiones: no hay columnas disc_tipo_* en el "
            "dataframe. ¿Se llamó antes de cargar_poblacion()?"
        )
    if "decil" not in df.columns:
        raise KeyError(
            "explotar_dimensiones: no hay columna 'decil' en el dataframe. "
            "¿Se llamó antes de cargar_poblacion()?"
        )

    base = df.copy()
    base["tipo_discapacidad"] = "Todos"
    base["decil"] = "Todos"

    con_disc = df[df["disc"] == "Con discapacidad"]
    partes = []
    for c in presentes:
        etiqueta = c.replace("disc_tipo_", "")
        sub = con_disc[con_disc[c]].copy()
        if sub.empty:
            continue
        sub["tipo_discapacidad"] = etiqueta
        sub["decil"] = "Todos"
        partes.append(sub)

    for d in range(1, 11):
        sub = df[df["decil"] == d].copy()
        if sub.empty:
            continue
        sub["tipo_discapacidad"] = "Todos"
        sub["decil"] = str(d)
        partes.append(sub)

    return pd.concat([base] + partes, ignore_index=True)
```

- [ ] **Step 2: Actualizar `indicadores()` en `enigh.csv.py` para usar la nueva función y agregar `decil` a `llaves`**

Ubicar (línea 274-278 aproximadamente):

```python
def indicadores(pob, ing, year):
    # Sin el año: lo aporta el filtro de edición.
    fuente = "ENIGH (INEGI)"
    llaves = ["anio", "sexo", "disc", "entidad", "rango_edad", "tipo_discapacidad"]
    pob = explotar_tipo_discapacidad(pob)
    filas = []
```

Reemplazar por:

```python
def indicadores(pob, ing, year):
    # Sin el año: lo aporta el filtro de edición.
    fuente = "ENIGH (INEGI)"
    llaves = ["anio", "sexo", "disc", "entidad", "rango_edad",
              "tipo_discapacidad", "decil"]
    pob = explotar_dimensiones(pob)
    filas = []
```

- [ ] **Step 3: Actualizar `enigh_apoyos.csv.py:181-184`**

Ubicar:

```python
def indicadores(pob, year):
    fuente = "ENIGH (INEGI)"
    llaves = ["anio", "sexo", "disc", "entidad", "rango_edad", "tipo_discapacidad"]
    pob = _enigh.explotar_tipo_discapacidad(pob)
    filas = []
```

Reemplazar por:

```python
def indicadores(pob, year):
    fuente = "ENIGH (INEGI)"
    llaves = ["anio", "sexo", "disc", "entidad", "rango_edad",
              "tipo_discapacidad", "decil"]
    pob = _enigh.explotar_dimensiones(pob)
    filas = []
```

- [ ] **Step 4: Actualizar `enigh_educacion.csv.py:53,70-72`**

Ubicar:

```python
    filas = []
    llaves = ["anio", "sexo", "disc", "entidad", "rango_edad", "tipo_discapacidad"]
```

Reemplazar por:

```python
    filas = []
    llaves = ["anio", "sexo", "disc", "entidad", "rango_edad",
              "tipo_discapacidad", "decil"]
```

Y ubicar (dentro del loop `for year in _enigh.ANIOS_ENIGH:`):

```python
    for year in _enigh.ANIOS_ENIGH:
        pob = _enigh.cargar_poblacion(year)
        pob = _enigh.explotar_tipo_discapacidad(pob)
```

Reemplazar por:

```python
    for year in _enigh.ANIOS_ENIGH:
        pob = _enigh.cargar_poblacion(year)
        pob = _enigh.explotar_dimensiones(pob)
```

- [ ] **Step 4b: Eliminar la función vieja `explotar_tipo_discapacidad()`, ya sin llamadas**

Tras los Steps 2-4, ningún loader llama ya a `explotar_tipo_discapacidad()`
(los 3 migraron a `explotar_dimensiones()`). Dejarla en el archivo sería
código muerto. Confirmar que no queda ninguna llamada:

```bash
grep -rn "explotar_tipo_discapacidad(" src/data/dataloader/*.py
```
Esperado: sin resultados (ni siquiera la definición debería aparecer si
ya se borró; si el grep encuentra la línea `def
explotar_tipo_discapacidad(df):` en `enigh.csv.py`, bórrala completa —
docstring y cuerpo, líneas 195-236 aproximadamente en el archivo
original, justo antes de `def cargar_ingresos_laborales`).

- [ ] **Step 5: Correr los 3 loaders y verificar que no hay fila "Todos" duplicada**

```bash
cd src/data/dataloader
python enigh.csv.py > out_enigh.csv 2> err_enigh.txt
python enigh_apoyos.csv.py > out_apoyos.csv 2> err_apoyos.txt
python enigh_educacion.csv.py > out_educacion.csv 2> err_educacion.txt
for f in enigh apoyos educacion; do
  echo "=== $f ==="
  grep -v "ckanext_duckdb\|addpackage\|module_from_spec\|<frozen\|<string>\|AttributeError: 'NoneType'\|Traceback (most recent" "err_$f.txt" | grep -iE "error|traceback"
  wc -l "out_$f.csv"
done
```
Esperado: los 3 corren sin error real. Si alguno lanza `KeyError` sobre
`explotar_dimensiones`/`decil`, revisa que el Task 1 se haya aplicado
correctamente antes de continuar este task.

- [ ] **Step 6: Verificar que el agregado no se duplicó, con un chequeo directo**

```bash
python3 -c "
import pandas as pd
df = pd.read_csv('out_enigh.csv')
sub = df[(df.indicador=='Participación en el trabajo remunerado') & (df.anio==2022) &
         (df.tipo_discapacidad=='Todos') & (df.decil=='Todos') &
         (df.sexo=='Mujeres') & (df.disc=='Con discapacidad')]
print('filas para esta combinación exacta (esperado: 4, una por rango_edad×entidad... revisar count real):')
print(len(sub))
print(sub[['entidad','rango_edad','num','den','casos']].head(10))
print()
print('deciles encontrados:', sorted(df.decil.unique()))
print('dominios encontrados:', sorted(df[df.tipo_discapacidad!='Todos'].tipo_discapacidad.unique()))
"
```
Esperado: el conteo de filas para esa combinación exacta corresponde a
las combinaciones reales de entidad×rango_edad (NO el doble de lo
esperado — si sale exactamente el doble de casos/num respecto a lo que
darías por corrida directa sin decil, es la señal de que el agregado se
duplicó). `deciles encontrados` debe mostrar `['1','10','2','3','4','5',
'6','7','8','9','Todos']` (11 valores). `dominios encontrados` debe
seguir mostrando los 8 dominios de siempre (Ver, Oír, Caminar, etc.), sin
"Todos" en esa lista (ya excluido por el filtro `!= 'Todos'`).

- [ ] **Step 7: Limpiar archivos temporales y commit**

```bash
rm -f out_enigh.csv out_apoyos.csv out_educacion.csv err_enigh.txt err_apoyos.txt err_educacion.txt
cd ../../..
git add src/data/dataloader/enigh.csv.py src/data/dataloader/enigh_apoyos.csv.py src/data/dataloader/enigh_educacion.csv.py
git commit -m "feat: explotar_dimensiones combina dominio de dificultad y decil sin duplicar el agregado

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

## Task 3: Tercer archivo de salida — `armar_indicadores.py` gana `indicadores_decil.csv`

**Files:**
- Modify: `scripts/armar_indicadores.py`
- Modify: `src/data/dataloader/utils_enadis.py:304-329` (`escribir()`)

- [ ] **Step 1: Actualizar `escribir()` para incluir `decil` con el mismo default que `tipo_discapacidad`**

Ubicar en `utils_enadis.py`:

```python
def escribir(dfs):
    """
    Concatena los indicadores y los imprime como CSV a stdout.

    La salida se fuerza a UTF-8: en Windows la codificación por defecto de
    stdout es cp1252 y los nombres de entidad con acento (Michoacán,
    Querétaro, México) llegan rotos al navegador.
    """
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", newline="")

    todo = pd.concat(dfs, ignore_index=True)
    # tipo_discapacidad es opcional: por ahora solo ENIGH lo produce (ver
    # enigh.csv.py, explotar_tipo_discapacidad). Los loaders que todavía no
    # lo tienen quedan en "Todos", que es exactamente su comportamiento de
    # hoy sin desagregar por dominio — así este cambio no les rompe nada.
    if "tipo_discapacidad" not in todo.columns:
        todo["tipo_discapacidad"] = "Todos"
    todo["tipo_discapacidad"] = todo["tipo_discapacidad"].fillna("Todos")
    columnas = [
        "tema", "indicador", "anio", "sexo", "disc", "entidad", "rango_edad",
        "tipo_discapacidad", "num", "den", "casos", "fuente", "universo",
    ]
    todo = todo[columnas]
    todo.to_csv(sys.stdout, index=False)
```

Reemplazar por:

```python
def escribir(dfs):
    """
    Concatena los indicadores y los imprime como CSV a stdout.

    La salida se fuerza a UTF-8: en Windows la codificación por defecto de
    stdout es cp1252 y los nombres de entidad con acento (Michoacán,
    Querétaro, México) llegan rotos al navegador.
    """
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", newline="")

    todo = pd.concat(dfs, ignore_index=True)
    # tipo_discapacidad y decil son opcionales: por ahora solo ENIGH los
    # produce (ver enigh.csv.py, explotar_dimensiones). Los loaders que no
    # los tienen quedan en "Todos" para ambas columnas, que es exactamente
    # su comportamiento de hoy sin desagregar — así este cambio no les
    # rompe nada.
    for col in ("tipo_discapacidad", "decil"):
        if col not in todo.columns:
            todo[col] = "Todos"
        todo[col] = todo[col].fillna("Todos")
    columnas = [
        "tema", "indicador", "anio", "sexo", "disc", "entidad", "rango_edad",
        "tipo_discapacidad", "decil", "num", "den", "casos", "fuente", "universo",
    ]
    todo = todo[columnas]
    todo.to_csv(sys.stdout, index=False)
```

- [ ] **Step 2: Actualizar `armar_indicadores.py` para escribir el tercer archivo**

Ubicar el archivo completo actual:

```python
# -*- coding: utf-8 -*-
"""
Concatena la salida de los data loaders en los dos CSV que consume el sitio.

    src/data/indicadores.csv           sin desglose por dominio de dificultad
    src/data/indicadores_tipo_disc.csv con el desglose

Los loaders emiten un esquema largo común; unos traen la columna
`tipo_discapacidad` y otros no (Censo y ENDIREH no la tienen). Este script:

1. Agrega la columna `encuesta`, derivada del nombre del archivo: `enigh_apoyos`
   y `enigh_jornada` son partes de la ENIGH, no encuestas distintas.
2. Parte en dos: las filas con `tipo_discapacidad == "Todos"` van al archivo
   principal (sin esa columna, que ahí no aporta), y TODAS las filas van al de
   desglose. Un loader sin la columna cuenta como "Todos".

USO
---
    python scripts/armar_indicadores.py <directorio con los .csv generados>

Los loaders se corren antes, uno por uno, redirigiendo a ese directorio:

    python src/data/dataloader/enigh.csv.py > /tmp/gen/enigh.csv
    ...
"""
import glob
import io
import os
import sys

import pandas as pd

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDA_PRINCIPAL = os.path.join(RAIZ, "src", "data", "indicadores.csv")
SALIDA_TIPO = os.path.join(RAIZ, "src", "data", "indicadores_tipo_disc.csv")

# Nombre de archivo -> encuesta. Lo que no esté aquí usa el nombre tal cual.
ENCUESTA = {
    "enigh_apoyos": "enigh",
    "enigh_jornada": "enigh",
    "enigh_educacion": "enigh",
    "enigh_tecnologia": "enigh",
    "enadis_discriminacion": "enadis",
}

COLS = ["tema", "indicador", "anio", "sexo", "disc", "entidad", "rango_edad",
        "tipo_discapacidad", "num", "den", "casos", "fuente", "universo",
        "encuesta"]


def main():
    if len(sys.argv) != 2:
        raise SystemExit(f"uso: python {sys.argv[0]} <directorio>")

    archivos = sorted(glob.glob(os.path.join(sys.argv[1], "*.csv")))
    if not archivos:
        raise SystemExit(f"No hay .csv en {sys.argv[1]}")

    partes = []
    for ruta in archivos:
        nombre = os.path.splitext(os.path.basename(ruta))[0]
        df = pd.read_csv(ruta, low_memory=False)
        if df.empty:
            print(f"  [aviso] {nombre} salió vacío, se omite")
            continue
        # Censo y ENDIREH no desagregan por dominio: cuentan como "Todos".
        if "tipo_discapacidad" not in df.columns:
            df["tipo_discapacidad"] = "Todos"
        df["encuesta"] = ENCUESTA.get(nombre, nombre)
        partes.append(df)
        print(f"  {nombre:24} {len(df):>7,} filas -> {df['encuesta'].iloc[0]}")

    todo = pd.concat(partes, ignore_index=True)
    for c in COLS:
        if c not in todo.columns:
            raise SystemExit(f"Falta la columna {c} tras concatenar")
    todo = todo[COLS]

    # Desglose completo.
    todo.to_csv(SALIDA_TIPO, index=False, encoding="utf-8")

    # Principal: solo el agregado, y sin la columna que ahí no dice nada.
    principal = todo[todo["tipo_discapacidad"] == "Todos"].drop(
        columns=["tipo_discapacidad"])
    principal.to_csv(SALIDA_PRINCIPAL, index=False, encoding="utf-8")

    print(f"\n{len(principal):>8,} filas -> {SALIDA_PRINCIPAL}")
    print(f"{len(todo):>8,} filas -> {SALIDA_TIPO}")


if __name__ == "__main__":
    main()
```

Reemplazar el archivo completo por:

```python
# -*- coding: utf-8 -*-
"""
Concatena la salida de los data loaders en los TRES CSV que consume el sitio.

    src/data/indicadores.csv           sin desglose (dominio=Todos, decil=Todos)
    src/data/indicadores_tipo_disc.csv desglose por dominio de dificultad
    src/data/indicadores_decil.csv     desglose por decil de ingreso

Los loaders emiten un esquema largo común; unos traen las columnas
`tipo_discapacidad`/`decil` y otros no (Censo y ENDIREH no las tienen; ni
siquiera los loaders de ENIGH que no calculan decil, como tecnología). Este
script:

1. Agrega la columna `encuesta`, derivada del nombre del archivo: `enigh_apoyos`
   y `enigh_jornada` son partes de la ENIGH, no encuestas distintas.
2. Parte en TRES: las filas con AMBAS columnas en "Todos" van al archivo
   principal (sin esas columnas, que ahí no aportan); las filas con
   tipo_discapacidad != "Todos" van al archivo de dominio; las filas con
   decil != "Todos" van al archivo de decil. Un loader sin alguna columna
   cuenta como "Todos" en ella — nunca aparece en el archivo de desglose
   correspondiente.

Las dos dimensiones de desglose son MUTUAMENTE EXCLUYENTES por diseño de los
loaders (ver enigh.csv.py, explotar_dimensiones): ninguna fila real tiene
ambas columnas distintas de "Todos" a la vez, así que separarlas en dos
archivos en vez de uno no pierde ninguna combinación que el tablero use.

USO
---
    python scripts/armar_indicadores.py <directorio con los .csv generados>

Los loaders se corren antes, uno por uno, redirigiendo a ese directorio:

    python src/data/dataloader/enigh.csv.py > /tmp/gen/enigh.csv
    ...
"""
import glob
import io
import os
import sys

import pandas as pd

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDA_PRINCIPAL = os.path.join(RAIZ, "src", "data", "indicadores.csv")
SALIDA_TIPO = os.path.join(RAIZ, "src", "data", "indicadores_tipo_disc.csv")
SALIDA_DECIL = os.path.join(RAIZ, "src", "data", "indicadores_decil.csv")

# Nombre de archivo -> encuesta. Lo que no esté aquí usa el nombre tal cual.
ENCUESTA = {
    "enigh_apoyos": "enigh",
    "enigh_jornada": "enigh",
    "enigh_educacion": "enigh",
    "enigh_tecnologia": "enigh",
    "enadis_discriminacion": "enadis",
}

COLS = ["tema", "indicador", "anio", "sexo", "disc", "entidad", "rango_edad",
        "tipo_discapacidad", "decil", "num", "den", "casos", "fuente",
        "universo", "encuesta"]


def main():
    if len(sys.argv) != 2:
        raise SystemExit(f"uso: python {sys.argv[0]} <directorio>")

    archivos = sorted(glob.glob(os.path.join(sys.argv[1], "*.csv")))
    if not archivos:
        raise SystemExit(f"No hay .csv en {sys.argv[1]}")

    partes = []
    for ruta in archivos:
        nombre = os.path.splitext(os.path.basename(ruta))[0]
        df = pd.read_csv(ruta, low_memory=False)
        if df.empty:
            print(f"  [aviso] {nombre} salió vacío, se omite")
            continue
        # Los loaders que no desagregan por dominio o por decil cuentan como
        # "Todos" en la columna que les falte.
        for col in ("tipo_discapacidad", "decil"):
            if col not in df.columns:
                df[col] = "Todos"
        df["encuesta"] = ENCUESTA.get(nombre, nombre)
        partes.append(df)
        print(f"  {nombre:24} {len(df):>7,} filas -> {df['encuesta'].iloc[0]}")

    todo = pd.concat(partes, ignore_index=True)
    for c in COLS:
        if c not in todo.columns:
            raise SystemExit(f"Falta la columna {c} tras concatenar")
    todo = todo[COLS]

    # Guardia: ninguna fila real debería tener AMBAS columnas distintas de
    # "Todos" a la vez (ver docstring). Si aparece una, algún loader está
    # generando la explosión cruzada que este diseño evita a propósito.
    cruzadas = todo[(todo["tipo_discapacidad"] != "Todos") &
                     (todo["decil"] != "Todos")]
    if len(cruzadas):
        raise SystemExit(
            f"{len(cruzadas)} filas tienen tipo_discapacidad Y decil "
            "distintos de 'Todos' a la vez — revisa el loader que las "
            "generó, la explosión cruzada no está soportada."
        )

    dominio = todo[todo["tipo_discapacidad"] != "Todos"].drop(columns=["decil"])
    dominio.to_csv(SALIDA_TIPO, index=False, encoding="utf-8")

    decil = todo[todo["decil"] != "Todos"].drop(columns=["tipo_discapacidad"])
    decil.to_csv(SALIDA_DECIL, index=False, encoding="utf-8")

    # Principal: solo el agregado real, sin las columnas que ahí no aportan.
    principal = todo[
        (todo["tipo_discapacidad"] == "Todos") & (todo["decil"] == "Todos")
    ].drop(columns=["tipo_discapacidad", "decil"])
    principal.to_csv(SALIDA_PRINCIPAL, index=False, encoding="utf-8")

    print(f"\n{len(principal):>8,} filas -> {SALIDA_PRINCIPAL}")
    print(f"{len(dominio):>8,} filas -> {SALIDA_TIPO}")
    print(f"{len(decil):>8,} filas -> {SALIDA_DECIL}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Actualizar `.gitignore` para versionar el nuevo CSV**

Verificar que existe la misma excepción que ya cubre a los otros dos:

```bash
grep -n "indicadores" .gitignore
```
Esperado: líneas `!src/data/indicadores.csv` y
`!src/data/indicadores_tipo_disc.csv`. Agregar una tercera línea
`!src/data/indicadores_decil.csv` justo después, en el mismo bloque.

- [ ] **Step 4: Correr TODOS los loaders y el build tool completo, regenerar los 3 CSV**

```bash
cd src/data/dataloader
mkdir -p /tmp/gen_decil
for f in enigh enigh_jornada enigh_educacion enigh_tecnologia enigh_apoyos censo enadis enadis_discriminacion endireh; do
  python "$f.csv.py" > "/tmp/gen_decil/$f.csv" 2> "/tmp/gen_decil/$f.err"
  echo "$f exit:$?"
done
```

**IMPORTANTE**: copia `/tmp/gen_decil` a una ruta Windows real antes de
correr `armar_indicadores.py` sobre ella (mismo problema de rutas ya
documentado):

```bash
SCRATCH="C:\Users\misae\AppData\Local\Temp\claude\z--SocialDataIbero-Framework-discriminacion-mujeres\a3ab7fac-b849-4e71-99e1-1f12f0f43dee\scratchpad"
mkdir -p "$SCRATCH/gen_decil"
cp /tmp/gen_decil/*.csv "$SCRATCH/gen_decil/"
cd ../../..
python scripts/armar_indicadores.py "$SCRATCH\gen_decil"
```

Esperado: sin la excepción de "filas cruzadas" del Step 2, y un resumen
final con 3 líneas de conteo. Si la ruta de scratchpad ya no existe (por
ejemplo, en una sesión nueva de Claude Code), usa cualquier directorio
Windows real accesible en su lugar — el detalle de la ruta exacta no es
lo importante, solo que sea una ruta Windows real y no `/tmp`.

- [ ] **Step 5: Verificar los 3 archivos finales con pandas**

```bash
python3 -c "
import pandas as pd
p = pd.read_csv('src/data/indicadores.csv')
t = pd.read_csv('src/data/indicadores_tipo_disc.csv')
d = pd.read_csv('src/data/indicadores_decil.csv')
print('principal:', len(p), 'columnas:', p.columns.tolist())
print('tipo_disc:', len(t), 'columnas:', t.columns.tolist())
print('decil:', len(d), 'columnas:', d.columns.tolist())
print()
print('deciles en indicadores_decil.csv:', sorted(d.decil.astype(str).unique()))
print('temas en indicadores_decil.csv:', sorted(d.tema.unique()))
"
```
Esperado: `principal` NO tiene columna `tipo_discapacidad` ni `decil`
(se dropearon). `tipo_disc` tiene `tipo_discapacidad` pero NO `decil`.
`decil` tiene `decil` pero NO `tipo_discapacidad`. Los deciles en el
tercer archivo son exactamente `['1','10','2','3','4','5','6','7','8',
'9']` (10 valores, sin "Todos" — ya filtrado). Los temas ahí deben ser
SOLO `trabajo` y `apoyos` (los loaders que ya calculan decil en este
punto del plan — `educacion-enigh` requiere el Task 4 de la página, que
llega después, pero el LOADER de educación ya lo produce desde el Task 2
de este plan, así que también debería aparecer `educacion` aquí).

- [ ] **Step 6: Commit**

```bash
git add scripts/armar_indicadores.py src/data/dataloader/utils_enadis.py .gitignore src/data/indicadores.csv src/data/indicadores_tipo_disc.csv src/data/indicadores_decil.csv
git commit -m "feat: armar_indicadores.py separa un tercer archivo indicadores_decil.csv

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

## Task 4: Selector "Decil de ingreso" en `filtros.js`, con exclusión mutua

**Files:**
- Modify: `src/components/filtros.js`

- [ ] **Step 1: Agregar el centinela y el selector en `panelFiltros()`**

Ubicar el bloque de constantes cerca del inicio del archivo (después de
`TODOS_TIPO_DISC`):

```js
export const TODOS_TIPO_DISC = "Todos";
```

Agregar justo después:

```js
// Mismo patrón que TODOS_TIPO_DISC: centinela de "todos los deciles
// juntos" (comportamiento agregado de hoy), distinto del TODAS/TODOS
// genérico de filtrar().
export const TODOS_DECIL = "Todos";
export const ETIQUETA_DECIL_TODOS = "Todos los deciles";
export const ETIQUETA_DECIL_COMPARAR = "Comparar deciles";
```

- [ ] **Step 2: Calcular los deciles disponibles, junto a `tiposDisc`**

Ubicar:

```js
  const tiposDisc = [...new Set(datos.map((d) => d.tipo_discapacidad))]
    .filter((t) => t && t !== TODOS_TIPO_DISC).sort((a, b) => a.localeCompare(b, "es"));
```

Agregar justo después:

```js
  const deciles = [...new Set(datos.map((d) => d.decil))]
    .filter((dc) => dc && dc !== TODOS_DECIL)
    .sort((a, b) => Number(a) - Number(b));
```

- [ ] **Step 3: Construir el selector de decil, con exclusión mutua con año y edad**

Ubicar el bloque completo de dominio de dificultad (después del bloque de
`edad`, antes de `const controles = ...`):

```js
  // Dominio de dificultad (NO "tipo de discapacidad": la ENIGH pregunta ocho
  // dominios de dificultad funcional — ver, oír, caminar...— que no son
  // categorías diagnósticas de discapacidad. Llamarlo "tipo" sugeriría una
  // clasificación clínica que estos datos no ofrecen). Solo tiene sentido
  // con la comparación "Mujeres vs
  // Hombres con discapacidad" (ambas series ya están filtradas a "con
  // discapacidad"; desagregar por dominio dice EN QUÉ tipo pesa más ser
  // mujer). En las otras dos comparaciones una de las series es "sin
  // discapacidad", que no tiene dominio que mostrar, así que el filtro se
  // oculta en vez de ofrecer una desagregación que no aplica a media
  // gráfica. Reacciona al valor ACTUAL de comparación, no solo al inicial:
  // ver más abajo el manejo de mostrarSelectorTipo.
  let tipoDisc = null;
  let tipoDiscWrap = null;
  function actualizarVisibilidadTipo() {
    if (!tipoDiscWrap) return;
    const mostrar = comparacion.value === "disc-sexo" && tiposDisc.length > 1;
    tipoDiscWrap.style.display = mostrar ? "" : "none";
  }
  // "Brazos o manos" o "Bañarse o vestirse" a secas leen como partes del
  // cuerpo, no como el dominio de dificultad que son. Con prefijo quedan
  // como fragmento de oración ("Dificultad para caminar"). "Mental" es la
  // excepción: no es una acción, así que no acepta el mismo prefijo.
  const ETIQUETA_DOMINIO = {
    Mental: "Dificultad mental o emocional",
  };
  if (tiposDisc.length > 1) {
    tipoDisc = Inputs.select([TODOS_TIPO_DISC, ...tiposDisc], {
      label: "Dominio de dificultad", value: TODOS_TIPO_DISC,
      format: (k) => k === TODOS_TIPO_DISC ? "Todos los dominios"
        : ETIQUETA_DOMINIO[k] ?? `Dificultad para ${k.toLowerCase()}`,
    });
    tipoDiscWrap = html`<div class="filtro-tipo-disc">${tipoDisc}</div>`;
  }

  const controles = [comparacion, anio, entidad, edad].filter(Boolean);
  const cont = html`<div class="panel-filtros">
    ${controles}
    ${tipoDiscWrap ?? ""}
    ${meta.nota ? html`<p class="panel-nota">${meta.nota}</p>` : ""}
  </div>`;
```

Reemplazar por (agrega el bloque de decil justo antes de `controles`, y
mete `decil` en el array de controles principal porque, a diferencia de
dominio de dificultad, decil NO tiene un gatillo de comparación — siempre
se ofrece si hay más de un decil real):

```js
  // Dominio de dificultad (NO "tipo de discapacidad": la ENIGH pregunta ocho
  // dominios de dificultad funcional — ver, oír, caminar...— que no son
  // categorías diagnósticas de discapacidad. Llamarlo "tipo" sugeriría una
  // clasificación clínica que estos datos no ofrecen). Solo tiene sentido
  // con la comparación "Mujeres vs
  // Hombres con discapacidad" (ambas series ya están filtradas a "con
  // discapacidad"; desagregar por dominio dice EN QUÉ tipo pesa más ser
  // mujer). En las otras dos comparaciones una de las series es "sin
  // discapacidad", que no tiene dominio que mostrar, así que el filtro se
  // oculta en vez de ofrecer una desagregación que no aplica a media
  // gráfica. Reacciona al valor ACTUAL de comparación, no solo al inicial:
  // ver más abajo el manejo de mostrarSelectorTipo.
  let tipoDisc = null;
  let tipoDiscWrap = null;
  function actualizarVisibilidadTipo() {
    if (!tipoDiscWrap) return;
    const mostrar = comparacion.value === "disc-sexo" && tiposDisc.length > 1;
    tipoDiscWrap.style.display = mostrar ? "" : "none";
  }
  // "Brazos o manos" o "Bañarse o vestirse" a secas leen como partes del
  // cuerpo, no como el dominio de dificultad que son. Con prefijo quedan
  // como fragmento de oración ("Dificultad para caminar"). "Mental" es la
  // excepción: no es una acción, así que no acepta el mismo prefijo.
  const ETIQUETA_DOMINIO = {
    Mental: "Dificultad mental o emocional",
  };
  if (tiposDisc.length > 1) {
    tipoDisc = Inputs.select([TODOS_TIPO_DISC, ...tiposDisc], {
      label: "Dominio de dificultad", value: TODOS_TIPO_DISC,
      format: (k) => k === TODOS_TIPO_DISC ? "Todos los dominios"
        : ETIQUETA_DOMINIO[k] ?? `Dificultad para ${k.toLowerCase()}`,
    });
    tipoDiscWrap = html`<div class="filtro-tipo-disc">${tipoDisc}</div>`;
  }

  // Decil de ingreso: a diferencia de dominio de dificultad, aplica a las
  // 4 comparaciones por igual (no solo a "disc-sexo"), así que siempre se
  // muestra si hay más de un decil real en los datos filtrados — sin
  // gatillo de comparación. Activarlo excluye año-por-facetas y
  // edad-por-facetas: el decil sustituye el eje X (ver geometria() en
  // este mismo archivo), y desplegar además año o edad como facetas
  // produciría 30-40 grupos de barras en un solo panel, ilegible. Si el
  // usuario reactiva "comparar años" o "por rango de edad" mientras decil
  // está activo, decil vuelve a "Todos" — mismo patrón defensivo que ya
  // usa tipoDiscapacidad para no dejar un filtro fantasma detrás de una
  // gráfica que ya no lo muestra.
  let decilInput = null;
  if (deciles.length > 1) {
    decilInput = Inputs.select([TODOS_DECIL, ETIQUETA_DECIL_COMPARAR], {
      label: "Decil de ingreso", value: TODOS_DECIL,
      format: (k) => k === TODOS_DECIL ? ETIQUETA_DECIL_TODOS : k,
    });
  }

  const controles = [comparacion, anio, entidad, edad, decilInput].filter(Boolean);
  const cont = html`<div class="panel-filtros">
    ${controles}
    ${tipoDiscWrap ?? ""}
    ${meta.nota ? html`<p class="panel-nota">${meta.nota}</p>` : ""}
  </div>`;
```

- [ ] **Step 4: Cablear la exclusión mutua y el valor final en `valor()`**

Ubicar el objeto `valor` y el bloque de listeners al final de la función:

```js
  const valor = () => ({
    comparacion: comparacion.value,
    // Si solo hay un año, ese es el año; no hay nada que comparar.
    anio: anio ? anio.value : (anios[0] ?? POR_SEPARADO),
    entidad: entidad ? entidad.value : TODAS,
    rangoEdad: edad ? edad.value : AGREGADO,
    // Fuera de "disc-sexo" el filtro está oculto: se fuerza a "Todos" para
    // que cambiar de comparación y volver no deje un dominio pegado detrás
    // de una gráfica que ya no lo muestra.
    tipoDiscapacidad: (tipoDisc && comparacion.value === "disc-sexo")
      ? tipoDisc.value : TODOS_TIPO_DISC,
  });

  cont.value = valor();
  actualizarVisibilidadTipo();
  for (const c of controles) {
    c.addEventListener("input", () => {
      actualizarVisibilidadTipo();
      cont.value = valor();
      cont.dispatchEvent(new Event("input", {bubbles: true}));
    });
  }
  if (tipoDisc) {
    tipoDisc.addEventListener("input", () => {
      cont.value = valor();
      cont.dispatchEvent(new Event("input", {bubbles: true}));
    });
  }
  return cont;
}
```

Reemplazar por:

```js
  const valor = () => ({
    comparacion: comparacion.value,
    // Si solo hay un año, ese es el año; no hay nada que comparar.
    anio: anio ? anio.value : (anios[0] ?? POR_SEPARADO),
    entidad: entidad ? entidad.value : TODAS,
    rangoEdad: edad ? edad.value : AGREGADO,
    // Fuera de "disc-sexo" el filtro está oculto: se fuerza a "Todos" para
    // que cambiar de comparación y volver no deje un dominio pegado detrás
    // de una gráfica que ya no lo muestra.
    tipoDiscapacidad: (tipoDisc && comparacion.value === "disc-sexo")
      ? tipoDisc.value : TODOS_TIPO_DISC,
    decil: decilInput ? decilInput.value : TODOS_DECIL,
  });

  // Exclusión mutua: activar decil fuerza año a un valor concreto y edad a
  // agregado; reactivar año-por-facetas o edad-por-facetas fuerza decil a
  // "Todos". Se resuelve en los propios listeners de cada control, no en
  // valor(), para que el estado interno de los Inputs (lo que se ve en
  // pantalla) quede sincronizado con lo que valor() reporta — si solo se
  // pisara el valor reportado sin tocar el control, el selector seguiría
  // mostrando la opción vieja aunque el filtro real ya hubiera cambiado.
  function comparandoDeciles() {
    return decilInput && decilInput.value === ETIQUETA_DECIL_COMPARAR;
  }

  cont.value = valor();
  actualizarVisibilidadTipo();
  for (const c of controles) {
    c.addEventListener("input", () => {
      actualizarVisibilidadTipo();
      if (c === decilInput && comparandoDeciles()) {
        if (anio) anio.value = anios.at(-1);
        if (edad) edad.value = AGREGADO;
      } else if ((c === anio || c === edad) && comparandoDeciles()) {
        decilInput.value = TODOS_DECIL;
      }
      cont.value = valor();
      cont.dispatchEvent(new Event("input", {bubbles: true}));
    });
  }
  if (tipoDisc) {
    tipoDisc.addEventListener("input", () => {
      cont.value = valor();
      cont.dispatchEvent(new Event("input", {bubbles: true}));
    });
  }
  return cont;
}
```

- [ ] **Step 5: Actualizar `filtrar()` para aceptar y aplicar el filtro de decil**

Ubicar:

```js
export function filtrar(datos, {indicador = null, anio = POR_SEPARADO,
    entidad = TODAS, rangoEdad = AGREGADO, tipoDiscapacidad = TODOS_TIPO_DISC} = {}) {
  const abierto = (v) => v === TODOS || v === TODAS ||
                         v === POR_SEPARADO || v === AGREGADO;
  return datos.filter((d) =>
    (indicador == null || d.indicador === indicador) &&
    (abierto(anio) || String(d.anio) === String(anio)) &&
    (abierto(entidad) || d.entidad === entidad) &&
    (abierto(rangoEdad) || d.rango_edad === rangoEdad) &&
    (d.tipo_discapacidad == null || d.tipo_discapacidad === (tipoDiscapacidad ?? TODOS_TIPO_DISC))
  );
}
```

Reemplazar por:

```js
export function filtrar(datos, {indicador = null, anio = POR_SEPARADO,
    entidad = TODAS, rangoEdad = AGREGADO, tipoDiscapacidad = TODOS_TIPO_DISC,
    decil = TODOS_DECIL} = {}) {
  const abierto = (v) => v === TODOS || v === TODAS ||
                         v === POR_SEPARADO || v === AGREGADO;
  // `decil` en `filtrar()` es "Todos" (sin recortar) o "Comparar deciles"
  // (tampoco recorta: entran todas las filas reales, el desglose lo hace
  // geometria()/dimX, no este filtro) — nunca un decil concreto, porque el
  // panel no ofrece elegir un solo decil, solo agregado o comparar todos.
  return datos.filter((d) =>
    (indicador == null || d.indicador === indicador) &&
    (abierto(anio) || String(d.anio) === String(anio)) &&
    (abierto(entidad) || d.entidad === entidad) &&
    (abierto(rangoEdad) || d.rango_edad === rangoEdad) &&
    (d.tipo_discapacidad == null || d.tipo_discapacidad === (tipoDiscapacidad ?? TODOS_TIPO_DISC)) &&
    (d.decil == null ||
      (decil === TODOS_DECIL ? d.decil === TODOS_DECIL : true))
  );
}
```

Nota sobre la última condición: cuando `decil === TODOS_DECIL` (default),
solo entran filas con `d.decil === "Todos"` (el agregado real, mismo
comportamiento de hoy). Cuando `decil === ETIQUETA_DECIL_COMPARAR`, entran
TODAS las filas (agregado Y por-decil-real) porque en ese modo
`geometria()` va a separar por `dimX: "decil"` y necesita las filas reales
de cada decil, no el agregado — el agregado sencillamente no participa en
`prepararSeries()` porque no coincide con ningún decil real 1-10 al
agrupar por `dim: "decil"` (queda como una fila aparte que Plot no
grafica al no tener valor numérico de decil, o se filtra explícitamente
en el Task 5 de `geometria()`/`prepararSeries()` si hiciera falta — se
revisa en el siguiente task).

- [ ] **Step 6: Actualizar `geometria()` para producir `dimX: "decil"` y forzar facetas a null**

Ubicar:

```js
export function geometria(v, {aniosDisponibles = []} = {}) {
  const comparaAnios = v.anio === POR_SEPARADO && aniosDisponibles.length > 1;
  const separaEdad = v.rangoEdad === POR_SEPARADO;

  // Los años van como columnas (se leen de izquierda a derecha, como el
  // tiempo) y las edades como filas.
  //
  // Dentro de cada panel el eje x son siempre las series de la comparación.
  // "Todas las edades (juntas)" significa exactamente eso: una barra por
  // serie con la población agregada, no las edades desplegadas en el eje.
  // Poner ahí la edad sería devolver un desglose que el usuario no pidió.
  return {
    facetaCol: comparaAnios ? "anio" : null,
    facetaFila: separaEdad ? "rango_edad" : null,
    dimX: null,
  };
}
```

Reemplazar por:

```js
export function geometria(v, {aniosDisponibles = []} = {}) {
  const comparaDeciles = v.decil === ETIQUETA_DECIL_COMPARAR;

  // Comparar deciles sustituye el eje X y excluye año/edad como facetas —
  // la exclusión mutua ya se resuelve en panelFiltros() forzando los
  // controles, pero geometria() la respeta aquí también por si acaso llega
  // un estado inconsistente (por ejemplo, un valor de panel guardado de
  // antes de este cambio): comparar deciles SIEMPRE gana sobre año/edad.
  if (comparaDeciles) {
    return {facetaCol: null, facetaFila: null, dimX: "decil"};
  }

  const comparaAnios = v.anio === POR_SEPARADO && aniosDisponibles.length > 1;
  const separaEdad = v.rangoEdad === POR_SEPARADO;

  // Los años van como columnas (se leen de izquierda a derecha, como el
  // tiempo) y las edades como filas.
  //
  // Dentro de cada panel el eje x son siempre las series de la comparación.
  // "Todas las edades (juntas)" significa exactamente eso: una barra por
  // serie con la población agregada, no las edades desplegadas en el eje.
  // Poner ahí la edad sería devolver un desglose que el usuario no pidió.
  return {
    facetaCol: comparaAnios ? "anio" : null,
    facetaFila: separaEdad ? "rango_edad" : null,
    dimX: null,
  };
}
```

- [ ] **Step 7: Agregar el caso "decil" al ordenamiento de `prepararSeries()`**

Ubicar:

```js
  // Orden estable: primero por las dimensiones (edad en su orden ordinal, no
  // alfabético), luego por el orden de las series declaradas en la
  // comparación, para que la leyenda y las barras coincidan siempre.
  const posSerie = new Map(comp.series.map((s, i) => [s, i]));
  return agregadas.sort((a, b) => {
    for (const k of dims) {
      if (k === "rango_edad") {
        const d = ORDEN_EDAD.indexOf(a.rango_edad) - ORDEN_EDAD.indexOf(b.rango_edad);
        if (d !== 0) return d;
      } else {
        const d = String(a[k] ?? "").localeCompare(String(b[k] ?? ""), "es");
        if (d !== 0) return d;
      }
    }
    return (posSerie.get(a.serie) ?? 99) - (posSerie.get(b.serie) ?? 99);
  });
}
```

Reemplazar por:

```js
  // Orden estable: primero por las dimensiones (edad y decil en su orden
  // ordinal/numérico, no alfabético — "10" antes que "2" alfabéticamente
  // sería un orden sin sentido para una escala de pobre a rico), luego por
  // el orden de las series declaradas en la comparación, para que la
  // leyenda y las barras coincidan siempre.
  const posSerie = new Map(comp.series.map((s, i) => [s, i]));
  return agregadas.sort((a, b) => {
    for (const k of dims) {
      if (k === "rango_edad") {
        const d = ORDEN_EDAD.indexOf(a.rango_edad) - ORDEN_EDAD.indexOf(b.rango_edad);
        if (d !== 0) return d;
      } else if (k === "decil") {
        const d = Number(a.decil) - Number(b.decil);
        if (d !== 0) return d;
      } else {
        const d = String(a[k] ?? "").localeCompare(String(b[k] ?? ""), "es");
        if (d !== 0) return d;
      }
    }
    return (posSerie.get(a.serie) ?? 99) - (posSerie.get(b.serie) ?? 99);
  });
}
```

Nota: cuando `dim` incluye `"decil"` y las filas también incluyen la fila
agregada `decil="Todos"` (`Number("Todos")` es `NaN`), esa fila quedaría
mezclada de forma impredecible en el sort — pero por diseño (Step 5), en
modo "Comparar deciles" el `filtrar()` deja pasar TODAS las filas
(agregado incluido). Esto SÍ es un problema real a resolver: la fila
`decil="Todos"` no debe llegar a `prepararSeries()` cuando `dimX ===
"decil"`, porque Plot la graficaría como una undécima barra sin sentido
numérico. Se resuelve en el Step 8 siguiente, filtrando esa fila
específicamente antes de agregar.

- [ ] **Step 8: Excluir la fila "Todos" del decil cuando se está comparando deciles, en `prepararSeries()`**

Ubicar el inicio de `prepararSeries()`:

```js
export function prepararSeries(datos, {comparacion, dim = null, formato = "pct"}) {
  const comp = COMPARACIONES.find((c) => c.clave === comparacion);
  if (!comp) return [];
  const dims = (Array.isArray(dim) ? dim : [dim]).filter(Boolean);

  // Solo los grupos que participan en la comparación, decidido por
  // pertenencia real a `comp.grupos` (no por un `if` a mano por cada
  // clave): "sexo" colapsa discapacidad y usa los 4 grupos, las demás
  // comparaciones son subconjuntos de 2. Antes esto era un `if` explícito
  // por clave (sexo / disc-mujeres / disc-sexo); con una 4ª comparación
  // (disc-extremo) y la posibilidad de más en el futuro, filtrar por la
  // lista ya declarada en COMPARACIONES evita mantener dos fuentes de
  // verdad sincronizadas a mano.
  const filas = datos
    .filter((d) => {
      if (comp.clave === "sexo") return true;
      const sx = d.sexo === "Mujeres" ? "M" : "H";
      const cd = d.disc === "Con discapacidad" ? "CD" : "SD";
      return comp.grupos.includes(`${sx}-${cd}`);
    })
    .map((d) => ({...d, serie: serieDe(d, comparacion)}));
```

Reemplazar por:

```js
export function prepararSeries(datos, {comparacion, dim = null, formato = "pct"}) {
  const comp = COMPARACIONES.find((c) => c.clave === comparacion);
  if (!comp) return [];
  const dims = (Array.isArray(dim) ? dim : [dim]).filter(Boolean);
  const separaDecil = dims.includes("decil");

  // Solo los grupos que participan en la comparación, decidido por
  // pertenencia real a `comp.grupos` (no por un `if` a mano por cada
  // clave): "sexo" colapsa discapacidad y usa los 4 grupos, las demás
  // comparaciones son subconjuntos de 2. Antes esto era un `if` explícito
  // por clave (sexo / disc-mujeres / disc-sexo); con una 4ª comparación
  // (disc-extremo) y la posibilidad de más en el futuro, filtrar por la
  // lista ya declarada en COMPARACIONES evita mantener dos fuentes de
  // verdad sincronizadas a mano.
  const filas = datos
    .filter((d) => {
      if (comp.clave === "sexo") return true;
      const sx = d.sexo === "Mujeres" ? "M" : "H";
      const cd = d.disc === "Con discapacidad" ? "CD" : "SD";
      return comp.grupos.includes(`${sx}-${cd}`);
    })
    // Cuando se está separando por decil (dim incluye "decil"), la fila
    // agregada decil="Todos" no tiene un valor numérico que graficar en
    // el eje X — se excluye aquí, antes de agregar, para que no aparezca
    // como una undécima barra sin sentido junto a los deciles 1-10.
    .filter((d) => !separaDecil || d.decil !== TODOS_DECIL)
    .map((d) => ({...d, serie: serieDe(d, comparacion)}));
```

- [ ] **Step 9: Build y revisión manual (sin dev server todavía — falta el cableado en `tablero.js`, Task 5)**

```bash
cd ../../..
npm run build 2>&1 | tail -20
```
Esperado: el build sigue pasando para las 15 páginas — este task NO
cambia ninguna página `.md` todavía (eso es Task 5/6/7). Si el build
falla con un error de sintaxis JS, revisa los reemplazos de este task
antes de continuar.

- [ ] **Step 10: Commit**

```bash
git add src/components/filtros.js
git commit -m "feat: selector de decil de ingreso con exclusión mutua año/edad

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

## Task 5: Cablear `decil` en `tablero.js` (dashboardTema + bloqueGrafica)

**Files:**
- Modify: `src/components/tablero.js`

- [ ] **Step 1: `dashboardTema()` gana el parámetro `datosDecil` y lo concatena**

Ubicar:

```js
// `datosTipoDisc` es opcional y viene de un archivo APARTE
// (indicadores_tipo_disc.csv): las filas por dominio de discapacidad
// multiplican el tamaño de los datos casi por 3, y la mayoría de las páginas
// nunca activan ese filtro. Separarlo evita que las 9 páginas que no lo usan
// paguen su peso de descarga. Solo lo pasan las páginas de ENIGH (ver
// filtros.js: el selector de tipo de discapacidad solo aparece si hay más de
// un valor real en los datos, así que si esto no se pasa el filtro
// simplemente no se ofrece).
export function dashboardTema(clave, datos, {geoEntidades = null, datosTipoDisc = null} = {}) {
  const tema = CATALOGO[clave];
  if (!tema) return html`<p>Tema desconocido: ${clave}</p>`;

  const fuente = tema.fuentePrincipal;
  const base = datos.filter((d) => d.encuesta === fuente);
  const extra = (datosTipoDisc ?? []).filter((d) => d.encuesta === fuente);
  const datosFuente = extra.length ? base.concat(extra) : base;
  const principales = datosFuente.filter((d) => d.indicador === tema.indicadorPrincipal);
```

Reemplazar por:

```js
// `datosTipoDisc`/`datosDecil` son opcionales y vienen de archivos APARTE
// (indicadores_tipo_disc.csv, indicadores_decil.csv): ambos multiplican el
// tamaño de los datos, y la mayoría de las páginas no activan ninguno de
// los dos filtros. Separarlos evita que las páginas que no los usan paguen
// su peso de descarga. Solo Trabajo/Apoyos/Educación (ENIGH) pasan
// `datosDecil` por ahora; el selector de decil solo aparece si hay más de
// un valor real en los datos, así que si esto no se pasa el filtro
// simplemente no se ofrece (mismo criterio que ya usa datosTipoDisc).
export function dashboardTema(clave, datos, {geoEntidades = null,
    datosTipoDisc = null, datosDecil = null} = {}) {
  const tema = CATALOGO[clave];
  if (!tema) return html`<p>Tema desconocido: ${clave}</p>`;

  const fuente = tema.fuentePrincipal;
  const base = datos.filter((d) => d.encuesta === fuente);
  const extraTipo = (datosTipoDisc ?? []).filter((d) => d.encuesta === fuente);
  const extraDecil = (datosDecil ?? []).filter((d) => d.encuesta === fuente);
  const datosFuente = base.concat(extraTipo, extraDecil);
  const principales = datosFuente.filter((d) => d.indicador === tema.indicadorPrincipal);
```

Nota: el `concat` cambia de condicional (`extra.length ? ... : base`) a
incondicional (`base.concat(extraTipo, extraDecil)`) — concatenar con un
arreglo vacío no cambia el resultado (`[].concat([])` es un no-op), así
que simplificar a incondicional es seguro y evita repetir la misma
condición dos veces para dos parámetros.

- [ ] **Step 2: Pasar `v.decil` en las 3 llamadas a `filtrar()` dentro de `tablero.js`**

Ubicar las 3 ocurrencias de `filtrar(` en el archivo:

```bash
grep -n "filtrar(" src/components/tablero.js
```

Para cada una, el patrón actual es:

```js
      const filas = filtrar(datosFuente, {
        indicador: tema.indicadorPrincipal,
        anio: v.anio, entidad: v.entidad, rangoEdad: v.rangoEdad,
        tipoDiscapacidad: v.tipoDiscapacidad,
      });
```

(o la variante sin `indicador:` en la sección de secundarios, o con
`anio: c.anio, rangoEdad: c.edad` en la sección de territorio). En las
TRES, agregar `decil: v.decil,` justo después de `tipoDiscapacidad:
v.tipoDiscapacidad,`. Por ejemplo, la primera ocurrencia (sección
principal) queda:

```js
      const filas = filtrar(datosFuente, {
        indicador: tema.indicadorPrincipal,
        anio: v.anio, entidad: v.entidad, rangoEdad: v.rangoEdad,
        tipoDiscapacidad: v.tipoDiscapacidad,
        decil: v.decil,
      });
```

Aplica el mismo agregado literal (`decil: v.decil,`) a las otras 2
ocurrencias de `filtrar(datosFuente, {...})`/`filtrar(fsec, {...})` en el
archivo.

- [ ] **Step 3: Agregar "decil" a `ETIQUETA_DIM` para la etiqueta del eje/tabla**

Ubicar:

```js
// Etiqueta legible de la dimensión del eje.
const ETIQUETA_DIM = {
  rango_edad: "Rango de edad",
  anio: "Edición",
  entidad: "Entidad",
};
```

Reemplazar por:

```js
// Etiqueta legible de la dimensión del eje.
const ETIQUETA_DIM = {
  rango_edad: "Rango de edad",
  anio: "Edición",
  entidad: "Entidad",
  decil: "Decil de ingreso",
};
```

- [ ] **Step 4: Confirmar que `bloqueGrafica()` no necesita cambios adicionales**

`bloqueGrafica()` ya lee `geo.dimX` genéricamente (línea ~64-74, sin
cambios de este plan) y lo pasa a `barrasComparadas({dim: dimX, dimLabel:
ETIQUETA_DIM[dimX] ?? "", ...})` — con `dimX === "decil"` y el paso 3 de
este task, `dimLabel` resuelve a "Decil de ingreso" automáticamente. NO
se requiere ningún cambio en `bloqueGrafica()` ni en `barrasComparadas()`
(`graficas.js`) para este plan — el orden del eje X ya lo resuelve el
Task 4/Step 7 (`prepararSeries()`), y `barrasComparadas()` respeta el
orden de los datos de entrada cuando no se le pasa `dominioDim` explícito
(confirmado leyendo `graficas.js` en la fase de diseño de este plan).

Verificación de esta afirmación, no una acción a ejecutar:

```bash
grep -n "dominioDim" src/components/graficas.js
```
Confirma que `dominioDim` solo se usa si se pasa explícitamente (default
`null`), y que `bloqueGrafica()` en `tablero.js` no lo pasa — así que el
orden natural de `prepararSeries()` (ya arreglado en Task 4) es
suficiente.

- [ ] **Step 5: Build**

```bash
npm run build 2>&1 | tail -20
```
Esperado: sigue pasando, 15 páginas, sin error (todavía ninguna página
`.md` pasa `datosDecil`, así que el comportamiento visible no cambia
todavía — este task solo prepara el cableado).

- [ ] **Step 6: Commit**

```bash
git add src/components/tablero.js
git commit -m "feat: dashboardTema acepta datosDecil y lo cablea a filtrar/geometria

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

## Task 6: Activar el filtro en las páginas Trabajo, Apoyos, Educación

**Files:**
- Modify: `src/encuestas/enigh/trabajo.md`
- Modify: `src/encuestas/enigh/apoyos.md`
- Modify: `src/encuestas/enigh/educacion-enigh.md`

- [ ] **Step 1: Leer las 3 páginas completas antes de editar**

```bash
cat src/encuestas/enigh/trabajo.md
cat src/encuestas/enigh/apoyos.md
cat src/encuestas/enigh/educacion-enigh.md
```

Confirma el patrón exacto de cada una (probablemente ya cargan
`indicadoresTipoDisc` desde `indicadores_tipo_disc.csv` y lo pasan como
`datosTipoDisc` a `dashboardTema(...)`, siguiendo el mismo patrón de la
ronda de Censo).

- [ ] **Step 2: `trabajo.md` — agregar la carga y el paso de `datosDecil`**

El patrón esperado (ajustar a lo que el Step 1 reveló si difiere) es
agregar, junto al `FileAttachment` de `indicadores_tipo_disc.csv` ya
existente:

```js
const indicadoresDecil = await FileAttachment("../../data/indicadores_decil.csv").csv({typed: true});
```

Y en la llamada a `dashboardTema`, agregar `datosDecil: indicadoresDecil`
al objeto de opciones, junto a `datosTipoDisc`:

```js
display(dashboardTema("trabajo", indicadores, {geoEntidades, datosTipoDisc: indicadoresTipoDisc, datosDecil: indicadoresDecil}));
```

- [ ] **Step 3: `apoyos.md` — mismo cambio, clave `"apoyos"`**

```js
const indicadoresDecil = await FileAttachment("../../data/indicadores_decil.csv").csv({typed: true});
```

```js
display(dashboardTema("apoyos", indicadores, {geoEntidades, datosTipoDisc: indicadoresTipoDisc, datosDecil: indicadoresDecil}));
```

- [ ] **Step 4: `educacion-enigh.md` — mismo cambio, clave `"educacion-enigh"`**

```js
const indicadoresDecil = await FileAttachment("../../data/indicadores_decil.csv").csv({typed: true});
```

```js
display(dashboardTema("educacion-enigh", indicadores, {geoEntidades, datosTipoDisc: indicadoresTipoDisc, datosDecil: indicadoresDecil}));
```

- [ ] **Step 5: Build completo**

```bash
npm run build 2>&1 | tail -30
```
Esperado: las 15 páginas renderizan sin error, incluidas las 3 tocadas
en este task.

- [ ] **Step 6: Revisión visual — confirmar el selector aparece y la exclusión mutua funciona**

```bash
npm run dev
```
Espera a que arranque (revisa el puerto en el log). Confirma con curl:
```bash
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:PUERTO/encuestas/enigh/trabajo
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:PUERTO/encuestas/enigh/apoyos
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:PUERTO/encuestas/enigh/educacion-enigh
```
Esperado: 200 en las 3.

Adicional: confirma que el módulo `filtros.js` servido trae el selector
nuevo:
```bash
curl -s http://127.0.0.1:PUERTO/_import/components/filtros.js | grep -o "Decil de ingreso\|Comparar deciles" | sort -u
```
Esperado: ambas cadenas presentes.

Detén el dev server al terminar:
```bash
netstat -ano | grep ":3000\|:3001\|:3002\|:3003" | grep LISTENING
taskkill //F //PID <PID>
```

- [ ] **Step 7: Verificación de datos — simular el filtro contra el CSV real**

```bash
python3 -c "
import pandas as pd
d = pd.read_csv('src/data/indicadores_decil.csv')
sub = d[(d.tema=='trabajo') & (d.indicador=='Ingreso laboral mensual promedio') &
        (d.anio==d.anio.max()) & (d.sexo=='Mujeres') & (d.disc=='Con discapacidad')]
sub = sub.groupby('decil').apply(lambda x: x['num'].sum()/x['den'].sum())
print('Ingreso mensual promedio, mujeres con discapacidad, por decil:')
print(sub.sort_index())
"
```
Esperado: una serie de 10 valores (decil 1 a 10, como strings numéricos),
CRECIENTE en general de decil 1 a decil 10 (el ingreso laboral debería
ser mayor en los deciles más ricos — es una verificación de sentido común
sobre el cálculo del decil en sí, no solo de que el código corre sin
error). Si la serie sale plana o invertida, DETENTE y revisa el cálculo
del decil en el Task 1 antes de continuar — sería indicio de que el
decil está mal calculado o mal ordenado.

- [ ] **Step 8: Commit**

```bash
git add src/encuestas/enigh/trabajo.md src/encuestas/enigh/apoyos.md src/encuestas/enigh/educacion-enigh.md
git commit -m "feat: activa el filtro de decil de ingreso en Trabajo, Apoyos y Educación

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

## Task 7: Verificación final de la ronda completa

**Files:** ninguno nuevo — solo verificación.

- [ ] **Step 1: Build limpio desde cero**

```bash
rm -rf dist .observablehq/cache
npm run build 2>&1 | tail -50
```
Esperado: 0 errores, 15 páginas (esta ronda no agrega páginas nuevas,
solo un filtro a 3 existentes).

- [ ] **Step 2: Recorrido manual de las 15 páginas**

```bash
npm run dev
```
Visitar cada ruta del nav y confirmar: (a) sin error de consola visible,
(b) las 12 páginas que NO son Trabajo/Apoyos/Educación siguen sin mostrar
ningún selector de decil (confirma que el filtro no se coló donde no
debía), (c) las 3 páginas SÍ muestran "Decil de ingreso" con las
opciones "Todos los deciles"/"Comparar deciles", (d) activar "Comparar
deciles" en cualquiera de las 3 muestra una gráfica de 10 grupos de
barras en orden 1→10, y el selector de Año/Edad se colapsa a un valor
fijo/agregado automáticamente.

- [ ] **Step 3: Detener dev server**

```bash
netstat -ano | grep ":3000\|:3001\|:3002\|:3003" | grep LISTENING
taskkill //F //PID <PID>
```

- [ ] **Step 4: Confirmar tamaño del nuevo archivo de datos**

```bash
ls -la src/data/indicadores_decil.csv
```
Reportar el tamaño — es informativo para decidir si vale la pena en el
futuro optimizar más (por ejemplo, si resulta mucho más pesado de lo
esperado dado que solo 3 de 5 loaders ENIGH lo producen).

- [ ] **Step 5: Push (si el usuario lo pide explícitamente — no antes)**

Esta rama (`feature/deciles-ingreso`) nace de `feature/filtros-y-censo`,
que a su vez no está mergeada a `main` todavía. NO hacer `git push` ni
proponer merge como parte automática de este plan — preguntar al usuario
cómo quiere integrar ambas ramas antes de tocar `main`.

---

## Auto-revisión del plan (hecha antes de entregarlo)

**Cobertura del spec:**
- Sección 1 (cálculo del decil) → Task 1. ✓
- Sección 2 (herencia hogar→persona) → Task 1 (el decil ya vive en la
  tabla de población por persona desde `cargar_poblacion`). ✓
- Sección 3 (implementación en enigh.csv.py) → Tasks 1, 2. ✓
- Sección 4 (archivo separado) → Task 3. ✓
- Sección 5 (filtro + exclusión mutua) → Task 4. ✓
- Sección 6 (forma de la gráfica, orden del eje) → Task 4 (Steps 6-8). ✓
- Sección 7 (páginas afectadas: Trabajo, Apoyos, Educación) → Tasks 5, 6. ✓

**Placeholders:** ninguno — cada step tiene código completo o comando
exacto con salida esperada.

**Consistencia de tipos/nombres:** `TODOS_DECIL`/`ETIQUETA_DECIL_COMPARAR`
(Task 4) se usan consistentemente en `panelFiltros()`, `filtrar()` y
`geometria()`, todas en el mismo archivo `filtros.js`. `dimX: "decil"`
(Task 4, `geometria()`) coincide con la llave `ETIQUETA_DIM.decil` (Task
5, `tablero.js`) y con el caso `k === "decil"` del sort (Task 4,
`prepararSeries()`) — sin nombres divergentes entre tasks.

**Riesgo detectado y resuelto durante la escritura de este plan:** el
diseño original (spec) proponía un archivo separado `indicadores_decil.csv`
sin especificar cómo el script de build real (`armar_indicadores.py`, que
NO estaba contemplado en el spec original porque se descubrió en la ronda
anterior) lo produciría. Se resolvió ampliando ese script a un tercer
archivo de salida en vez de inventar un mecanismo paralelo, y se detectó
—antes de escribir el código, no después— el riesgo de duplicar la fila
"Todos" si se explotaban dominio y decil por separado y se concatenaban;
la solución (`explotar_dimensiones()` combinada, Task 2) se diseñó
explícitamente para evitarlo, con una guardia adicional en
`armar_indicadores.py` (Task 3, Step 2) que aborta si alguna fila llegara
a tener ambas dimensiones activas a la vez, como red de seguridad ante un
futuro loader mal escrito.

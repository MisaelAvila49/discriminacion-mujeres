# Filtros de comparación + Censo primero — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reordenar/ampliar el filtro de comparación (4 pares, nuevo default M-CD vs H-CD), y subir el Censo 2020 a primer lugar del tablero con numeralia de portada migrada, panel de filtros propio y una pestaña nueva de educación.

**Architecture:** Cambios de configuración en `comparacion.js`/`filtros.js` (sin tocar datos) para la sección 1. Para la sección 2: ampliar `censo.csv.py` (loader Python/DuckDB) con 3 indicadores de educación + el bloque de distribución/dominio de dificultad que hoy vive en `enigh_distribucion.csv.py` (que se retira), reordenar `catalogo.js`/`observablehq.config.js`, migrar `index.md` a la nueva fuente, y crear 2 páginas `.md` nuevas siguiendo el patrón `dashboardTema()` ya establecido por las 9 páginas existentes.

**Tech Stack:** Observable Framework (data loaders Python + DuckDB, componentes JS/Plot), sin test runner — la verificación es: correr el loader directo y ver stderr/conteos, `npm run build` sin errores, y una revisión manual de cifras contra rangos plausibles (mismo patrón que usa todo el repo).

---

## Este plan cubre EXACTAMENTE las 2 secciones del spec aprobado

`docs/superpowers/specs/2026-08-29-filtros-y-censo-design.md`. Todo lo listado en su sección "Fuera de alcance" (deciles ENIGH, jefatura-discapacidad, hogar/persona, transporte, quién-violenta ENDIREH, dominio-de-dificultad-en-más-páginas, márgenes de error) NO se toca en este plan — son rondas futuras.

---

## Task 1: Reordenar y ampliar `COMPARACIONES`

**Files:**
- Modify: `src/components/comparacion.js:58-90`

- [ ] **Step 1: Reescribir el arreglo `COMPARACIONES` en el nuevo orden, con la comparación nueva**

El default lo fija `panelFiltros()` con `compsValidas[0]?.clave`, donde
`compsValidas` es el resultado de `comparacionesDe(fuente)` — que filtra
`COMPARACIONES` conservando su orden. Para que el default sea `disc-sexo`
(confirmado en el spec), ese elemento debe ir PRIMERO en el arreglo.

Reemplazar el bloque completo (líneas 58-90) por:

```js
export const COMPARACIONES = [
  {
    clave: "disc-sexo",
    etiqueta: "Mujeres vs Hombres con discapacidad",
    corto: "M CD vs H CD",
    grupos: ["M-CD", "H-CD"],
    colapsa: null,
    series: ["Mujeres con discapacidad", "Hombres con discapacidad"],
    llaveSerie: "grupo",
    pregunta: "Entre personas con discapacidad, ¿cuánto pesa ser mujer?",
  },
  {
    clave: "disc-mujeres",
    etiqueta: "Mujeres con vs sin discapacidad",
    corto: "M CD vs M SD",
    grupos: ["M-CD", "M-SD"],
    colapsa: null,
    series: ["Mujeres con discapacidad", "Mujeres sin discapacidad"],
    llaveSerie: "grupo",
    pregunta: "Entre mujeres, ¿cuánto pesa la discapacidad?",
  },
  {
    clave: "disc-extremo",
    etiqueta: "Mujer con discapacidad vs Hombre sin discapacidad",
    corto: "M CD vs H SD",
    grupos: ["M-CD", "H-SD"],
    colapsa: null,
    series: ["Mujeres con discapacidad", "Hombres sin discapacidad"],
    llaveSerie: "grupo",
    pregunta: "¿Qué tan grande es la brecha cuando se suman las dos desventajas?",
  },
  {
    clave: "sexo",
    etiqueta: "Mujeres vs Hombres",
    corto: "M vs H",
    grupos: ["M-CD", "M-SD", "H-CD", "H-SD"],
    colapsa: "disc",
    series: ["Mujeres", "Hombres"],
    llaveSerie: "sexo",
    pregunta: "¿Qué tan distinta es la situación de las mujeres frente a la de los hombres?",
  },
];
```

Esto SÍ da: 1º disc-sexo (default), 2º disc-mujeres, 3º disc-extremo
(nuevo), 4º sexo (al final) — coincide con lo aprobado en el spec (sección
1.1, orden numerado 1-4 ahí es orden de aparición en el menú, no de
prioridad de default; el default se confirmó explícitamente como
`disc-sexo`).

- [ ] **Step 2: Verificar que no quedó ninguna referencia directa a la posición del arreglo**

```bash
grep -n "COMPARACIONES\[0\]\|COMPARACIONES\[1\]\|COMPARACIONES\[2\]" src/components/*.js
```
Esperado: sin resultados (nada depende de índice fijo salvo
`comparacionesDe()`, que filtra por clave, no por posición literal, y ya
está correcto).

- [ ] **Step 3: Commit**

```bash
git add src/components/comparacion.js
git commit -m "feat: reordena comparaciones (default M-CD vs H-CD) y agrega M-CD vs H-SD

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

## Task 2: Fix estructural en `prepararSeries()` para filtrar por `comp.grupos`

**Files:**
- Modify: `src/components/filtros.js:254-268`

- [ ] **Step 1: Reemplazar el filtro hardcodeado por uno genérico basado en `comp.grupos`**

Reemplazar:

```js
export function prepararSeries(datos, {comparacion, dim = null, formato = "pct"}) {
  const comp = COMPARACIONES.find((c) => c.clave === comparacion);
  if (!comp) return [];
  const dims = (Array.isArray(dim) ? dim : [dim]).filter(Boolean);

  // Solo los grupos que participan en la comparación. Para "mujeres con vs
  // sin discapacidad", los hombres no entran en ningún lado.
  const filas = datos
    .filter((d) => {
      if (comp.clave === "sexo") return true;
      if (comp.clave === "disc-mujeres") return d.sexo === "Mujeres";
      if (comp.clave === "disc-sexo") return d.disc === "Con discapacidad";
      return true;
    })
    .map((d) => ({...d, serie: serieDe(d, comparacion)}));
```

Por:

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

- [ ] **Step 2: Verificar manualmente que el resultado es idéntico para las 3 comparaciones existentes**

```bash
cd src/data/dataloader
python enigh.csv.py > /tmp/enigh_check.csv 2> /tmp/enigh_check.err
```

Luego, con Node (Framework usa ESM, se puede probar el módulo con un script
suelto):

```bash
cat > /tmp/test_prepararSeries.mjs << 'EOF'
import {prepararSeries} from "../../Z:/SocialDataIbero/Framework/discriminacion-mujeres/src/components/filtros.js";
EOF
```

Nota: este import cruzado desde fuera del árbol de Framework probablemente
falla por resolución de `npm:` specifiers propios del bundler de
Observable — Framework resuelve esos imports en tiempo de build, no en
Node puro. En vez de este script, la verificación real es la Step 3
(build completo) y una revisión visual del sitio: abrir cualquier página
existente (`/encuestas/enigh/trabajo`), confirmar que las 3 comparaciones
viejas siguen mostrando las mismas cifras que antes del cambio (comparar
contra una captura o memoria de la sesión anterior: p. ej. "Mujeres con
discapacidad" en el KPI de brecha 2024 debe seguir леyendo igual).

- [ ] **Step 3: Build y confirmar sin errores**

```bash
npm run build 2>&1 | tail -30
```
Esperado: las 13 páginas renderizan (`render /encuestas/... → dist/...`),
sin excepciones de JS, tamaños de página similares a la corrida anterior
(no hay cambio de datos en este task, solo lógica de filtrado).

- [ ] **Step 4: Commit**

```bash
git add src/components/filtros.js
git commit -m "refactor: prepararSeries filtra por comp.grupos, no por clave hardcodeada

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

## Task 3: Agregar `disc-extremo` a `FUENTES`

**Files:**
- Modify: `src/components/comparacion.js` (bloque `FUENTES`, dentro del mismo archivo ya tocado en Task 1)

- [ ] **Step 1: Agregar la clave a `enadis`, `enigh` y `censo` (no `endireh`)**

Ubicar el bloque `FUENTES` (después de `COMPARACIONES` en el mismo
archivo) y cambiar cada `comparaciones: [...]` así:

```js
export const FUENTES = {
  enadis: {
    nombre: "ENADIS",
    anios: [2017, 2022],
    nivel: "nacional",
    comparaciones: ["sexo", "disc-mujeres", "disc-sexo", "disc-extremo"],
    nota: "Diseño muestral nacional: no produce estimaciones por entidad.",
  },
  enigh: {
    nombre: "ENIGH",
    anios: [2020, 2022, 2024],
    nivel: "estatal",
    comparaciones: ["sexo", "disc-mujeres", "disc-sexo", "disc-extremo"],
    nota: "Las ediciones 2016 y 2018 no traen tabla de población y quedan fuera.",
  },
  censo: {
    nombre: "Censo 2020 (cuestionario ampliado)",
    anios: [2020],
    nivel: "municipal",
    comparaciones: ["sexo", "disc-mujeres", "disc-sexo", "disc-extremo"],
    nota: "Muestra ampliada del Censo; única fuente con nivel municipal.",
  },
  endireh: {
    nombre: "ENDIREH",
    anios: [2016, 2021],
    nivel: "estatal",
    comparaciones: ["disc-mujeres"],
    nota: "Encuesta aplicada solo a mujeres de 15 años o más: no admite " +
          "comparación con hombres. La pregunta de discapacidad existe desde 2021.",
  },
};
```

(Solo cambia la línea `comparaciones:` de `enadis`, `enigh` y `censo` — el
resto del objeto queda igual; `endireh` no se toca.)

- [ ] **Step 2: Build y revisar el selector de comparación en una página de cada fuente**

```bash
npm run build 2>&1 | tail -10
```
Confirmar 0 errores. Verificación manual (levantar dev server):

```bash
npm run dev
```

Abrir `/encuestas/enigh/trabajo`, `/encuestas/enadis/educacion`,
`/encuestas/endireh/autonomia` — confirmar que el selector "Comparación"
en ENIGH y ENADIS ahora ofrece 4 opciones (con "Mujer con discapacidad vs
Hombre sin discapacidad" incluida) y abre en "Mujeres vs Hombres con
discapacidad" por default; ENDIREH sigue mostrando solo 1 opción
("Mujeres con vs sin discapacidad"), sin selector visible si
`compsValidas.length <= 1` (revisar si `panelFiltros` oculta el selector
con una sola opción — si no lo hace, es comportamiento preexistente, no
de este cambio, y no hay que arreglarlo en esta tarea).

- [ ] **Step 3: Detener el dev server**

```bash
netstat -ano | grep ":3000\|:3003" | grep LISTENING
# tomar el PID de la columna final
taskkill //F //PID <PID>
```

- [ ] **Step 4: Commit**

```bash
git add src/components/comparacion.js
git commit -m "feat: habilita disc-extremo en ENADIS, ENIGH y Censo

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

## Task 4: Reorden editorial — Censo antes de ENIGH

**Files:**
- Modify: `src/components/catalogo.js:13-51` (arreglo `ENCUESTAS`)
- Modify: `observablehq.config.js:36-62` (arreglo `pages`)

- [ ] **Step 1: Mover el bloque `censo` antes de `enigh` en `ENCUESTAS`**

En `catalogo.js`, el arreglo `ENCUESTAS` pasa de
`[enigh, endireh, censo, enadis]` a `[censo, enigh, endireh, enadis]`.
Cortar el objeto completo de `censo` (líneas 33-41 actuales) y pegarlo
como PRIMER elemento del arreglo, antes de `enigh`:

```js
export const ENCUESTAS = [
  {
    clave: "censo",
    nombre: "Censo 2020",
    titulo: "Censo de Población y Vivienda, cuestionario ampliado",
    resumen: `Quince millones de registros de persona. Es la única fuente con
      representatividad municipal y, por su tamaño, el mejor contraste para
      verificar las cifras de las encuestas.`,
    subtemas: ["numeralia-censo", "trabajo-censo", "educacion-censo"],
  },
  {
    clave: "enigh",
    nombre: "ENIGH",
    titulo: "Encuesta Nacional de Ingresos y Gastos de los Hogares",
    resumen: `Tres ediciones (2020, 2022 y 2024) con representatividad estatal.
      Es la fuente más versátil del tablero: identifica sexo y discapacidad a
      nivel persona y cubre trabajo, ingreso y conectividad.`,
    subtemas: ["trabajo", "educacion-enigh", "hogar", "apoyos", "tecnologia"],
  },
  {
    clave: "endireh",
    nombre: "ENDIREH",
    titulo: "Encuesta Nacional sobre la Dinámica de las Relaciones en los Hogares",
    resumen: `La fuente más sólida sobre violencia contra las mujeres, con
      representatividad estatal. Entrevista únicamente a mujeres de 15 años o
      más, así que solo admite la comparación entre mujeres con y sin
      discapacidad.`,
    subtemas: ["autonomia"],
  },
  {
    clave: "enadis",
    nombre: "ENADIS",
    titulo: "Encuesta Nacional sobre Discriminación",
    resumen: `La única encuesta diseñada para medir discriminación de forma
      directa. Su diseño muestral es nacional: no produce estimaciones por
      entidad, aunque el número de casos por estado lo aparente.`,
    subtemas: ["discriminacion", "educacion", "trabajo-enadis"],
  },
];
```

Nota: `subtemas` de `censo` ya incluye `"numeralia-censo"` y
`"educacion-censo"` (los dos temas nuevos de Task 6 y Task 8) — este
arreglo se edita completo en este Step, no hace falta volver a tocarlo
después.

- [ ] **Step 2: Reordenar el nav en `observablehq.config.js`**

Cambiar el bloque `pages:` (líneas 36-62 actuales) de
`[Distribución, ENIGH, ENDIREH, Censo, ENADIS, Metodología]` a
`[Distribución, Censo, ENIGH, ENDIREH, ENADIS, Metodología]`, y agregar
las 2 páginas nuevas de Censo (orden: Numeralia, Trabajo, Educación):

```js
pages: [
  {name: "Distribución", path: "/"},
  {
    name: "Censo 2020",
    open: true,
    pages: [
      {name: "Numeralia", path: "/encuestas/censo/numeralia-censo"},
      {name: "Trabajo", path: "/encuestas/censo/trabajo-censo"},
      {name: "Educación", path: "/encuestas/censo/educacion-censo"},
    ],
  },
  {
    name: "ENIGH",
    open: true,
    pages: [
      {name: "Trabajo e ingreso", path: "/encuestas/enigh/trabajo"},
      {name: "Educación", path: "/encuestas/enigh/educacion-enigh"},
      {name: "Jefatura del hogar", path: "/encuestas/enigh/hogar"},
      {name: "Apoyos y gasto", path: "/encuestas/enigh/apoyos"},
      {name: "Tecnología y conectividad", path: "/encuestas/enigh/tecnologia"},
    ],
  },
  {
    name: "ENDIREH",
    open: true,
    pages: [
      {name: "Violencia contra las mujeres", path: "/encuestas/endireh/autonomia"},
    ],
  },
  {
    name: "ENADIS",
    open: true,
    pages: [
      {name: "Discriminación vivida", path: "/encuestas/enadis/discriminacion"},
      {name: "Educación", path: "/encuestas/enadis/educacion"},
      {name: "Trabajo", path: "/encuestas/enadis/trabajo-enadis"},
    ],
  },
  {
    name: "Metodología",
    pages: [
      {name: "Fuentes y cobertura", path: "/metodologia/fuentes"},
      {name: "Definiciones", path: "/metodologia/definiciones"},
    ],
  },
],
```

Las rutas `numerlia-censo` y `educacion-censo` todavía no existen como
archivos — se crean en Task 6 y Task 8. El build fallará hasta entonces
si se corre ahora; por eso este Task 4 NO cierra con un build limpio, solo
con commit. El primer build limpio de esta ronda llega al final de Task 8.

- [ ] **Step 3: Commit (sin build todavía — las páginas nuevas no existen aún)**

```bash
git add src/components/catalogo.js observablehq.config.js
git commit -m "refactor: Censo 2020 pasa a primer lugar en encuestas y nav

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

## Task 5: Ampliar `censo.csv.py` — indicadores de educación + distribución + dominio de dificultad

Este es el task más grande: reescribe `censo.csv.py` para que además de
ocupación/quehaceres del hogar (ya existentes), calcule en la MISMA
consulta DuckDB los 3 indicadores de educación (2.4 del spec) y el bloque
de distribución/prevalencia/dominio de dificultad que hoy vive en
`enigh_distribucion.csv.py` (2.2/2.5 del spec).

**Files:**
- Modify: `src/data/dataloader/censo.csv.py` (reescritura completa)

- [ ] **Step 1: Verificar una vez más los 3 códigos antes de escribir la consulta (ya verificado en el spec, repetir aquí como guardia final del propio script)**

```bash
python3 -c "
import duckdb
con = duckdb.connect()
con.execute('PRAGMA disable_progress_bar')
ruta = r'Z:\SocialDataIbero\AnalisisSueltos\JCF\data\raw\censo2020\Personas00.CSV'.replace(chr(92), '/')
for col in ['ALFABET', 'ASISTEN']:
    q = f'SELECT {col}, COUNT(*) n FROM read_csv_auto(\"{ruta}\", ignore_errors=true) WHERE EDAD BETWEEN 18 AND 90 GROUP BY {col} ORDER BY {col}'
    print(col); print(con.execute(q).df())
"
```
Esperado (ya confirmado en la fase de spec): `ALFABET` 1=89.5%/3=10.4%/9=0.13%,
`ASISTEN` 1=5.1%/3=94.9%/9=0.06%. Si estos números NO coinciden, DETENER
— no continuar el task hasta entender la discrepancia (podría indicar que
los datos crudos cambiaron).

- [ ] **Step 2: Reescribir `censo.csv.py` completo**

```python
"""
censo.csv.py: Indicadores del Censo 2020, cuestionario ampliado.

Es la única fuente del tablero con representatividad municipal, y por eso de
aquí sale el mapa y el ranking territorial, Y AHORA TAMBIÉN la numeralia de
portada (antes construida desde ENIGH en enigh_distribucion.csv.py, retirado
en esta ronda). La muestra ampliada son ~15 millones de registros de persona
(3.3 GB en CSV), así que se procesa con DuckDB en una sola pasada agregada:
cargarla a pandas no cabe en memoria.

Semántica de los códigos, tomada de los scripts de análisis ya validados del
equipo (AnalisisSueltos/Obindi/inegi/censo_2020) y confirmada contra las
frecuencias de los propios microdatos:

  SEXO      1 = hombre, 3 = mujer.  OJO: no es 1/2 como en ENADIS y ENIGH.
            Confundirlo deja a las mujeres fuera de todo el tablero.
  DIS_*     1 = sin dificultad, 2 = limitación (lo hace con dificultad),
            3 = mucha dificultad, 4 = no puede hacerlo, 8/9 = no especificado.
            Discapacidad = 3 o 4. La "limitación" (2) NO se cuenta: es una
            categoría intermedia que el propio INEGI reporta aparte, y
            sumarla dispararía la prevalencia por encima del 10%.
  CONACT    10-19 = trabajó, 30 = buscó trabajo, 60 = quehaceres del hogar,
            50 = estudia. Es un código de dos dígitos, no de uno.

Códigos de educación, verificados por CONSISTENCIA CRUZADA contra las
frecuencias — no existe un diccionario oficial del Censo 2020 localmente
(se buscó exhaustivamente en el árbol Z:\SocialDataIbero\ antes de fijar
estos valores; ver docs/superpowers/specs/2026-08-29-filtros-y-censo-design.md
sección 2.4 para el detalle de la verificación):

  ALFABET   1 = sabe leer y escribir (89.5% de adultos), 3 = no (10.4%),
            9 = no especificado (0.13%). Mismo patrón 1=sí/3=no que SEXO.
  ASISTEN   1 = asiste a la escuela (5.1% en 18+), 3 = no (94.9%),
            9 = no especificado (0.06%).
  ESCOLARI  '00' a '08', escala ASCENDENTE de nivel aprobado (verificado
            cruzando contra ALFABET y edad promedio: '00' tiene 17.1% de
            alfabetismo y 59.7 años de edad promedio — sin escolaridad,
            población de mayor edad; '03' en adelante ya 98-100% alfabeta).
            El mapeo fino nivel-por-nivel (01=preescolar, 02=primaria...)
            NO está confirmado contra texto oficial, pero el UMBRAL que usa
            el indicador de abajo sí: educación media superior o más =
            ESCOLARI >= '04', análogo al corte NIVEL_MEDIA_SUPERIOR=4 que
            usa ENIGH sobre su propia escala 0-9 (enigh_educacion.csv.py).
            '99' = no especificado, sale del denominador.
"""

import sys
import os
import duckdb

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils_enadis import ENTIDADES, TIPOS_DISC, escribir  # noqa: E402

RUTA_CENSO = os.environ.get(
    "CENSO_PERSONAS",
    r"Z:\SocialDataIbero\AnalisisSueltos\JCF\data\raw\censo2020\Personas00.CSV",
)

COLS_DIS = [
    "DIS_VER", "DIS_OIR", "DIS_CAMINAR", "DIS_RECORDAR",
    "DIS_BANARSE", "DIS_HABLAR", "DIS_MENTAL",
]

# Etiqueta de cada columna, mismo vocabulario que TIPOS_DISC (utils_enadis.py)
# y que ETIQUETA_TIPO_DISC de ENIGH (enigh.csv.py), para que "dominio de
# dificultad" signifique lo mismo en las tres fuentes. El Censo NO tiene un
# dominio equivalente a "Brazos o manos" (disc_brazo de ENIGH): son 7
# dominios, no 8.
ETIQUETA_DOMINIO = {
    "DIS_VER": "Ver",
    "DIS_OIR": "Oír",
    "DIS_CAMINAR": "Caminar",
    "DIS_RECORDAR": "Recordar o concentrarse",
    "DIS_BANARSE": "Bañarse o vestirse",
    "DIS_HABLAR": "Hablar o comunicarse",
    "DIS_MENTAL": "Mental",
}
assert set(ETIQUETA_DOMINIO.values()) <= set(TIPOS_DISC), (
    "ETIQUETA_DOMINIO debe usar un subconjunto del vocabulario de TIPOS_DISC "
    "(utils_enadis.py) para que el filtro de dominio signifique lo mismo en "
    "todas las fuentes."
)

# Discapacidad = mucha dificultad (3) o no puede hacerlo (4).
COND_DISC = " OR ".join(f"{c} IN (3, 4)" for c in COLS_DIS)

# Los mismos rangos de edad que el resto del tablero.
CASE_EDAD = """
  CASE
    WHEN EDAD BETWEEN 18 AND 29 THEN '18-29'
    WHEN EDAD BETWEEN 30 AND 44 THEN '30-44'
    WHEN EDAD BETWEEN 45 AND 59 THEN '45-59'
    WHEN EDAD >= 60 AND EDAD < 999 THEN '60+'
  END
"""

CASE_ENT = "\n".join(
    f"    WHEN ENT = {k} THEN '{v}'" for k, v in ENTIDADES.items()
)

# Columnas de dominio de dificultad, cada una 1/0 según si la persona marcó
# discapacidad (3 o 4) en ESE dominio específico. Se seleccionan aparte del
# indicador binario `disc` porque el filtro de dominio necesita saber CUÁL
# dominio, no solo si hay alguno.
SELECT_DOMINIOS = ",\n    ".join(
    f"CASE WHEN {col} IN (3, 4) THEN 1 ELSE 0 END AS dom_{etiqueta}"
    for col, etiqueta in ETIQUETA_DOMINIO.items()
)

# Un solo barrido del archivo produce todos los indicadores a la vez: agrupa
# por las llaves del tablero y suma FACTOR de forma condicional. Recorrer
# 3.3 GB una vez por indicador costaría varias veces más sin ganar nada.
CONSULTA = f"""
WITH base AS (
  SELECT
    CASE WHEN SEXO = 1 THEN 'Hombres' WHEN SEXO = 3 THEN 'Mujeres' END AS sexo,
    CASE WHEN {COND_DISC} THEN 'Con discapacidad'
         ELSE 'Sin discapacidad' END AS disc,
    CASE
{CASE_ENT}
    END AS entidad,
    {CASE_EDAD} AS rango_edad,
    FACTOR AS factor,
    CONACT,
    ALFABET,
    ASISTEN,
    ESCOLARI,
    {SELECT_DOMINIOS}
  FROM read_csv_auto('{{ruta}}', ignore_errors=true)
  WHERE EDAD >= 18 AND EDAD < 999 AND SEXO IN (1, 3)
)
SELECT
  2020 AS anio, sexo, disc, entidad, rango_edad,
  -- Ocupación: trabajó la semana de referencia.
  SUM(CASE WHEN CONACT BETWEEN 10 AND 19 THEN factor ELSE 0 END) AS ocupada_num,
  -- Trabajo doméstico como actividad principal.
  SUM(CASE WHEN CONACT = 60 THEN factor ELSE 0 END) AS hogar_num,
  -- Denominador común de trabajo: población con condición de actividad
  -- declarada. El no especificado (99) y el nulo salen del denominador en
  -- vez de contarse como "no trabaja".
  SUM(CASE WHEN CONACT IS NOT NULL AND CONACT <> 99 THEN factor ELSE 0 END) AS den_conact,
  COUNT(*) FILTER (WHERE CONACT IS NOT NULL AND CONACT <> 99) AS casos_conact,
  -- Educación: alfabetismo, asistencia, nivel.
  SUM(CASE WHEN ALFABET = 3 THEN factor ELSE 0 END) AS no_alfabeta_num,
  SUM(CASE WHEN ALFABET IN (1, 3) THEN factor ELSE 0 END) AS den_alfabet,
  COUNT(*) FILTER (WHERE ALFABET IN (1, 3)) AS casos_alfabet,
  SUM(CASE WHEN ASISTEN = 1 AND rango_edad = '18-29' THEN factor ELSE 0 END) AS asiste_num,
  SUM(CASE WHEN ASISTEN IN (1, 3) AND rango_edad = '18-29' THEN factor ELSE 0 END) AS den_asisten,
  COUNT(*) FILTER (WHERE ASISTEN IN (1, 3) AND rango_edad = '18-29') AS casos_asisten,
  SUM(CASE WHEN ESCOLARI >= '04' THEN factor ELSE 0 END) AS media_sup_num,
  SUM(CASE WHEN ESCOLARI <> '99' THEN factor ELSE 0 END) AS den_escolari,
  COUNT(*) FILTER (WHERE ESCOLARI <> '99') AS casos_escolari,
  -- Población total del grupo (para distribución/prevalencia de portada).
  SUM(factor) AS poblacion,
  COUNT(*) AS casos_poblacion,
  {", ".join(f"SUM(CASE WHEN dom_{et} = 1 THEN factor ELSE 0 END) AS dom_{et}_num" for et in ETIQUETA_DOMINIO.values())}
FROM base
WHERE sexo IS NOT NULL AND rango_edad IS NOT NULL AND entidad IS NOT NULL
GROUP BY ALL
ORDER BY ALL
"""


def main():
    if not os.path.exists(RUTA_CENSO):
        raise SystemExit(
            f"No se encontró la muestra del Censo en {RUTA_CENSO}. "
            "Define CENSO_PERSONAS o consulta el README."
        )

    con = duckdb.connect()
    con.execute("PRAGMA disable_progress_bar")  # ensucia stderr en el build
    df = con.execute(CONSULTA.format(ruta=RUTA_CENSO.replace("\\", "/"))).df()

    if df.empty:
        raise SystemExit("El Censo no devolvió filas; revisa la ruta y los códigos.")

    # Guardia: prevalencia de discapacidad en adultos. Si SEXO o DIS_* se
    # leyeran mal, este número se dispara o se desploma.
    tot = df["poblacion"].sum()
    cd = df.loc[df["disc"] == "Con discapacidad", "poblacion"].sum()
    prev = cd / tot * 100 if tot else 0
    if not 2 <= prev <= 25:
        raise SystemExit(
            f"Censo 2020: prevalencia de discapacidad de {prev:.1f}%, fuera de "
            "rango. Revisa los códigos de DIS_* y SEXO."
        )
    print(f"[ok] Censo 2020: prevalencia de discapacidad {prev:.1f}% en 18+",
          file=sys.stderr)

    import pandas as pd
    salida = []
    fuente = "Censo de Población y Vivienda, cuestionario ampliado (INEGI)"
    universo_adultos = "Personas de 18 años o más"

    def agrega(col_num, col_den, col_casos, tema, indicador, universo=universo_adultos):
        d = df[["anio", "sexo", "disc", "entidad", "rango_edad"]].copy()
        d["num"] = df[col_num]
        d["den"] = df[col_den]
        d["casos"] = df[col_casos]
        d["tema"] = tema
        d["indicador"] = indicador
        d["fuente"] = fuente
        d["universo"] = universo
        salida.append(d)

    # --- Trabajo (ya existían) ----------------------------------------------
    agrega("ocupada_num", "den_conact", "casos_conact", "trabajo", "Población ocupada")
    agrega("hogar_num", "den_conact", "casos_conact", "trabajo",
           "Se dedica a los quehaceres del hogar")

    # --- Educación (nuevos) --------------------------------------------------
    agrega("no_alfabeta_num", "den_alfabet", "casos_alfabet",
           "educacion-censo", "No sabe leer ni escribir (Censo)")
    agrega("asiste_num", "den_asisten", "casos_asisten",
           "educacion-censo", "Asiste a la escuela (18 a 29 años, Censo)",
           universo="Personas de 18 a 29 años")
    agrega("media_sup_num", "den_escolari", "casos_escolari",
           "educacion-censo", "Educación media superior o más (Censo)")

    # --- Distribución de portada (antes en enigh_distribucion.csv.py) ------
    # Población de cada grupo: num = población del grupo, den = población
    # adulta total (2020), así que num/den es la participación del grupo.
    total_nacional = float(df["poblacion"].sum())
    d = df[["anio", "sexo", "disc", "entidad", "rango_edad"]].copy()
    d["num"] = df["poblacion"]
    d["den"] = total_nacional
    d["casos"] = df["casos_poblacion"]
    d["tema"] = "distribucion"
    d["indicador"] = "Población"
    d["fuente"] = fuente
    d["universo"] = universo_adultos
    salida.append(d)

    # Prevalencia de discapacidad: num = población con discapacidad del
    # grupo (sexo+entidad+edad), den = población total de ESE grupo.
    prev_llaves = ["anio", "sexo", "entidad", "rango_edad"]
    piv = df.groupby(prev_llaves, observed=True).apply(
        lambda x: pd.Series({
            "num": float(x.loc[x["disc"] == "Con discapacidad", "poblacion"].sum()),
            "den": float(x["poblacion"].sum()),
            "casos": int(x["casos_poblacion"].sum()),
        }), include_groups=False).reset_index()
    piv["disc"] = "Total"
    piv["tema"] = "distribucion"
    piv["indicador"] = "Prevalencia de discapacidad"
    piv["fuente"] = fuente
    piv["universo"] = universo_adultos
    salida.append(piv)

    # --- Distribución por dominio de dificultad (entre quienes tienen
    # discapacidad) -----------------------------------------------------------
    con_disc = df[df["disc"] == "Con discapacidad"]
    if len(con_disc) and cd > 0:
        for etiqueta in ETIQUETA_DOMINIO.values():
            col_dom = f"dom_{etiqueta}_num"
            t = con_disc.groupby(prev_llaves, observed=True).apply(
                lambda x: pd.Series({
                    "num": float(x[col_dom].sum()),
                    "den": float(x["poblacion"].sum()),
                    "casos": int(x["casos_poblacion"].sum()),
                }), include_groups=False).reset_index()
            t["disc"] = "Con discapacidad"
            t["tipo_discapacidad"] = etiqueta
            t["tema"] = "distribucion"
            t["indicador"] = "Distribución por dominio de dificultad"
            t["fuente"] = fuente
            t["universo"] = "Personas de 18 años o más con discapacidad"
            salida.append(t)

    todo = pd.concat(salida, ignore_index=True)
    escribir([todo])


if __name__ == "__main__":
    main()
```

**Nota importante sobre el cambio de writer**: la versión anterior escribía
su propio CSV con `todo[[...]].to_csv(sys.stdout, ...)` y una lista de
columnas SIN `tipo_discapacidad`. Esta reescritura usa `escribir()` de
`utils_enadis.py`, que ya rellena `tipo_discapacidad="Todos"` por default
y agrega la columna al esquema — necesario porque este loader ahora SÍ
produce filas con dominio de dificultad (las de
"Distribución por dominio de dificultad").

- [ ] **Step 3: Correr el loader y revisar stderr + conteo de filas**

```bash
cd src/data/dataloader
python censo.csv.py > /tmp/censo_out.csv 2> /tmp/censo_err.txt
echo "exit:$?"
grep -v "ckanext_duckdb\|addpackage\|module_from_spec\|<frozen\|<string>\|AttributeError: 'NoneType'\|Traceback (most recent" /tmp/censo_err.txt | grep -iE "error|traceback"
tail -5 /tmp/censo_err.txt
wc -l /tmp/censo_out.csv
```

Esperado: `exit:0`, sin líneas de error reales (el traceback de
`ckanext_duckdb` es el ruido de arranque conocido, ignorarlo), línea
`[ok] Censo 2020: prevalencia de discapacidad N.N% en 18+` con N.N entre
2 y 25 (la propia guardia del script ya lo exige o aborta).

- [ ] **Step 4: Verificar las cifras nuevas con pandas**

```bash
python3 -c "
import pandas as pd
df = pd.read_csv('/tmp/censo_out.csv')
print(df['indicador'].unique())
print()
edu = df[(df.indicador=='Educación media superior o más (Censo)') & (df.tipo_discapacidad=='Todos')]
print('Media superior+, por sexo y disc:')
print(edu.groupby(['sexo','disc']).apply(lambda x: x['num'].sum()/x['den'].sum()*100))
print()
dom = df[df.indicador=='Distribución por dominio de dificultad']
print('Dominios encontrados:', sorted(dom.tipo_discapacidad.unique()))
print('Cantidad de dominios:', dom.tipo_discapacidad.nunique(), '(esperado: 7)')
"
```

Esperado: 7 (no 8) dominios distintos en la última línea — confirma que
"Brazos o manos" está correctamente ausente. Las tasas de educación media
superior deben ser menores en el grupo "Con discapacidad" que en "Sin
discapacidad" para ambos sexos (mismo patrón de rezago que ya documenta
ENIGH: "solo una de cada cuatro terminó la preparatoria" entre personas
con discapacidad).

- [ ] **Step 5: Commit**

```bash
git add src/data/dataloader/censo.csv.py
git commit -m "feat: censo.csv.py agrega educación, distribución y dominio de dificultad

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

## Task 6: Retirar `enigh_distribucion.csv.py` y regenerar `indicadores.csv`/`indicadores_tipo_disc.csv`

**Files:**
- Delete: `src/data/dataloader/enigh_distribucion.csv.py`
- Modify: `src/data/indicadores.csv` (regenerado, no editado a mano)
- Modify: `src/data/indicadores_tipo_disc.csv` (regenerado, no editado a mano)

- [ ] **Step 1: Correr TODOS los loaders que alimentan `indicadores.csv`, capturando cada salida por separado**

```bash
cd src/data/dataloader
for f in enigh.csv.py enigh_jornada.csv.py enigh_educacion.csv.py enigh_tecnologia.csv.py enigh_apoyos.csv.py censo.csv.py enadis.csv.py enadis_discriminacion.csv.py endireh.csv.py; do
  echo "=== $f ==="
  python "$f" > "/tmp/out_$f.csv" 2> "/tmp/err_$f.txt"
  echo "exit:$?"
  grep -v "ckanext_duckdb\|addpackage\|module_from_spec\|<frozen\|<string>\|AttributeError: 'NoneType'\|Traceback (most recent" "/tmp/err_$f.txt" | grep -iE "error|traceback"
  tail -3 "/tmp/err_$f.txt"
  wc -l "/tmp/out_$f.csv"
done
```

Esperado: `exit:0` para los 9, sin líneas de error reales. `enigh_distribucion.csv.py`
NO está en esta lista — se retira en el Step 3.

- [ ] **Step 2: Splice — reconstruir `indicadores.csv` (Todos) e `indicadores_tipo_disc.csv` (por dominio) desde cero**

```bash
python3 << 'EOF'
import pandas as pd

archivos = [
    "enigh.csv.py", "enigh_jornada.csv.py", "enigh_educacion.csv.py",
    "enigh_tecnologia.csv.py", "enigh_apoyos.csv.py", "censo.csv.py",
    "enadis.csv.py", "enadis_discriminacion.csv.py", "endireh.csv.py",
]
partes = [pd.read_csv(f"/tmp/out_{f}.csv") for f in archivos]
todo = pd.concat(partes, ignore_index=True)

# Falta la columna `encuesta`, que indicadores.csv sí trae (usada por
# dashboardTema para filtrar por encuesta.fuentePrincipal). Se deriva de
# `fuente`.
mapa_encuesta = {
    "ENIGH (INEGI)": "enigh",
    "Censo de Población y Vivienda, cuestionario ampliado (INEGI)": "censo",
    "ENADIS (INEGI)": "enadis",
    "ENDIREH (INEGI)": "endireh",
}
todo["encuesta"] = todo["fuente"].map(mapa_encuesta)
sin_encuesta = todo["encuesta"].isna().sum()
if sin_encuesta:
    faltantes = todo.loc[todo["encuesta"].isna(), "fuente"].unique()
    raise SystemExit(f"{sin_encuesta} filas sin mapeo de encuesta. Fuentes sin mapear: {faltantes}")

principal = todo[todo["tipo_discapacidad"] == "Todos"].drop(columns=["tipo_discapacidad"])
dominio = todo[todo["tipo_discapacidad"] != "Todos"]

print("principal:", len(principal), "dominio:", len(dominio))

principal.to_csv("/tmp/indicadores_nuevo.csv", index=False)
dominio.to_csv("/tmp/indicadores_tipo_disc_nuevo.csv", index=False)
EOF
```

**IMPORTANTE — verificar el mapa `fuente → encuesta` contra los valores REALES
de `fuente` antes de correr esto**: revisar con
`grep -h "^enadis\|^enigh" src/data/dataloader/*.py | grep 'fuente ='` o
inspeccionando manualmente cada loader qué string literal usa cada uno para
`fuente` (algunos podrían diferir ligeramente, p. ej. `"ENADIS (INEGI)"` vs
otro formato) — si el script aborta con "Fuentes sin mapear", agregar la
entrada faltante al diccionario `mapa_encuesta` y volver a correr.

- [ ] **Step 3: Confirmar que las filas viejas de `tema=distribucion, fuente=ENIGH` ya no existen y las nuevas de `fuente=Censo...` sí**

```bash
python3 -c "
import pandas as pd
p = pd.read_csv('/tmp/indicadores_nuevo.csv')
dist = p[p.tema=='distribucion']
print(dist['fuente'].unique())
print(dist['indicador'].unique())
"
```
Esperado: solo `"Censo de Población y Vivienda, cuestionario ampliado
(INEGI)"` en fuente (ningún `"ENIGH (INEGI)"` para `tema=distribucion`),
e indicadores `['Población', 'Prevalencia de discapacidad']`.

- [ ] **Step 4: Copiar los dos CSV nuevos al lugar real, eliminar el loader retirado**

```bash
cp /tmp/indicadores_nuevo.csv "src/data/indicadores.csv"
cp /tmp/indicadores_tipo_disc_nuevo.csv "src/data/indicadores_tipo_disc.csv"
rm src/data/dataloader/enigh_distribucion.csv.py
```

- [ ] **Step 5: Confirmar que nada más referencia el loader retirado**

```bash
grep -rn "enigh_distribucion" src/ 2>&1
```
Esperado: sin resultados.

- [ ] **Step 6: Commit**

```bash
git add -A src/data/
git commit -m "feat: regenera indicadores.csv con Censo como fuente de distribución, retira enigh_distribucion.csv.py

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

## Task 7: Migrar `index.md` (portada) a Censo

**Files:**
- Modify: `src/index.md` (reescritura de las interpolaciones de año y la nota de fuente)

- [ ] **Step 1: Leer el archivo completo antes de editar (puede haber cambiado desde la última sesión)**

```bash
cat src/index.md
```

- [ ] **Step 2: Quitar la interpolación de año variable — Censo es un solo corte fijo en 2020**

Cambiar:

```js
const anio = d3.max(indicadores.filter((d) => d.tema === "distribucion"), (d) => d.anio);
```

Por:

```js
// Censo 2020 es un solo corte: no hay edición que comparar, así que el año
// se fija en vez de tomarlo de los datos (antes venía de ENIGH, que sí
// tiene tres ediciones).
const anio = 2020;
```

El resto del código que usa `anio` (líneas con `d.anio === anio`,
`` `Personas con discapacidad · ${anio}` ``, etc.) NO cambia — sigue
funcionando igual, solo que ahora `anio` es una constante en vez de un
`d3.max` calculado.

- [ ] **Step 3: Actualizar la nota al pie de fuente**

Cambiar:

```markdown
**Sobre estas cifras.** Provienen de la ENIGH ${anio} y están expandidas con el
factor de la encuesta. La condición de discapacidad se define como declarar que
no se puede hacer o se tiene mucha dificultad para al menos una de ocho
actividades básicas; la categoría intermedia de "poca dificultad" queda fuera,
siguiendo el criterio del INEGI. Los detalles están en
[Definiciones](/metodologia/definiciones).
```

Por:

```markdown
**Sobre estas cifras.** Provienen del Censo de Población y Vivienda 2020,
cuestionario ampliado, y están expandidas con el factor de la muestra. La
condición de discapacidad se define como declarar mucha dificultad o no
poder hacer al menos una de siete actividades básicas; la categoría
intermedia de "lo hace con dificultad" queda fuera, siguiendo el criterio
del INEGI. Los detalles están en
[Definiciones](/metodologia/definiciones).
```

(Nota: dice "siete actividades", no "ocho" — el Censo tiene 7 dominios,
ENIGH tiene 8. Este archivo lee del Censo ahora, así que el número debe
coincidir con esta fuente.)

- [ ] **Step 4: Revisar si el mapa/gráfica de "Prevalencia de discapacidad por edad" cita la fuente correcta**

Buscar en el archivo la línea con `fuente: "ENIGH (INEGI)"` dentro de la
llamada a `barrasComparadas` o `mapaEntidades` (visto en la versión leída
en sesiones anteriores, alrededor de la sección "02 · La discapacidad
crece con la edad" y "03 · Dónde vive la población con discapacidad") y
cambiarla a:

```js
fuente: "Censo de Población y Vivienda, cuestionario ampliado (INEGI)",
```

en AMBAS gráficas de la página (la de prevalencia por edad y la del mapa).

- [ ] **Step 5: Build y comparar cifras contra un valor de referencia**

```bash
npm run build 2>&1 | tail -20
```
Esperado: `render /index → dist/index.html` sin error. Levantar dev
server y revisar visualmente:

```bash
npm run dev
```

Abrir `/` — confirmar: los 3 KPIs muestran cifras (millones de personas
con discapacidad, % que son mujeres, población total), sin `undefined` ni
`NaN`; el pie de página dice "Censo de Población y Vivienda 2020"; no hay
selector de año visible (nunca lo hubo en esta página, se mantiene igual).

- [ ] **Step 6: Detener dev server y commit**

```bash
netstat -ano | grep ":3000\|:3003" | grep LISTENING
taskkill //F //PID <PID>
git add src/index.md
git commit -m "feat: portada usa Censo 2020 en vez de ENIGH

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

## Task 8: Página nueva "Numeralia" del Censo

**Files:**
- Create: `src/encuestas/censo/numeralia-censo.md`
- Modify: `src/components/catalogo.js` (agregar entrada `"numeralia-censo"` a `CATALOGO`)

- [ ] **Step 1: Agregar la entrada al catálogo, en el bloque `// --- Censo ---` (antes de `trabajo-censo`)**

```js
// --- Censo ---------------------------------------------------------------
"numeralia-censo": {
  encuesta: "censo",
  titulo: "Numeralia",
  kicker: "Numeralia",
  entrada: `La misma cifra de la portada, pero con filtros: cuántas personas
    hay en cada grupo, y cómo cambia la prevalencia de discapacidad por
    edad, entidad y dominio de dificultad.`,
  fuentePrincipal: "censo",
  indicadorPrincipal: "Prevalencia de discapacidad",
  formato: "pct",
  explica: `Porcentaje de personas de cada grupo (sexo, edad, entidad) que
    tiene discapacidad, definida como declarar mucha dificultad o no poder
    hacer al menos una de siete actividades básicas. El Censo es la única
    fuente con representatividad municipal, así que es la más confiable
    para ver cómo varía la prevalencia por entidad.`,
  secundarios: [],
},
```

Nota: `indicadorPrincipal: "Prevalencia de discapacidad"` usa
`tema="distribucion"` con `disc="Total"` (columna fija, ver Task 5) —
`dashboardTema()` filtra por `d.indicador === tema.indicadorPrincipal`
directamente, sin filtrar por `tema`, así que esto funciona sin cambios
adicionales en `tablero.js`. Verificar en el Step 4 de este task que las
comparaciones sexo/disc-mujeres/disc-sexo/disc-extremo tienen sentido
sobre un indicador cuya fila trae `disc="Total"` fijo — si `prepararSeries`
filtra por `d.disc === "Con discapacidad"` (comparación `disc-sexo`) y
TODAS las filas de este indicador tienen `disc="Total"`, el resultado
sale VACÍO para esas 3 comparaciones. Esto es un problema real a
resolver en el Step 2.

- [ ] **Step 2: Resolver el conflicto disc="Total" vs las comparaciones basadas en discapacidad**

El indicador "Prevalencia de discapacidad" no tiene sentido cruzado con
"disc-mujeres"/"disc-sexo"/"disc-extremo" (esas comparaciones YA asumen
que la fila pertenece a un grupo con/sin discapacidad conocido; la
prevalencia ES esa medida, no puede filtrarse por ella misma). La
solución: esta página usa como indicador principal **"Población"**
(conteo, ya trae `sexo`+`disc` reales, no `disc="Total"`), y muestra la
prevalencia como una gráfica SECUNDARIA aparte con su propio manejo, NO
como indicador principal del motor `dashboardTema`.

Corregir la entrada del catálogo:

```js
"numeralia-censo": {
  encuesta: "censo",
  titulo: "Numeralia",
  kicker: "Numeralia",
  entrada: `La misma cifra de la portada, pero con filtros: cuántas personas
    hay en cada grupo, y cómo cambia la prevalencia de discapacidad por
    edad, entidad y dominio de dificultad.`,
  fuentePrincipal: "censo",
  indicadorPrincipal: "Población",
  formato: "pesos",
  explica: `Personas expandidas de cada grupo (sexo, discapacidad, edad,
    entidad). No es un porcentaje: es el conteo absoluto de población,
    la misma cifra que ya usa la portada.`,
  secundarios: [],
},
```

`formato: "pesos"` es un truco deliberado: el indicador "Población" no es
una tasa (num/den da la PARTICIPACIÓN del grupo en el total, ver docstring
del Task 5), así que se formatea como cifra absoluta con
`formatear(valor, "pesos")` → `"$" + Math.round(valor).toLocaleString()`.
Esto muestra un número con separador de miles pero antecedido de "$", que
es visualmente incorrecto (no es dinero). Antes de aceptar este truco,
revisar si `graficas.js`/`formatear()` admite un tercer formato genuino
("conteo" o similar) — si no existe, AGREGARLO en este mismo task en vez
de reusar "pesos" con una etiqueta incorrecta:

En `src/components/graficas.js`, función `formatear()` (línea ~53):

```js
export function formatear(valor, formato = "pct") {
  if (valor == null || !isFinite(valor)) return "s/d";
  if (formato === "pesos") {
    return "$" + Math.round(valor).toLocaleString("es-MX");
  }
  if (formato === "horas") return `${valor.toFixed(1)} h`;
  if (formato === "conteo") return Math.round(valor).toLocaleString("es-MX");
  return `${valor.toFixed(1)}%`;
}
```

Y en la misma función/archivo, buscar `ejeValor()` (usada por
`barrasComparadas` para la escala del eje Y) y agregar el mismo caso
`"conteo"` con la misma forma que `"pesos"` pero sin el prefijo `"$"`:

```js
// buscar el bloque existente tipo:
//   if (formato === "pesos") {
//     return {label: "pesos", grid: true, tickFormat: ...};
//   }
// y agregar justo después:
if (formato === "conteo") {
  return {label: "personas", grid: true,
          tickFormat: (d) => d.toLocaleString("es-MX")};
}
```

Actualizar la entrada del catálogo para usar `formato: "conteo"` en vez
de `"pesos"`.

- [ ] **Step 3: Crear la página `.md`**

```markdown
# Numeralia del Censo

```js
import {dashboardTema} from "../../components/tablero.js";
const indicadores = await FileAttachment("../../data/indicadores.csv").csv({typed: true});
const indicadoresTipoDisc = await FileAttachment("../../data/indicadores_tipo_disc.csv").csv({typed: true});
const geoEntidades = await FileAttachment("../../data/mx_entidades.json").json();
```

```js
display(dashboardTema("numeralia-censo", indicadores, {geoEntidades, datosTipoDisc: indicadoresTipoDisc}));
```
```

(Mismo patrón EXACTO que las 9 páginas existentes — sin filtro de año
porque `censo` solo tiene `anios: [2020]`, y `panelFiltros()` ya oculta el
selector de año cuando `anios.length <= 1`, sin necesidad de código
adicional.)

- [ ] **Step 4: Build y revisar la página en el navegador**

```bash
npm run build 2>&1 | tail -20
```
Esperado: `render /encuestas/censo/numeralia-censo → dist/...`, sin error.

```bash
npm run dev
```
Abrir `/encuestas/censo/numeralia-censo` — confirmar: el panel de filtros
muestra Comparación (4 opciones), Entidad, Rango de edad, y Dominio de
dificultad (visible SOLO cuando la comparación es "Mujeres vs Hombres con
discapacidad" — mismo comportamiento ya implementado en `filtros.js`); las
cifras del indicador principal se leen como población absoluta (con
separador de miles, sin "%" ni "$"); cambiar la comparación a las 4
opciones y confirmar que ninguna produce una gráfica vacía o rota.

- [ ] **Step 5: Detener dev server y commit**

```bash
netstat -ano | grep ":3000\|:3003" | grep LISTENING
taskkill //F //PID <PID>
git add src/components/catalogo.js src/components/graficas.js src/encuestas/censo/numeralia-censo.md
git commit -m "feat: nueva página Numeralia del Censo con filtros completos

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

## Task 9: Página nueva "Educación" del Censo

**Files:**
- Create: `src/encuestas/censo/educacion-censo.md`
- Modify: `src/components/catalogo.js` (agregar entrada `"educacion-censo"` a `CATALOGO`)

- [ ] **Step 1: Agregar la entrada al catálogo, después de `trabajo-censo`**

```js
"educacion-censo": {
  encuesta: "censo",
  titulo: "Educación según el Censo",
  kicker: "Educación",
  entrada: `El Censo mide escolaridad con una muestra mil veces más grande
    que cualquier encuesta y con desagregación municipal, así que sirve de
    verificación cruzada de los indicadores de ENIGH y ENADIS.`,
  fuentePrincipal: "censo",
  indicadorPrincipal: "Educación media superior o más (Censo)",
  formato: "pct",
  explica: `Porcentaje de personas cuyo nivel de escolaridad aprobado
    corresponde a preparatoria o superior (código ESCOLARI 04 en adelante
    de la escala del Censo, 00 a 08). Quienes no declararon su nivel
    salen del denominador en vez de contarse como si no tuvieran
    estudios.`,
  secundarios: [
    {encuesta: "censo", indicador: "No sabe leer ni escribir (Censo)", formato: "pct",
     explica: `Porcentaje de personas que declararon no saber leer ni
       escribir. Comparable con el mismo indicador de ENIGH y ENADIS,
       aunque el instrumento no sea idéntico.`},
    {encuesta: "censo", indicador: "Asiste a la escuela (18 a 29 años, Censo)", formato: "pct",
     explica: `Porcentaje de personas de 18 a 29 años inscritas y
       asistiendo a la escuela.`},
  ],
},
```

- [ ] **Step 2: Crear la página `.md`**

```markdown
# Educación según el Censo

```js
import {dashboardTema} from "../../components/tablero.js";
const indicadores = await FileAttachment("../../data/indicadores.csv").csv({typed: true});
const indicadoresTipoDisc = await FileAttachment("../../data/indicadores_tipo_disc.csv").csv({typed: true});
const geoEntidades = await FileAttachment("../../data/mx_entidades.json").json();
```

```js
display(dashboardTema("educacion-censo", indicadores, {geoEntidades, datosTipoDisc: indicadoresTipoDisc}));
```
```

- [ ] **Step 3: Build completo (primera vez que TODAS las rutas del nav existen)**

```bash
npm run build 2>&1 | tail -40
```

Esperado: las 15 páginas renderizan (13 anteriores + 2 nuevas de Censo)
sin error, `1 link validated` al final (o el número de links que
corresponda), y en el árbol de tamaños el bloque "Censo 2020" aparece
ANTES que "ENIGH".

- [ ] **Step 4: Revisar en el navegador la página nueva y confirmar cifras contra ENIGH**

```bash
npm run dev
```

Abrir `/encuestas/censo/educacion-censo` — confirmar: KPI de brecha entre
"Mujeres con discapacidad" y "Hombres con discapacidad" (comparación
default) tiene el mismo SIGNO que el indicador equivalente de
`/encuestas/enigh/educacion-enigh` (ambas fuentes deben coincidir en
DIRECCIÓN del rezago educativo por discapacidad, aunque la magnitud
exacta difiera por instrumento distinto — si el signo se invierte entre
Censo y ENIGH para el mismo hallazgo, DETENER e investigar antes de
continuar, es la señal clásica de una escala de discapacidad invertida).

- [ ] **Step 5: Detener dev server y commit**

```bash
netstat -ano | grep ":3000\|:3003" | grep LISTENING
taskkill //F //PID <PID>
git add src/components/catalogo.js src/encuestas/censo/educacion-censo.md
git commit -m "feat: nueva página Educación del Censo (alfabetismo, asistencia, nivel)

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

## Task 10: Verificación final de la ronda completa

**Files:** ninguno nuevo — solo verificación.

- [ ] **Step 1: Build limpio desde cero**

```bash
rm -rf dist .observablehq/cache
npm run build 2>&1 | tail -50
```
Esperado: 0 errores, 15 páginas, tamaños de archivo razonables (los 4
temas ENIGH que ya usaban `indicadores_tipo_disc.csv` deben seguir en
~29MB; las páginas nuevas de Censo que también lo cargan (Numeralia,
Educación) sumarán ese mismo peso — revisar que no se disparó a un
tamaño absurdo por el crecimiento del archivo con los 7 dominios nuevos
de Censo).

- [ ] **Step 2: Recorrido manual de las 15 páginas**

```bash
npm run dev
```

Visitar cada ruta del nav (usar la barra lateral) y confirmar, para cada
una: (a) sin error de consola visible, (b) el panel de filtros ofrece 4
comparaciones donde corresponda (todas menos ENDIREH), con default
"Mujeres vs Hombres con discapacidad", (c) las páginas de ENIGH (trabajo,
educación, hogar, apoyos, tecnología) siguen mostrando las mismas cifras
que antes de esta ronda (nada en esta ronda tocó sus datos).

- [ ] **Step 3: Detener dev server**

```bash
netstat -ano | grep ":3000\|:3003" | grep LISTENING
taskkill //F //PID <PID>
```

- [ ] **Step 4: Push (si el usuario lo pide explícitamente — no antes)**

Este repo tiene `origin/main` un commit atrás desde el inicio de esta
sesión (ver `git status` al arrancar). NO hacer `git push` como parte
automática de este plan — preguntar al usuario si quiere publicar los
commits de esta ronda antes de subirlos.

---

## Auto-revisión del plan (hecha antes de entregarlo)

**Cobertura del spec:**
- Sección 1.1 (orden/default) → Task 1. ✓
- Sección 1.2 (nueva comparación) → Task 1. ✓
- Sección 1.3 (fix estructural) → Task 2. ✓
- Sección 1.4 (FUENTES) → Task 3. ✓
- Sección 2.1 (reorden editorial) → Task 4. ✓
- Sección 2.2 (portada→Censo) → Tasks 5, 6, 7. ✓
- Sección 2.3 (pestaña Numeralia) → Task 8. ✓
- Sección 2.4 (pestaña Educación) → Tasks 5, 9. ✓
- Sección 2.5 (dominio de dificultad en Censo) → Task 5. ✓

**Placeholders:** ninguno — cada step tiene código completo o comando
exacto con salida esperada.

**Consistencia de tipos/nombres:** `ETIQUETA_DOMINIO` (Censo, Task 5) usa
las mismas 7 etiquetas string que `ETIQUETA_TIPO_DISC` (ENIGH) y
`TIPOS_DISC` (ENADIS/utils_enadis.py) — verificado con el `assert` dentro
del propio loader. `formato: "conteo"` se define en `graficas.js` (Task 8)
antes de usarse en `catalogo.js` (mismo Task 8) — sin referencias
adelantadas a algo no definido todavía.

**Riesgo detectado y resuelto durante la escritura de este plan:** el
task 8 originalmente asumía que "Prevalencia de discapacidad" podía ser
el indicador principal de la página Numeralia; se detectó en el propio
Step 1 de ese task que las filas de ese indicador traen `disc="Total"`
fijo, incompatible con las comparaciones basadas en discapacidad — se
corrigió a usar "Población" como principal y se documentó la razón
inline, en vez de dejarlo como problema para "cuando se implemente".

# Filtros de comparación + Censo primero

Fecha: 2026-08-29. Primera de varias rondas sobre una lista más grande de
pendientes (ver "Fuera de alcance" al final); esta ronda cubre solo las dos
piezas ya aprobadas: reordenar/ampliar el filtro de comparación, y subir el
Censo 2020 a primer lugar del tablero con numeralia propia y una pestaña
nueva de educación.

## 1. Filtro de comparación

### 1.1 Nuevo orden y default

`COMPARACIONES` en `comparacion.js` pasa de
`[sexo, disc-mujeres, disc-sexo]` (default `sexo`) a:

1. `disc-mujeres` — Mujeres con vs sin discapacidad
2. `disc-sexo` — Mujeres vs Hombres con discapacidad (**nuevo default**)
3. `disc-extremo` (nuevo) — Mujer con discapacidad vs Hombre sin discapacidad
4. `sexo` — Mujeres vs Hombres (ahora al final)

El orden del arreglo es el orden en que `Inputs.select` los ofrece, así que
reordenar el arreglo basta; el default se fija con
`comparacionInicial ?? compsValidas[0]?.clave` en `panelFiltros()`
(`filtros.js`) — cambia solo si `compsValidas[0]` cambia, que es justo lo que
hace el reorden.

### 1.2 Nueva comparación `disc-extremo`

```js
{
  clave: "disc-extremo",
  etiqueta: "Mujer con discapacidad vs Hombre sin discapacidad",
  corto: "M CD vs H SD",
  grupos: ["M-CD", "H-SD"],
  colapsa: null,
  series: ["Mujeres con discapacidad", "Hombres sin discapacidad"],
  llaveSerie: "grupo",
  pregunta: "¿Qué tan grande es la brecha cuando se suman las dos desventajas?",
}
```

Color: `escalaColor()` ya resuelve genérico por `c.grupos.map(k =>
GRUPO_POR_CLAVE[k].color)` cuando `llaveSerie === "grupo"` — no necesita
cambio. M-CD usa el naranja pleno (`#E8930C`), H-SD el azul aclarado
(`#8FB8DA`), ambos ya definidos en `GRUPOS`.

### 1.3 Fix estructural en `prepararSeries()` (`filtros.js`)

El filtro de "qué filas participan en la comparación" hoy es un `if` por
`comp.clave` (`sexo` / `disc-mujeres` / `disc-sexo`), no genérico por
`comp.grupos`. Añadir un cuarto branch a mano funcionaría, pero deja la
misma trampa para una 5ª comparación futura. Se reescribe genérico:

```js
function claveDeFila(d) {
  const s = d.sexo === "Mujeres" ? "M" : "H";
  const c = d.disc === "Con discapacidad" ? "CD" : "SD";
  return `${s}-${c}`;
}
// ...
const filas = datos
  .filter((d) => comp.clave === "sexo" || comp.grupos.includes(claveDeFila(d)))
  .map((d) => ({...d, serie: serieDe(d, comparacion)}));
```

`sexo` sigue sin filtrar (usa los 4 grupos, colapsando disc). Las otras tres
comparaciones filtran por pertenencia real a `comp.grupos`, que ya está
declarado en cada entrada de `COMPARACIONES` — una sola fuente de verdad en
vez de dos (el `clave` string Y una condición aparte).

### 1.4 `FUENTES`

Se agrega `"disc-extremo"` a `comparaciones` de `enadis`, `enigh` y `censo`.
`endireh` no la admite (sigue sin población masculina).

### Impacto

Las 9 páginas ya existentes que usan `dashboardTema()`/dashboard compartido
cambian de comparación default (antes M vs H, ahora M-CD vs H-CD) y ganan la
4ª opción. Cero cambios a datos, solo configuración — riesgo bajo, sin
necesidad de regenerar ningún CSV. Esta pieza (sección 1) se implementa
ANTES que la sección 2: las páginas nuevas de Censo (2.3/2.4) nacen ya con
las 4 comparaciones disponibles, sin necesidad de tocarlas después.

---

## 2. Censo primero + numeralia + pestaña de educación

### 2.1 Reorden editorial

- `catalogo.js`: `ENCUESTAS` — Censo sube antes de ENIGH.
- `observablehq.config.js`: bloque de nav `"Censo 2020"` sube antes de
  `"ENIGH"`.

### 2.2 Portada migra a Censo

`index.md` sigue leyendo `tema === "distribucion"`, pero esa tabla la
genera ahora `censo.csv.py` en vez de `enigh_distribucion.csv.py` (que se
retira — sus dos indicadores, "Población" y "Prevalencia de discapacidad",
se reconstruyen desde el Censo con el mismo esquema exacto: mismas llaves
`anio, sexo, disc, entidad, rango_edad`, mismo significado de `num`/`den`
documentado en el docstring actual de `enigh_distribucion.csv.py`).

Cambios de contenido en `index.md`:
- El filtro de edición desaparece (Censo es un solo corte). Los `${anio}`
  en títulos y notas se fijan a `"2020"` en vez de interpolar una variable
  que ya no varía.
- Nota al pie: "provienen del Censo de Población y Vivienda 2020,
  cuestionario ampliado" (reemplaza "provienen de la ENIGH ${anio}").
- El resto de la estructura (3 KPIs, barras de los 4 grupos, prevalencia por
  edad, mapa por entidad) no cambia — mismo componente, misma forma.

`enigh_distribucion.csv.py` se elimina del pipeline de loaders (igual que se
retiró `apoyosHogar.js` en la ronda anterior): ya no se ejecuta, y sus filas
de `tema=distribucion` con `fuente="ENIGH (INEGI)"` se reemplazan en
`indicadores.csv` por las nuevas con `fuente="Censo de Población y
Vivienda, cuestionario ampliado (INEGI)"` (mismo string que ya usa
`censo.csv.py` para sus otros indicadores, así que la portada y la nueva
pestaña de numeralia citan la misma fuente sin duplicar el nombre).

### 2.3 Nueva pestaña "Numeralia" en Censo

Ruta `/encuestas/censo/numeralia`, primera pestaña del bloque Censo en el
nav (antes de "Trabajo"). Misma cifra de portada, pero con panel de filtros
real: entidad, rango de edad, y dominio de dificultad (nuevo para Censo, ver
2.5). Sin filtro de año (un solo corte). Construida con el mismo patrón que
`bloqueGrafica()`/`seccion()` de `tablero.js`, no un componente aparte.

### 2.4 Censo — pestaña "Educación" (`tema="educacion-censo"`)

Ampliación de `censo.csv.py`: se agregan tres indicadores nuevos al mismo
barrido DuckDB que ya calcula ocupación/quehaceres del hogar (una sola
pasada por el archivo de 3.3GB, sin costo adicional de I/O).

Códigos verificados contra las frecuencias de los microdatos (no existe un
diccionario oficial del Censo 2020 en el sistema — se confirmó por búsqueda
exhaustiva antes de escribir este spec; los valores siguientes se
verificaron por consistencia cruzada, mismo criterio que ya usa el proyecto
para la escala de discapacidad):

- **`ALFABET`** (1 = sabe leer y escribir, 3 = no, 9 = no especificado).
  Verificado: código 1 = 89.5% de la población adulta (cifra plausible de
  alfabetismo nacional), código 3 = 10.4%. Indicador:
  "No sabe leer ni escribir (Censo)" — mismo nombre-patrón que el ya
  existente "No sabe leer ni escribir (ENIGH)", para poder contrastarlas.

- **`ASISTEN`** (1 = asiste a la escuela, 3 = no, 9 = no especificado).
  Verificado: código 1 = 5.1% en población de 18+ (plausible: la mayoría de
  adultos ya no asiste), código 3 = 94.9%. Indicador:
  "Asiste a la escuela (18 a 29 años, Censo)", mismo corte de edad que su
  equivalente ENIGH.

- **`ESCOLARI`** (00 a 08, escala ascendente de nivel aprobado; 99 = no
  especificado). Verificado cruzando contra `ALFABET` y edad promedio: 00
  tiene 17.1% de alfabetismo y 59.7 años de edad promedio (sin escolaridad,
  población mayor); 03 en adelante ya 98-100% alfabeta. El mapeo fino
  01→preescolar, 02→primaria, 03→secundaria, 04→preparatoria... no está
  confirmado contra un texto oficial (no existe ese documento localmente),
  pero el UMBRAL que necesita el indicador sí está confirmado por la
  monotonía de la tasa de alfabetismo: **educación media superior o más =
  `ESCOLARI >= '04'`**, análogo al corte que ya usa ENIGH
  (`NIVEL_MEDIA_SUPERIOR = 4` sobre su propia escala 0-9). Indicador:
  "Educación media superior o más (Censo)".

Universo de los tres: personas de 18 años o más (mismo filtro `EDAD >= 18`
que ya aplica la CTE `base` de `censo.csv.py`), excepto asistencia escolar
que además acota a 18-29.

`catalogo.js`: nueva entrada `"educacion-censo"` en `CATALOGO`,
`fuentePrincipal: "censo"`, `indicadorPrincipal: "Educación media superior o
más (Censo)"`, secundarios: alfabetismo y asistencia escolar. Nueva página
`/encuestas/censo/educacion-censo.md`, patrón idéntico a las páginas
`dashboardTema()` existentes. Nav: `"Censo 2020" → ["Numeralia", "Trabajo",
"Educación"]`.

### 2.5 Dominio de dificultad en Censo

El Censo tiene **7 dominios**, no 8: `DIS_VER, DIS_OIR, DIS_CAMINAR,
DIS_RECORDAR, DIS_BANARSE, DIS_HABLAR, DIS_MENTAL` — falta el equivalente a
`disc_brazo` ("Brazos o manos") que sí tiene ENIGH. Mapeo de etiquetas
reutiliza el vocabulario ya establecido en `utils_enadis.TIPOS_DISC`/
`enigh.ETIQUETA_TIPO_DISC` (Ver, Oír, Caminar, Recordar o concentrarse,
Bañarse o vestirse, Hablar o comunicarse, Mental), simplemente sin la
opción "Brazos o manos" en esta fuente. Mismo patrón de explosión que
`enigh.explotar_tipo_discapacidad()`: una columna booleana por dominio, una
fila "Todos" (comportamiento de hoy) + una fila por dominio con dificultad,
solo para personas con discapacidad. Alimenta el mismo archivo separado
`indicadores_tipo_disc.csv` (no crece `indicadores.csv` base), consistente
con la partición ya hecha para no inflar la descarga de las páginas que no
usan el filtro.

Este punto (2.5) es la única pieza de esta ronda que toca la pieza más
grande "dominio de dificultad en más páginas" del pedido original — se
incluye aquí porque Censo lo necesita de todas formas para la pestaña
Numeralia (punto 2.3), no como adelanto general del resto de encuestas.

### Fuera de alcance de esta ronda (pendiente, rondas futuras)

- Vivienda en Censo (requiere unir `Personas00.CSV` con `Viviendas00.CSV`
  por `ID_VIV`, consulta DuckDB más pesada — confirmado explícitamente con
  el usuario que se pospone).
- ENIGH: deciles de ingreso, jefatura de hogar con discapacidad, etiqueta
  hogar/persona en cada página, gasto en transporte (taxi/Uber).
- ENDIREH: análisis de quién violenta.
- Dominio de dificultad en el resto de páginas (ENADIS, ENDIREH, y las
  páginas ENIGH que no lo tienen todavía más que apoyos/trabajo/
  educación/tecnología, ya hecho en la ronda anterior).
- Márgenes de error / intervalos de confianza que crecen con más filtros —
  el usuario pidió explícitamente NO implementarlo todavía, solo confirmar
  si es calculable. Respuesta corta: sí, con el error estándar de una
  proporción ponderada (fórmula de Kish para diseño muestral complejo,
  requiere el factor de diseño `deff` de cada encuesta, que no todas
  publican) — se deja para una ronda de diseño propia cuando se decida
  implementar.

# Deciles de ingreso en ENIGH (Trabajo, Apoyos, Educación)

Fecha: 2026-08-30. Primera de varias rondas sobre la lista de pendientes
confirmada tras la ronda de Censo (ver mensaje del usuario "falta algo más de
lo que te pedí"): deciles de ingreso, hogar-vs-persona, gasto en transporte,
ENDIREH quién-violenta, dominio-de-dificultad-en-más-páginas. Esta ronda
cubre SOLO deciles. Aportación al hogar y jefatura con discapacidad, aunque
se mencionaron junto con deciles en el pedido original, quedan
explícitamente para una ronda aparte (confirmado con el usuario).

## 1. Qué es el decil y cómo se calcula

El decil de ingreso mide qué tan rico o pobre es el HOGAR de una persona,
en una escala de 1 (10% más pobre) a 10 (10% más rico) de la distribución
nacional ponderada. ENIGH no trae una columna de decil ya calculada; se
construye desde `concentradohogar{año}.csv` (tabla de hogar, ya usada hoy
solo para heredar `factor` en 2020):

```
ing_cor_percapita = ing_cor / tot_integ
decil = percentil ponderado por factor de ing_cor_percapita,
        cortado en los deciles 10/20/.../90 (criterio oficial INEGI:
        ingreso corriente TRIMESTRAL per cápita del hogar — ing_cor en
        concentradohogar ya viene en esa unidad, mediana $46,074/trimestre
        por hogar en 2022, consistente con esa magnitud; NO es anual).
```

Verificado contra los microdatos crudos de 2022: `ing_cor` sin nulos,
`tot_integ` nunca 0 (sin riesgo de división por cero), 90,102 hogares.

**El decil NO se deflacta entre ediciones.** A diferencia de los montos en
pesos (que sí usan `deflactor.py` para comparar 2020/2022/2024 en pesos
constantes), el decil es un RANKING dentro de la distribución de CADA año
por separado — el hogar en el decil 3 de 2020 y el hogar en el decil 3 de
2024 son ambos "el 20-30% más pobre de su propio año", una comparación que
no necesita ajuste de inflación. Mezclar deciles de años distintos como si
fueran una sola escala continua sería el error; compararlos año por año
(cada uno resuelto dentro de su propia distribución) es correcto y es
exactamente lo que hace este diseño.

## 2. Herencia hogar → persona

Cada persona de la tabla de población hereda el decil de SU hogar (mismo
folioviv+foliohog), igual criterio que ya usa el proyecto para "recibe la
beca" en `apoyos.md` (dato de hogar heredado a persona) y para el `factor`
de 2020. Confirmado con el usuario: NO se construye un modelo aparte a
nivel hogar (ese patrón se descartó explícitamente en la ronda anterior).

## 3. Implementación en `enigh.csv.py`

- `cargar_poblacion(year)`: el merge con `concentradohogar` que hoy es
  CONDICIONAL (solo si falta `factor`, solo 2020) pasa a ser SIEMPRE, para
  los 3 años, trayendo también `ing_cor` y `tot_integ` además de `factor`.
  Para 2022/2024 (que ya traen `factor` a nivel persona) el merge se hace
  igual pero solo para las 2 columnas nuevas, sin pisar el `factor` de
  persona ya presente.
- Nueva función `_calcular_decil(hog)`: recibe el DataFrame de
  `concentradohogar` ya cargado, calcula `ing_cor_percapita`, y devuelve
  una columna `decil` (entero 1-10) usando percentiles ponderados por
  `factor` — sin librería externa nueva, con `numpy`/`pandas` puro
  (`np.average` con pesos para el ingreso acumulado ponderado, o
  equivalente; el detalle exacto se resuelve en el plan de implementación,
  no en este spec).
- Guardia de sanidad: cada decil debe concentrar aproximadamente 10% ± 2pp
  de la población ponderada (los deciles no son EXACTAMENTE 10% cada uno
  por los empates en el corte, pero deben estar cerca). Si algún decil se
  sale de un rango razonable (por ejemplo <5% o >15%), el script aborta —
  mismo criterio de "abortar antes que publicar mal" que ya usan las
  guardias de prevalencia de discapacidad y del deflactor.
- `explotar_decil(df)`: mismo patrón que `explotar_tipo_discapacidad()` —
  agrega una fila `decil="Todos"` (comportamiento agregado, hoy) MÁS una
  fila por cada decil real (1-10) para quien quiera comparar. A diferencia
  de dominio de dificultad (que solo aplica a personas CON discapacidad),
  el decil aplica a TODAS las personas, con y sin discapacidad — así que
  no hay problema de universo parcial aquí.

## 4. Esquema de datos: archivo separado

Mismo patrón que `indicadores_tipo_disc.csv`: el decil multiplica las
filas por ~10 (una fila "Todos" + 10 por decil), así que va en un archivo
NUEVO y separado, `indicadores_decil.csv`, para que las páginas que no lo
usan (todas menos Trabajo/Apoyos/Educación) no paguen ese peso de
descarga. `escribir()` (`utils_enadis.py`) necesita una nueva columna
opcional `decil` con el mismo mecanismo de default (`"Todos"` si el loader
no la trae) que ya tiene para `tipo_discapacidad` — los demás 8 loaders
(ENADIS, Censo, ENDIREH, etc.) no calculan decil y deben seguir sin verse
afectados.

`dashboardTema()` (`tablero.js`) gana un tercer parámetro opcional
`datosDecil`, que se concatena con `datos` igual que ya hace
`datosTipoDisc` — solo lo pasan las 3 páginas de esta ronda.

## 5. Filtro nuevo en `filtros.js`

Selector "Decil de ingreso": `Todos` (agregado, default) / `Comparar
deciles` (activa el eje X en modo decil). Mismo patrón visual que el
selector de dominio de dificultad, pero SIN el gatillo de comparación —
aplica a las 4 comparaciones por igual, se muestra siempre que haya más
de un decil real en los datos filtrados (es decir, en las 3 páginas que
lo activan).

### Exclusión mutua con año y edad

Activar "Comparar deciles" fuerza:
- Año → al valor concreto más reciente disponible (si estaba en "Comparar
  años", se colapsa a un año fijo).
- Rango de edad → a "Todas las edades juntas" (si estaba en "Por rango de
  edad", se colapsa a agregado).

Mismo criterio que ya rige el resto del sitio: nunca dos dimensiones
densas desplegadas a la vez (edad×año ya se resuelve hoy con un heatmap
en vez de bloquearse mutuamente — pero decil, al ser 10 valores, no cabe
en esa misma solución de heatmap sin quedar denso; se opta por exclusión
simple, no por una tercera forma de gráfica).

Si el usuario reactiva "Comparar años" o "Por rango de edad" mientras
decil está activo, decil vuelve a `"Todos"` — mismo patrón defensivo que
ya usa `tipoDiscapacidad` en `panelFiltros()` (se fuerza a un valor
neutro cuando la condición que lo justificaba deja de cumplirse, para que
cambiar de opción y volver no deje un filtro fantasma).

## 6. Forma de la gráfica

Cuando "Comparar deciles" está activo, el decil sustituye el EJE X (no es
una faceta adicional): `geometria()` devuelve `dimX: "decil"` en vez de
`null`, y por la exclusión mutua de la sección 5, en ese mismo estado
`facetaCol` (año) y `facetaFila` (edad) están garantizados en `null` — el
resultado es siempre UN panel con el decil en el eje X, nunca una rejilla
decil×año o decil×edad. Las series de la comparación activa (ej. "Mujeres
con discapacidad" vs "Hombres con discapacidad") se codifican por COLOR
dentro de cada grupo de decil — mismo patrón visual que ya usa
`barrasComparadas({dim: "rango_edad", ...})` cuando se agrupa por edad,
simplemente con `dim: "decil"` en su lugar.

**Orden del eje X**: numérico fijo 1→10 (decil 1 = más pobre, a la
izquierda). Es una escala ordinal con significado propio, igual que
`ORDEN_EDAD` — no se reordena por valor de la barra (esa regla de "ordenar
por valor" aplica a rampas de COLOR por año, no a un eje X con orden
intrínseco).

## 7. Páginas afectadas

- **Trabajo** (`enigh/trabajo.md`): filtro de decil aplicado a
  "Participación en el trabajo remunerado" (principal) y a los 2
  secundarios de ingreso ("Ingreso laboral mensual promedio", "Ingreso por
  hora trabajada") — estos últimos son justo donde el decil importa más
  (¿la brecha salarial es igual en decil 1 que en decil 10?).
- **Apoyos** (`enigh/apoyos.md`): filtro aplicado a "Recibe la beca de
  discapacidad" (principal) y a los indicadores de gasto (¿los hogares
  pobres gastan proporcionalmente lo mismo en discapacidad que los ricos?).
- **Educación** (`enigh/educacion-enigh.md`): filtro aplicado a
  "Educación media superior o más" (principal) y a "Sin ningún grado de
  escolaridad"/"No sabe leer ni escribir"/"Asiste a la escuela" (la
  escolaridad correlaciona fuertemente con decil, es la pregunta más
  directa de "¿la desigualdad de género/discapacidad en educación es
  distinta según el nivel socioeconómico del hogar?").

**Tecnología y Hogar (jefatura) quedan fuera de esta ronda** — confirmado
con el usuario: Tecnología es candidato claro para una ronda futura
(brecha digital por decil), Hogar/jefatura va junto con
aportación-al-hogar en su propia ronda separada.

## Fuera de alcance de esta ronda (pendiente, rondas futuras)

- Decil en Tecnología y en Jefatura del hogar.
- Aportación de la persona con discapacidad al ingreso del hogar (métrica
  derivada nueva: ingreso individual / `ing_cor` del hogar).
- Jefatura del hogar cruzada con discapacidad de la propia persona jefa
  (distinto del indicador ya existente "Es jefa o jefe del hogar", que no
  filtra por si el jefe mismo tiene discapacidad).
- Hogar-vs-persona (etiqueta visual en cada página/gráfica de ENIGH).
- Gasto en transporte (taxi/Uber).
- ENDIREH quién-violenta.
- Dominio de dificultad en el resto de páginas (ENADIS, ENDIREH).
- Márgenes de error — el usuario pidió explícitamente NO implementarlo
  todavía.

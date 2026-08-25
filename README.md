# Discriminación y género

Tablero de Observable Framework sobre la situación de las mujeres en México,
con corte transversal de discapacidad. Construido con cuatro encuestas del
INEGI: ENADIS, ENIGH, Censo 2020 (cuestionario ampliado) y ENDIREH.

Social Data Ibero · Universidad Iberoamericana.

## Correr el sitio

```bash
npm install
npm run dev      # servidor local en http://127.0.0.1:3000
npm run build    # sitio estático en dist/
```

El sitio lee un solo archivo de datos ya calculado, `src/data/indicadores.csv`,
así que `npm run dev` funciona sin tener los microdatos en disco.

## Las tres comparaciones

Todo el tablero gira sobre tres pares fijos, definidos en
`src/components/comparacion.js`:

1. Mujeres frente a hombres
2. Mujeres con frente a mujeres sin discapacidad
3. Mujeres frente a hombres con discapacidad

No todas las fuentes sostienen las tres. ENDIREH entrevista solo a mujeres de
15 años o más, así que únicamente admite la segunda; el objeto `FUENTES`
declara qué puede cada encuesta y la interfaz oculta lo que no aplica en vez de
dibujar gráficas vacías.

## Reconstruir los datos

Los microdatos son públicos pero pesan varios gigabytes y **no se versionan**.
Para regenerar `src/data/indicadores.csv` hay que tenerlos en disco y correr
los data loaders de `src/data/dataloader/`.

| Fuente | Ruta esperada | Variable de entorno |
|---|---|---|
| ENADIS 2017 y 2022 | `…/AnalisisSueltos/Enadis/Enadis{año}/Bases/` | `ENADIS_DIR` |
| ENIGH 2020-2024 | `…/AnalisisSueltos/Obindi/enigh/Bases{año}/` | `ENIGH_DIR` |
| Censo 2020 ampliado | `…/JCF/data/raw/censo2020/Personas00.CSV` | `CENSO_PERSONAS` |
| ENDIREH 2021 | `src/data/raw/endireh/2021/` | `ENDIREH_DIR` |

Descarga de ENDIREH (la única que este proyecto trajo desde cero):

```bash
curl -L -o endireh_2021.zip \
  https://www.inegi.org.mx/contenidos/programas/endireh/2021/datosabiertos/conjunto_de_datos_endireh_2021_csv.zip
```

Generación:

```bash
python src/data/dataloader/enadis.csv.py  > /tmp/enadis.csv
python src/data/dataloader/enigh.csv.py   > /tmp/enigh.csv
python src/data/dataloader/censo.csv.py   > /tmp/censo.csv   # ~3.3 GB, usa DuckDB
python src/data/dataloader/endireh.csv.py > /tmp/endireh.csv
```

Cada salida lleva una columna `encuesta`; el archivo final es la concatenación
de las cuatro. Todos los loaders emiten el mismo esquema largo:

```
tema, indicador, anio, sexo, disc, entidad, rango_edad,
num, den, casos, fuente, universo
```

`num` y `den` van expandidos por el factor de la encuesta; `casos` es el
número de registros **sin expandir**, que es con lo que se juzga si la cifra
aguanta. El porcentaje se calcula en el navegador, después de agregar, para no
promediar tasas nunca.

## Trampas de estos microdatos

Están documentadas en el encabezado de cada loader. Las que costaron trabajo
descubrir:

- **La escala de discapacidad cambia entre ediciones, y en la ENIGH 2024 está
  invertida.** En 2020 y 2022 el código 1 es "no puede hacerlo"; en 2024 es "sin
  dificultad". Aplicar el criterio viejo a 2024 da 115 mil personas con
  discapacidad contra 294 sin ella, e invierte el signo de todos los
  indicadores. Los loaders declaran la orientación año por año y abortan si la
  prevalencia resultante cae fuera de un rango plausible.
- **ENADIS renumeró el cuestionario entre 2017 y 2022**, y hay columnas que
  existen en ambas ediciones con significados distintos: `p3_18` es alfabetismo
  en 2022 y parte del bloque laboral en 2017. Por eso los indicadores se piden
  por concepto (`col(year, "alfabetismo")`) y nunca por nombre de columna.
- **ENADIS 2017 usa escala binaria y 2022 de severidad.** El criterio de
  positividad no es intercambiable.
- **El Censo codifica el sexo como 1/3**, no 1/2.
- **ENADIS es representativa solo a nivel nacional.** Hay entre 53 y 147 casos
  por entidad, así que las cifras estatales pasan cualquier umbral de
  suficiencia y aun así no son válidas. La desagregación está bloqueada en
  `FUENTES`, no solo desaconsejada.
- **La ENIGH 2020 no trae el factor de expansión en la tabla de población**: hay
  que heredarlo de `concentradohogar`.

## Composición por edad

La discapacidad se concentra en las edades mayores, y eso produce paradojas de
Simpson en cualquier indicador que también dependa de la edad.

El caso vivo está en violencia sexual (ENDIREH 2021). En el agregado parece
menor entre mujeres con discapacidad (19.0% contra 22.8%); al abrir por rango de
edad se invierte en todos los grupos menores de 60 años:

| Edad | Con discapacidad | Sin discapacidad |
|---|---|---|
| 18-29 | 61.6% | 39.1% |
| 30-44 | 34.6% | 24.0% |
| 45-59 | 19.0% | 13.2% |
| 60+ | 5.3% | 5.6% |

Por eso la página de violencia abre desglosada por edad y el filtro de rango de
edad está presente en todas las páginas.

## Muestra insuficiente

Las celdas con menos de 30 casos sin expandir se dibujan con textura de rayas y
un asterisco, y la gráfica muestra un aviso con cuántas barras están afectadas.
Se dibujan en vez de ocultarse porque un hueco en una gráfica de barras se lee
como un cero.

Con los datos actuales, ninguna combinación alcanzable desde la interfaz (1,302
celdas evaluadas) cae por debajo del umbral: las 94 celdas frágiles que existen
en los datos están todas en ENADIS por entidad, que es justamente lo que la
interfaz no ofrece.

## Estructura

```
src/
├── components/
│   ├── comparacion.js   # los 3 pares, la paleta y qué puede cada fuente
│   ├── agregar.js       # agregación ponderada y regla de fragilidad
│   ├── graficas.js      # librería de Plot, avisos, KPIs, tablas de respaldo
│   ├── filtros.js       # panel de filtros y preparación de series
│   └── tablero.js       # renderer de las páginas temáticas + catálogo de texto
├── data/
│   ├── indicadores.csv  # datos ya calculados que consume el sitio
│   └── dataloader/      # scripts de reconstrucción desde microdatos
├── temas/               # páginas-cascarón (3 líneas cada una)
├── metodologia/
└── index.md
```

## Paleta

Los cuatro grupos son dos binarios cruzados (sexo × discapacidad), no cuatro
categorías independientes, y se codifican como dos tonos por dos intensidades:
naranja para mujeres, azul para hombres, y la discapacidad como intensidad más
textura. Cuatro tonos distintos **no pasan** el validador de daltonismo en modo
oscuro (rojo, naranja y verde colisionan para deuteranopía, ΔE 4.5); dos tonos
pasan con holgura en ambos modos (ΔE 24.7 y 29.6).

La condición de discapacidad nunca se codifica solo con color: va también en la
textura de rayas y en la etiqueta de la serie.

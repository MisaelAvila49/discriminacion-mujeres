# Definiciones

<span class="kicker">01 · Condición de discapacidad</span>

Se considera que una persona tiene discapacidad cuando declara **no poder
hacer** o tener **mucha dificultad** para al menos una de ocho actividades:
ver, oír, caminar o subir escaleras, recordar o concentrarse, bañarse o
vestirse, hablar o comunicarse, mover brazos o manos, y realizar actividades
diarias por una condición mental.

Es el criterio del INEGI y deja fuera, a propósito, a quienes reportan **poca
dificultad**. Esa categoría intermedia ("limitación" en el vocabulario del
censo) se reporta por separado justamente porque incluirla desplaza la
prevalencia varios puntos y cambia el universo del que habla el tablero.

La escala con la que se pregunta esto **no es la misma en todas las encuestas
ni en todas las ediciones**, y es la fuente de error más peligrosa de este
proyecto porque no se detecta a simple vista:

| Fuente | Escala | Cuenta como discapacidad |
|---|---|---|
| ENADIS 2017 | binaria: 1 sí, 2 no | 1 |
| ENADIS 2022 | severidad: 1 no puede … 4 sin dificultad | 1 y 2 |
| ENIGH 2020 y 2022 | severidad: 1 no puede … 4 sin dificultad | 1 y 2 |
| ENIGH 2024 | severidad **invertida**: 1 sin dificultad … 4 no puede | 3 y 4 |
| Censo 2020 | 1 sin dificultad, 2 limitación, 3 mucha dificultad, 4 no puede | 3 y 4 |
| ENDIREH 2021 | severidad: 1 no puede … 4 sin dificultad | 1 y 2 |

El caso de la ENIGH 2024 merece atención: el INEGI invirtió la orientación de
la escala respecto de 2020 y 2022. Aplicarle el criterio de las ediciones
anteriores clasifica como personas con discapacidad a quienes no declararon
ninguna dificultad, y produce un resultado absurdo (más de cien mil personas
con discapacidad frente a unos cientos sin ella) que además invierte el signo
de todos los indicadores. Los data loaders declaran la orientación año por año
y verifican que la prevalencia resultante caiga en un rango plausible antes de
emitir nada.

<span class="kicker">02 · Los cuatro grupos y las tres comparaciones</span>

Cada persona se clasifica por dos atributos: sexo y condición de discapacidad.
De ahí salen cuatro grupos, y las tres comparaciones del tablero son
subconjuntos de esos cuatro.

**Mujeres frente a hombres** agrega a las personas con y sin discapacidad
dentro de cada sexo. Mide la brecha de género en la población total.

**Mujeres con frente a mujeres sin discapacidad** deja fuera a los hombres.
Mide cuánto pesa la discapacidad entre mujeres.

**Mujeres frente a hombres con discapacidad** deja fuera a quienes no tienen
discapacidad. Mide cuánto pesa el género dentro de la población con
discapacidad.

<span class="kicker">03 · Cómo se calculan las cifras</span>

Todas las estimaciones se expanden con el factor de la encuesta
correspondiente, que convierte la muestra en población.

**Cada grupo se mide contra su propia población, no contra el total.** Cuando
el tablero dice que trabajó el 82.9% de los hombres sin discapacidad, el
denominador son los 39.9 millones de hombres sin discapacidad, no la población
adulta del país. Los cuatro grupos tienen cuatro denominadores distintos:

| Grupo (ENIGH 2024) | Población | Trabajó |
|---|---|---|
| Hombres sin discapacidad | 39.9 millones | 82.9% |
| Mujeres sin discapacidad | 45.6 millones | 54.9% |
| Hombres con discapacidad | 3.9 millones | 46.6% |
| Mujeres con discapacidad | 4.7 millones | 29.9% |

Por eso **los porcentajes de las barras no suman 100%**: en el ejemplo suman
214.3%, y así debe ser. No son partes de un total repartido, sino cuatro tasas
independientes. Si todas se calcularan contra la población nacional, los grupos
chicos aparecerían siempre cerca de cero y la comparación no diría nada: la
pregunta del tablero es qué proporción de *cada* grupo está en cada situación,
no qué tanto pesa cada grupo en el país.

Los porcentajes **nunca se promedian**. Al agregar varias entidades o varios
rangos de edad se suman el numerador y el denominador de cada grupo y se divide
al final. Promediar las tasas de grupos de distinto tamaño produce un número que
no corresponde a ninguna población real.

Cuando una pregunta admite "no especificado", esa respuesta **sale del
denominador** en lugar de contarse como un "no". Contar los no especificados
como respuestas negativas inventa certeza que nadie declaró.

El **ingreso laboral** se calcula solo entre quienes perciben ingreso por
trabajo, y es el único indicador del tablero que se expresa en pesos y no en
por ciento. Incluir a la población sin ocupación mezclaría la brecha de
participación con la brecha salarial, que son dos problemas distintos y de
magnitudes distintas.

<span class="kicker">04 · Muestra insuficiente</span>

La suficiencia de una cifra se juzga con el número de **casos sin expandir**, no
con la población que representa. Una estimación expandida a cuarenta mil
personas que proviene de ocho entrevistas sigue siendo ocho entrevistas.

Las celdas calculadas con menos de **30 casos** se dibujan con textura de rayas
y llevan un asterisco junto a su valor, y la gráfica muestra un aviso con el
número de barras afectadas y el mínimo de casos. Se dibujan en vez de ocultarse
porque un hueco en una gráfica de barras se lee como un cero, que es una
afirmación más fuerte y más falsa que una cifra imprecisa.

<span class="kicker">05 · Composición por edad</span>

La discapacidad se concentra en las edades mayores. Cualquier indicador que
también dependa de la edad, y la violencia sexual depende mucho, produce
agregados engañosos si no se controla por ella.

El caso vivo está en la página de violencia: en el agregado, la violencia sexual
aparece más baja entre las mujeres con discapacidad, y al abrir por rango de
edad la relación se invierte en todos los grupos menores de sesenta años. Es una
paradoja de Simpson, y por eso esa página abre desglosada por edad de forma
predeterminada.

Como regla de lectura: **si una comparación mezcla edades, la composición por
edad puede estar produciendo el resultado**. El filtro de rango de edad está en
todas las páginas para poder descartarlo.

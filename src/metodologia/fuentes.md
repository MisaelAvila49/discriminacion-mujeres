# Fuentes y cobertura

Este tablero se construye con cuatro encuestas del INEGI. Ninguna responde sola
la pregunta central, y cada una tiene un límite que conviene conocer antes de
leer una cifra.

<span class="kicker">01 · Qué aporta cada encuesta</span>

**ENADIS, Encuesta Nacional sobre Discriminación (2017 y 2022).** Es la única
encuesta del país diseñada específicamente para medir discriminación, y la
única que pregunta por experiencias de rechazo y negación de derechos. Su
tabla sociodemográfica identifica sexo, edad, entidad y las ocho preguntas de
dificultad que definen la condición de discapacidad, de modo que sostiene las
tres comparaciones del tablero.

Su límite es de diseño muestral: **ENADIS es representativa solo a nivel
nacional**. Al abrir por entidad quedan entre 53 y 147 casos por estado en el
cruce de mujeres con discapacidad, cifras que superan cualquier umbral de
suficiencia y que aun así no autorizan una estimación estatal, porque el
muestreo no se construyó para eso. El tablero bloquea esa desagregación en
lugar de ofrecerla con una nota al pie: es la clase de cifra que se ve sólida
y no lo es.

**ENIGH, Encuesta Nacional de Ingresos y Gastos de los Hogares (2020, 2022 y
2024).** Aporta el ingreso laboral y la participación en el trabajo remunerado,
con representatividad estatal y una serie de tres puntos.

Las ediciones 2016 y 2018 están descargadas pero fuera del tablero: no incluyen
tabla de población, y sin ella no hay forma de cruzar sexo con discapacidad a
nivel persona. Incluirlas produciría una serie que cambia de universo a la
mitad.

**Censo de Población y Vivienda 2020, cuestionario ampliado.** Es la muestra
ampliada del censo, con cerca de quince millones de registros de persona. Es la
**única fuente del tablero con representatividad municipal**, y por eso sostiene
el ranking territorial. Su tamaño también la vuelve el mejor contraste para las
demás: su prevalencia de discapacidad en población adulta (6.1%) coincide con
la de ENADIS (6.1% en 2017 y 6.4% en 2022), calculada con un instrumento
distinto y una muestra mil veces más chica.

**ENDIREH, Encuesta Nacional sobre la Dinámica de las Relaciones en los Hogares
(2021).** Es la fuente más sólida que existe sobre violencia contra las
mujeres, con representatividad estatal, y usa la clasificación de violencia del
propio INEGI en vez de una construida para este tablero.

Tiene dos restricciones que definen cómo puede usarse. La primera es que
**entrevista únicamente a mujeres de 15 años o más**: no existe el hombre como
término de comparación, así que de las tres comparaciones del tablero solo
sostiene una, la de mujeres con y sin discapacidad. Las otras dos se ocultan en
sus páginas. La segunda es que el módulo de discapacidad se levantó por primera
vez en 2021: la edición 2016 está descargada y sirve para la serie de violencia
total, pero no admite el corte por discapacidad, y mezclar un año con corte y
otro sin él en la misma gráfica sería un error de lectura.

**ENDUTIH, Encuesta Nacional sobre Disponibilidad y Uso de Tecnologías de la
Información en los Hogares.** Se descargó y se descartó, y vale la pena decir
por qué. Es la fuente natural para hablar de brecha digital y tiene muchas
ediciones, pero **no identifica la discapacidad de la persona**: solo la
registra cuando alguien la señala como la razón principal para no usar
internet, computadora o celular. Ese proxy capta al 1.4% de la población,
contra el 9.2% que reporta la ENIGH, porque deja fuera a quien tiene
discapacidad y no usa internet por falta de dinero, y porque solo se pregunta
a quien ya declaró no usar la tecnología.

Con ese instrumento no se pueden hacer las comparaciones del tablero. El tema
de tecnología se construyó con la **ENIGH**, cuya tabla de hogares trae las
variables de conectividad y se une sin pérdida con la de población, que sí
identifica sexo y discapacidad a nivel persona.

<span class="kicker">02 · Qué se puede comparar con qué</span>

| Encuesta | Ediciones | Nivel máximo | M vs H | M con vs sin discapacidad | M vs H con discapacidad |
|---|---|---|---|---|---|
| ENADIS | 2017, 2022 | Nacional | sí | sí | sí |
| ENIGH | 2020, 2022, 2024 | Estatal | sí | sí | sí |
| Censo ampliado | 2020 | Municipal | sí | sí | sí |
| ENDIREH | 2021 | Estatal | no | sí | no |

Las prevalencias de discapacidad **no son comparables entre encuestas**. ENDIREH
reporta 12.6% y las demás alrededor de 6%, y la diferencia no es un error: el
universo de ENDIREH son mujeres de 15 años o más, no la población adulta de
ambos sexos, y la discapacidad es más frecuente entre mujeres y crece con la
edad. Dentro de una misma encuesta, en cambio, las comparaciones entre grupos
son limpias, y son las que sostiene el tablero.

<span class="kicker">03 · De dónde salen los datos</span>

Los microdatos son públicos y se descargan de los sitios del INEGI de cada
programa. El tablero no los versiona: pesan varios gigabytes y se reconstruyen
con los data loaders que están en `src/data/dataloader/`. Cada loader emite la
misma tabla larga (numerador y denominador expandidos, más el número de casos
sin expandir) y documenta en su encabezado los códigos que usa y por qué.

Las rutas de descarga y el procedimiento de reconstrucción están en el README
del proyecto.

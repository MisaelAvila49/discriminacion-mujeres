// src/components/catalogo.js
// El contenido editorial del tablero: qué encuestas hay, qué subtemas tiene
// cada una, qué indicadores muestra cada subtema y con qué palabras se explican.
//
// Está organizado por ENCUESTA, no por tema, porque una cifra solo es
// comparable con otra de la misma fuente: los universos, los años y los
// instrumentos difieren entre encuestas, y mezclarlos en una misma página
// invitaba a leer como serie lo que son mediciones distintas.
//
// Separado de tablero.js para que el texto viva aparte de la lógica de armado.

// Orden de prioridad editorial del proyecto.
export const ENCUESTAS = [
  {
    clave: "censo",
    nombre: "Censo 2020",
    titulo: "Censo de Población y Vivienda, cuestionario ampliado",
    resumen: `Quince millones de registros de persona. Es la única fuente con
      representatividad municipal y, por su tamaño, el mejor contraste para
      verificar las cifras de las encuestas.`,
    // numeralia-censo y educacion-censo se agregan en tasks posteriores de
    // esta misma ronda (docs/superpowers/plans/2026-08-29-filtros-y-censo-plan.md):
    // se declaran aquí antes de que sus páginas .md existan a propósito, para
    // no tener que rehacer un placeholder vacío cuando lleguen.
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
    subtemas: ["autonomia", "agresor"],
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

export const ENCUESTA_POR_CLAVE = Object.fromEntries(
  ENCUESTAS.map((e) => [e.clave, e])
);

// Un objeto por subtema. El campo `explica` alimenta el desplegable
// "¿Qué quiere decir este análisis?" que acompaña a cada gráfica.
export const CATALOGO = {
  // --- ENIGH ---------------------------------------------------------------
  trabajo: {
    encuesta: "enigh",
    titulo: "Trabajo e ingreso",
    kicker: "Trabajo e ingreso",
    entrada: `La participación en el trabajo remunerado es donde la brecha
      entre mujeres y hombres es más ancha y más estable en el tiempo. Al
      cruzarla con discapacidad, las dos desventajas no se suman: se
      multiplican.`,
    fuentePrincipal: "enigh",
    indicadorPrincipal: "Participación en el trabajo remunerado",
    formato: "pct",
    explica: `Porcentaje de personas que declararon haber trabajado al menos
      una hora en el mes anterior a la entrevista. Se calcula sobre cada grupo
      por separado: el dato de las mujeres con discapacidad es la proporción
      dentro de ese grupo, no su peso en la población total.`,
    secundarios: [
      {encuesta: "enigh", indicador: "Ingreso laboral mensual promedio", formato: "pesos",
       nota: `Solo entre quienes perciben ingreso por trabajo: incluir a la
         población sin ocupación mezclaría la brecha de participación con la
         salarial.`,
       explica: `Promedio de pesos al mes que recibe cada persona por su
         trabajo, entre quienes sí perciben un ingreso laboral. No incluye
         pensiones, apoyos ni ingresos de otros integrantes del hogar.
         Expresado en pesos constantes de 2024: cada edición viene en pesos
         de su propio año y se deflactó con el INPC del periodo de
         levantamiento, de modo que los montos sí se pueden comparar entre
         años. Sin ese ajuste el ingreso "crecía" 56% de 2020 a 2024, casi
         todo inflación.`},
      {encuesta: "enigh", indicador: "Horas de trabajo remunerado a la semana", formato: "horas",
       nota: `La jornada explica buena parte de la brecha anterior: las mujeres
         sin discapacidad trabajan nueve horas menos a la semana que los
         hombres sin discapacidad.`,
       explica: `Promedio de horas semanales dedicadas al trabajo remunerado,
         entre quienes declararon alguna. No cuenta el trabajo doméstico ni de
         cuidados, que no se remunera.`},
      {encuesta: "enigh", indicador: "Ingreso por hora trabajada", formato: "pesos",
       nota: `Al descontar las horas, la brecha de género casi desaparece
         (100.9 contra 104.0 pesos por hora en 2024) y la de discapacidad se
         mantiene: la desigualdad mensual viene del tiempo disponible para el
         trabajo remunerado, no del pago por hora.`,
       explica: `El ingreso mensual dividido entre las horas efectivamente
         trabajadas. Sirve para separar dos cosas que el ingreso mensual
         mezcla: cuánto se paga por el trabajo y cuánto tiempo se puede
         dedicar a él. En pesos constantes de 2024, igual que el ingreso
         mensual.`},
    ],
  },
  tecnologia: {
    encuesta: "enigh",
    titulo: "Tecnología y conectividad",
    kicker: "Tecnología y conectividad",
    entrada: `El acceso a internet condiciona a las demás desigualdades: sin
      conexión no hay trámite en línea, ni empleo remoto, ni escuela a
      distancia. Aquí la brecha por discapacidad es casi nueve veces más ancha
      que la de género.`,
    fuentePrincipal: "enigh",
    indicadorPrincipal: "Hogar con conexión a internet",
    formato: "pct",
    explica: `Porcentaje de personas que viven en un hogar con conexión a
      internet. Mide el acceso en la vivienda, no el uso personal: alguien con
      conexión en casa puede no usarla, y alguien sin conexión puede usar
      internet en otro lado.`,
    secundarios: [
      {encuesta: "enigh", indicador: "Hogar con teléfono celular", formato: "pct",
       nota: `El celular está mucho más extendido que la conexión fija, así que
         la brecha se estrecha: es la tecnología que primero llega.`,
       explica: `Porcentaje de personas que viven en un hogar donde al menos
         un integrante tiene teléfono celular.`},
      {encuesta: "enigh", indicador: "Hogar con computadora", formato: "pct",
       explica: `Porcentaje de personas que viven en un hogar con al menos
         una computadora (num_compu > 0). Es más exigente que el internet o
         el celular: una computadora es un gasto fijo, no un servicio que se
         paga mes a mes.`},
      {encuesta: "enigh", indicador: "Hogar con línea telefónica fija", formato: "pct",
       explica: `Porcentaje de personas que viven en un hogar con línea
         telefónica fija contratada. Es la tecnología en declive: el celular
         la ha ido sustituyendo en todos los grupos.`},
      {encuesta: "enigh", indicador: "Hogar con televisión de paga", formato: "pct",
       explica: `Porcentaje de personas que viven en un hogar con servicio de
         televisión de paga contratado.`},
    ],
  },

  "educacion-enigh": {
    encuesta: "enigh",
    titulo: "Educación",
    kicker: "Educación",
    entrada: `La ENIGH mide escolaridad en tres ediciones y con
      representatividad estatal, así que permite seguir el rezago en el tiempo.
      La brecha por discapacidad duplica a la de género: entre las personas con
      discapacidad, solo una de cada cuatro terminó la preparatoria.`,
    fuentePrincipal: "enigh",
    indicadorPrincipal: "Educación media superior o más",
    formato: "pct",
    explica: `Porcentaje de personas cuyo último nivel aprobado es preparatoria
      o superior (incluye normal, carrera técnica, profesional, maestría y
      doctorado). Quienes no declararon su nivel salen del denominador en vez
      de contarse como si no tuvieran estudios.`,
    secundarios: [
      {encuesta: "enigh", indicador: "Sin ningún grado de escolaridad", formato: "pct",
       nota: `El extremo opuesto del indicador principal, y donde la brecha por
         discapacidad es más brutal: 16.2% contra 3.8% entre mujeres.`,
       explica: `Porcentaje de personas que declararon no haber aprobado ningún
         grado escolar.`},
      {encuesta: "enigh", indicador: "No sabe leer ni escribir (ENIGH)", formato: "pct",
       explica: `Porcentaje de personas que declararon no saber leer ni
         escribir. Es la misma pregunta que hace la ENADIS, así que las dos
         cifras se pueden contrastar.`},
      {encuesta: "enigh", indicador: "Asiste a la escuela (18 a 29 años, ENIGH)", formato: "pct",
       explica: `Porcentaje de personas de 18 a 29 años inscritas y asistiendo
         a la escuela.`},
    ],
  },
  hogar: {
    encuesta: "enigh",
    titulo: "Jefatura del hogar",
    kicker: "Jefatura del hogar",
    entrada: `Quién encabeza el hogar es una posición, no una carencia: una
      jefatura femenina alta no es en sí misma buena ni mala señal. Lo que sí
      llama la atención es que entre las mujeres con discapacidad la jefatura
      casi duplica a la de las mujeres sin discapacidad.`,
    fuentePrincipal: "enigh",
    indicadorPrincipal: "Es jefa o jefe del hogar",
    formato: "pct",
    explica: `Porcentaje de personas que la propia encuesta registra como jefa
      o jefe de su hogar. Hay exactamente una jefatura por hogar, y el
      denominador es la población adulta, no los hogares: la cifra se lee como
      qué proporción de cada grupo encabeza un hogar. A diferencia del resto
      del tablero, este indicador no mide una desventaja; en México una
      jefatura femenina suele reflejar hogares sin cónyuge varón.`,
    secundarios: [],
  },
  apoyos: {
    encuesta: "enigh",
    titulo: "Apoyos y transferencias",
    kicker: "Apoyos",
    entrada: `Qué tanto llega el apoyo público a los hogares con discapacidad.
      Aquí solo entra el dinero que ENTRA al hogar; lo que sale de su bolsillo
      —aparatos, cuidados, educación especial, transporte— vive en la sección
      de Gastos.`,
    fuentePrincipal: "enigh",
    indicadorPrincipal: "Recibe la beca de discapacidad",
    formato: "pct",
    explica: `Porcentaje de personas que viven en un hogar donde alguien recibe
      la pensión federal para personas con discapacidad. Es un dato de HOGAR
      heredado a la persona: la encuesta registra el ingreso por hogar, no por
      individuo, así que la cifra no dice que cada persona reciba la beca sino
      que su hogar la recibe.`,
    secundarios: [
      {encuesta: "enigh", indicador: "Recibe la pensión de adultos mayores", formato: "pct",
       nota: `Sirve de contraste: es el programa social de mayor cobertura del
         país, y muestra cómo se ve un apoyo verdaderamente masivo frente a la
         beca de discapacidad.`,
       explica: `Porcentaje de personas que viven en un hogar donde alguien
         recibe la pensión para adultos mayores.`},
    ],
  },

  gastos: {
    encuesta: "enigh",
    titulo: "Gastos por discapacidad",
    kicker: "Gastos",
    entrada: `El sobrecosto de vivir con discapacidad: aparatos, cuidados,
      educación especial y transporte que otros hogares simplemente no pagan.
      Ningún indicador de ingreso captura este gasto, y por eso dos hogares
      con el mismo ingreso no tienen el mismo margen real.`,
    fuentePrincipal: "enigh",
    indicadorPrincipal: "Su hogar gasta en aparatos o cuidados por discapacidad",
    formato: "pct",
    explica: `Porcentaje de personas que viven en un hogar que registró gasto
      en aparatos ortopédicos, sillas de ruedas, andaderas, prótesis, su
      reparación, cuidado de enfermos o educación especial. Es un dato de
      HOGAR heredado a la persona. Solo hay tabla de gastos para 2022 y 2024.`,
    secundarios: [
      {encuesta: "enigh", indicador: "Gasto trimestral en aparatos o cuidados por discapacidad", formato: "pesos",
       nota: `El promedio se calcula solo entre quienes gastan algo: "cuánto
         gasta el que gasta", no diluido con los hogares en cero.`,
       explica: `Promedio de pesos gastados en el trimestre, entre las
         personas cuyo hogar registró algún gasto asociado a discapacidad.
         No incluye a quienes viven en un hogar sin ese gasto. En pesos
         constantes de 2024: la ENIGH estandariza el gasto a precios de
         agosto de su propia edición, lo que lo deja comparable dentro de un
         año pero no entre años.`},
      {encuesta: "enigh", indicador: "Gasto en: Lentes y apoyos visuales", formato: "pct",
       explica: `Porcentaje de personas que viven en un hogar que gastó en
         anteojos, lentes de contacto o intraoculares u otros apoyos
         visuales.`},
      {encuesta: "enigh", indicador: "Gasto en: Aparatos para sordera", formato: "pct",
       explica: `Porcentaje de personas que viven en un hogar que gastó en
         aparatos auditivos.`},
      {encuesta: "enigh", indicador: "Gasto en: Sillas de ruedas, andaderas y movilidad", formato: "pct",
       explica: `Porcentaje de personas que viven en un hogar que gastó en
         silla de ruedas, andadera, calzado terapéutico u otro apoyo de
         movilidad.`},
      {encuesta: "enigh", indicador: "Gasto en: Prótesis, ortesis y otros dispositivos de apoyo", formato: "pct",
       explica: `Porcentaje de personas que viven en un hogar que gastó en
         prótesis, ortesis u otro dispositivo médico de soporte. Desglose
         exclusivo de 2022 y 2024: el INEGI amplió el catálogo de gasto ese
         año.`},
      {encuesta: "enigh", indicador: "Gasto en: Reparación y renta de aparatos", formato: "pct",
       explica: `Porcentaje de personas que viven en un hogar que gastó en
         reparar o rentar aparatos ortopédicos o médicos.`},
      {encuesta: "enigh", indicador: "Gasto en: Cuidado de enfermos y terapias", formato: "pct",
       explica: `Porcentaje de personas que viven en un hogar que gastó en
         cuidado de enfermos, terapeutas u otro servicio similar
         (incluye glucómetro y equipo de monitoreo).`},
      {encuesta: "enigh", indicador: "Gasto en: Educación especial", formato: "pct",
       explica: `Porcentaje de personas que viven en un hogar que gastó en
         educación especial para discapacidad, en cualquier nivel escolar.`},
      {encuesta: "enigh", indicador: "Gasto en: Residencias y protección social", formato: "pct",
       explica: `Porcentaje de personas que viven en un hogar que gastó en
         residencias no médicas u otros servicios de protección social para
         personas con discapacidad. Desglose exclusivo de 2024.`},

      {encuesta: "enigh", indicador: "Su hogar gasta en taxi o aplicación de viaje", formato: "pct",
       nota: `Cuando el transporte público no es accesible, el taxi deja de
         ser una alternativa cara y se vuelve el único medio utilizable: los
         hogares con discapacidad gastan en él 1.7 veces más que los demás.`,
       explica: `Porcentaje de personas que viven en un hogar que registró
         gasto en taxi de sitio o en aplicaciones de viaje (Uber, DiDi). Es un
         dato de HOGAR heredado a la persona. La ENIGH capta la mayor parte de
         este gasto como NO monetario: buena parte de esos viajes los paga
         otra persona, el trabajo o un programa, y aquí se cuentan igual
         porque son parte del costo de moverse.`},
      {encuesta: "enigh", indicador: "Su hogar gasta en transporte público", formato: "pct",
       nota: `Es el contraste que da sentido al gasto en taxi: si un grupo
         gasta más en taxi y no menos en transporte público, no está
         sustituyendo un medio por otro sino pagando ambos.`,
       explica: `Porcentaje de personas cuyo hogar gastó en metro, tren
         ligero, autobús urbano, trolebús, metrobús, colectivo, combi o
         microbús. No incluye autobús foráneo ni transporte entre ciudades:
         la comparación es sobre el traslado cotidiano.`},
      {encuesta: "enigh", indicador: "Gasto trimestral en taxi o aplicación de viaje", formato: "pesos",
       nota: `El promedio se calcula solo entre quienes gastan algo: "cuánto
         gasta el que gasta", no diluido con los hogares en cero.`,
       explica: `Promedio de pesos gastados en el trimestre en taxi o
         aplicaciones, entre las personas cuyo hogar registró ese gasto. En
         pesos constantes: la ENIGH estandariza el gasto a precios de agosto
         de su propia edición, así que sin deflactar los años no serían
         comparables.`},
      {encuesta: "enigh", indicador: "Gasto trimestral en transporte público", formato: "pesos",
       explica: `Promedio de pesos gastados en el trimestre en transporte
         público, entre las personas cuyo hogar registró ese gasto. En pesos
         constantes, igual que el anterior.`},
      {encuesta: "enigh", indicador: "Su hogar gasta en aplicación de viaje (Uber, DiDi)", formato: "pct",
       nota: `Solo 2024: el INEGI separó las aplicaciones del taxi de sitio
         apenas ese año. No hay serie hacia atrás porque la encuesta no lo
         preguntaba por separado, no porque nadie las usara.`,
       explica: `Porcentaje de personas cuyo hogar gastó en renta de vehículo
         con chofer (Uber, DiDi y similares). Antes de 2024 este gasto se
         capturaba dentro de "taxi", así que el indicador que une ambos es el
         que sí se puede seguir en el tiempo.`},
    ],
  },

  // --- ENDIREH -------------------------------------------------------------
  autonomia: {
    encuesta: "endireh",
    titulo: "Tipos de violencia",
    kicker: "Tipos de violencia",
    entrada: `ENDIREH entrevista únicamente a mujeres de 15 años o más, así que
      esta sección compara mujeres con y sin discapacidad; no hay hombres como
      término de comparación. El desglose por edad no es opcional aquí: sin él,
      las cifras se invierten.`,
    fuentePrincipal: "endireh",
    indicadorPrincipal: "Violencia total en los últimos 12 meses",
    formato: "pct",
    abrePorEdad: true,
    explica: `Porcentaje de mujeres que declararon haber vivido al menos un
      incidente de violencia (psicológica, física, sexual o económica) en los
      doce meses previos a la entrevista, en cualquier ámbito: pareja,
      familia, escuela, trabajo o espacios públicos. La clasificación es la
      del propio INEGI, no una construida para este tablero.`,
    secundarios: [
      {encuesta: "endireh", indicador: "Violencia psicológica en los últimos 12 meses", formato: "pct",
       explica: `Incluye humillaciones, amenazas, control de las actividades,
         vigilancia y aislamiento. Es el tipo más frecuente de todos.`},
      {encuesta: "endireh", indicador: "Violencia sexual en los últimos 12 meses", formato: "pct",
       nota: `Sin controlar por edad esta cifra se invierte: ver la nota de la
         sección.`,
       explica: `Incluye desde acoso y hostigamiento hasta abuso y violación,
         en cualquier ámbito. En el agregado parece menor entre mujeres con
         discapacidad, pero al comparar dentro de cada rango de edad ocurre lo
         contrario en todos los grupos menores de 60 años.`},
      {encuesta: "endireh", indicador: "Violencia económica o patrimonial en los últimos 12 meses", formato: "pct",
       explica: `Incluye el control o la retención del dinero, la prohibición
         de trabajar o estudiar, y el despojo de bienes o documentos.`},
      {encuesta: "endireh", indicador: "Violencia física en los últimos 12 meses", formato: "pct",
       explica: `Incluye empujones, jalones, golpes y agresiones con objetos o
         armas.`},
    ],
  },


  agresor: {
    encuesta: "endireh",
    titulo: "Quién ejerce la violencia",
    kicker: "Quién violenta",
    entrada: `La misma violencia se lee distinto según quién la ejerce. Para una
      mujer con discapacidad que depende de alguien para bañarse, comer o salir,
      que ese alguien sea el agresor cambia por completo lo que significa
      denunciar o irse. Cada barra tiene su propio denominador: solo entran las
      mujeres expuestas a ese ámbito.`,
    fuentePrincipal: "endireh",
    indicadorPrincipal: "Violencia de la pareja en los últimos 12 meses",
    formato: "pct",
    abrePorEdad: true,
    explica: `Porcentaje de mujeres con pareja actual o pasada que declararon
      violencia de su pareja en los últimos doce meses. El denominador son las
      mujeres que han tenido pareja, no todas: quien nunca ha tenido no puede
      haber vivido este tipo de violencia. En el ámbito de pareja no se
      desglosa quién agrede porque el agresor es, por definición, la pareja.`,
    secundarios: [
      {encuesta: "endireh", indicador: "Violencia comunitaria (calle, transporte) en los últimos 12 meses", formato: "pct",
       nota: `Sin controlar por edad esta cifra se invierte, igual que la
         violencia sexual: en el agregado parece menor entre mujeres con
         discapacidad, pero dentro de cada rango de edad menor de 60 es
         mayor, hasta 21 puntos más entre las de 18 a 29 años.`,
       explica: `Violencia ejercida por personas desconocidas o conocidas sin
         vínculo cercano, en la calle, el transporte público, parques y otros
         espacios públicos. El denominador son todas las mujeres: el espacio
         público no requiere haber "participado" en él. El agregado sin edad
         refleja que la discapacidad se concentra en mayores de 60, que salen
         menos y por eso reportan menos violencia en la calle.`},
      {encuesta: "endireh", indicador: "Violencia en el trabajo en los últimos 12 meses", formato: "pct",
       explica: `Violencia ejercida por jefes, compañeros o clientes. El
         denominador son solo las mujeres que trabajaron en los últimos doce
         meses; quien no trabajó no está expuesta a este ámbito y queda fuera
         del cálculo, no contada como "sin violencia".`},
      {encuesta: "endireh", indicador: "Violencia en la escuela en los últimos 12 meses", formato: "pct",
       explica: `Violencia ejercida por docentes, personal o compañeros. El
         denominador son solo las mujeres que asistieron a la escuela en los
         últimos doce meses, un grupo pequeño entre las mujeres adultas, así
         que el desglose por entidad puede quedar con pocos casos.`},
    ],
    ranking: {
      titulo: "Quién agrede, dentro de cada ámbito",
      etiqueta: "Ámbito",
      limite: 20,
      explica: `Cada barra es el porcentaje de mujeres que declararon violencia
        de esa persona en los últimos doce meses. Están ordenadas por BRECHA:
        arriba queda el agresor cuya violencia es más desproporcionada contra
        las mujeres con discapacidad, que no siempre es el más frecuente. Los
        porcentajes no suman el total del ámbito: una misma mujer agredida por
        su padre y por su hermano aparece en las dos filas.`,
      grupos: [
        {
          clave: "familiar",
          nombre: "Ámbito familiar",
          dimLabel: "Familiar que agrede",
          recorta: "Violencia familiar de ",
          indicadores: [
          "Violencia familiar de su padre en los últimos 12 meses",
          "Violencia familiar de su madre en los últimos 12 meses",
          "Violencia familiar de su padrastro o madrastra en los últimos 12 meses",
          "Violencia familiar de un abuelo o abuela en los últimos 12 meses",
          "Violencia familiar de un hijo o hija en los últimos 12 meses",
          "Violencia familiar de un hermano o hermana en los últimos 12 meses",
          "Violencia familiar de un tío o tía en los últimos 12 meses",
          "Violencia familiar de un primo o prima en los últimos 12 meses",
          "Violencia familiar de un suegro o suegra en los últimos 12 meses",
          "Violencia familiar de un cuñado o cuñada en los últimos 12 meses",
          "Violencia familiar de un sobrino o sobrina en los últimos 12 meses",
          "Violencia familiar de un yerno en los últimos 12 meses",
          "Violencia familiar de otro familiar en los últimos 12 meses",
          ],
        },
        {
          clave: "laboral",
          nombre: "Ámbito laboral",
          dimLabel: "Persona que agrede en el trabajo",
          recorta: "Violencia en el trabajo de ",
          indicadores: [
          "Violencia en el trabajo de su patrón o jefe en los últimos 12 meses",
          "Violencia en el trabajo de un supervisor o capataz en los últimos 12 meses",
          "Violencia en el trabajo de un gerente o directivo en los últimos 12 meses",
          "Violencia en el trabajo de un compañero de trabajo en los últimos 12 meses",
          "Violencia en el trabajo de un cliente en los últimos 12 meses",
          "Violencia en el trabajo de una persona desconocida del trabajo en los últimos 12 meses",
          "Violencia en el trabajo de un familiar del patrón en los últimos 12 meses",
          "Violencia en el trabajo de otra persona del trabajo en los últimos 12 meses",
          ],
        },
        {
          clave: "escolar",
          nombre: "Ámbito escolar",
          dimLabel: "Persona que agrede en la escuela",
          recorta: "Violencia en la escuela de ",
          indicadores: [
          "Violencia en la escuela de un maestro en los últimos 12 meses",
          "Violencia en la escuela de una maestra en los últimos 12 meses",
          "Violencia en la escuela de un compañero en los últimos 12 meses",
          "Violencia en la escuela de una compañera en los últimos 12 meses",
          "Violencia en la escuela de el director o directora en los últimos 12 meses",
          "Violencia en la escuela de un trabajador de la escuela en los últimos 12 meses",
          "Violencia en la escuela de una trabajadora de la escuela en los últimos 12 meses",
          "Violencia en la escuela de una persona desconocida de la escuela en los últimos 12 meses",
          "Violencia en la escuela de otra persona de la escuela en los últimos 12 meses",
          ],
        },
      ],
    },
  },

  // --- Censo ---------------------------------------------------------------
  "numeralia-censo": {
    encuesta: "censo",
    titulo: "Numeralia",
    kicker: "Numeralia",
    entrada: `La misma cifra de la portada, pero con filtros: cuántas personas
      hay en cada grupo, y cómo cambia la prevalencia de discapacidad por
      edad, entidad y dominio de dificultad.`,
    fuentePrincipal: "censo",
    indicadorPrincipal: "Población",
    formato: "conteo",
    explica: `Personas expandidas de cada grupo (sexo, discapacidad, edad,
      entidad). No es un porcentaje: es el conteo absoluto de población,
      la misma cifra que ya usa la portada.`,
    secundarios: [],
  },
  "trabajo-censo": {
    encuesta: "censo",
    titulo: "Trabajo según el Censo",
    kicker: "Trabajo",
    entrada: `El Censo mide lo mismo que la ENIGH con un instrumento distinto y
      una muestra mil veces más grande, así que sirve de verificación. Además
      es la única fuente con desagregación municipal.`,
    fuentePrincipal: "censo",
    indicadorPrincipal: "Población ocupada",
    formato: "pct",
    explica: `Porcentaje de personas que declararon haber trabajado la semana
      anterior al censo. El denominador excluye a quienes no declararon su
      condición de actividad, en vez de contarlos como si no trabajaran.`,
    secundarios: [
      {encuesta: "censo", indicador: "Se dedica a los quehaceres del hogar", formato: "pct",
       nota: `El reverso de la barra anterior: donde baja la ocupación de las
         mujeres, sube el trabajo doméstico no remunerado.`,
       explica: `Porcentaje de personas cuya actividad principal declarada son
         los quehaceres del hogar. Es trabajo no remunerado y, por definición
         del censo, excluyente de la ocupación.`},
    ],
  },
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

  // --- ENADIS --------------------------------------------------------------
  discriminacion: {
    encuesta: "enadis",
    titulo: "Discriminación vivida",
    kicker: "Discriminación vivida",
    entrada: `El resto del tablero mide desigualdades de resultado: quién
      trabaja, quién gana cuánto, quién sabe leer. Esta sección mide algo
      distinto y más directo: a quién le negaron un derecho.`,
    fuentePrincipal: "enadis",
    indicadorPrincipal: "Le negaron injustificadamente algún derecho",
    formato: "pct",
    explica: `Porcentaje de personas que respondieron que sí a la pregunta
      sobre si en los últimos cinco años les negaron injustificadamente al
      menos uno de seis derechos o servicios. El denominador son quienes
      solicitaron el servicio: quien nunca lo pidió no pudo ser discriminado
      al pedirlo, y contarlo diluiría la cifra.`,
    secundarios: [
      {encuesta: "enadis", indicador: "Le negaron atención médica o medicamentos", formato: "pct",
       nota: `La salud es el derecho donde la negación tiene consecuencias más
         inmediatas, y donde la discapacidad pesa más.`,
       explica: `Porcentaje de quienes solicitaron atención médica o
         medicamentos y declararon que se los negaron injustificadamente.`},
      {encuesta: "enadis", indicador: "Le negaron apoyos de programas sociales", formato: "pct",
       explica: `Porcentaje de quienes solicitaron un apoyo de algún programa
         social y declararon que se lo negaron injustificadamente.`},
    ],
  },
  educacion: {
    encuesta: "enadis",
    titulo: "Educación",
    kicker: "Educación",
    entrada: `El analfabetismo es un rezago acumulado: habla de la escuela a la
      que estas mujeres pudieron o no entrar hace décadas, no de la de hoy. Por
      eso conviene leerlo junto al rango de edad.`,
    fuentePrincipal: "enadis",
    indicadorPrincipal: "No sabe leer ni escribir",
    formato: "pct",
    explica: `Porcentaje de personas que declararon no saber leer ni escribir.
      Es un rezago acumulado a lo largo de la vida: mide el acceso a la
      escuela de hace décadas, no el sistema educativo actual.`,
    secundarios: [
      {encuesta: "enadis", indicador: "Asiste a la escuela (18 a 29 años)", formato: "pct",
       nota: `Solo disponible en la edición 2022: la tabla sociodemográfica de
         2017 no trae la pregunta de asistencia escolar.`,
       explica: `Porcentaje de personas de 18 a 29 años que declararon estar
         inscritas y asistiendo a la escuela.`},
    ],
  },
  "trabajo-enadis": {
    encuesta: "enadis",
    titulo: "Trabajo según la ENADIS",
    kicker: "Trabajo",
    entrada: `La ENADIS también mide condición de actividad, lo que permite
      contrastar sus cifras con las de la ENIGH y el Censo.`,
    fuentePrincipal: "enadis",
    indicadorPrincipal: "Población ocupada",
    formato: "pct",
    explica: `Porcentaje de personas que declararon haber trabajado la semana
      anterior, o tener trabajo aunque no hubieran trabajado esa semana.`,
    secundarios: [
      {encuesta: "enadis", indicador: "Se dedica a los quehaceres del hogar", formato: "pct",
       explica: `Porcentaje de personas cuya actividad principal declarada son
         los quehaceres del hogar.`},
    ],
  },
};

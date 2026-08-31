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
    subtemas: ["trabajo", "educacion-enigh", "hogar", "ingreso", "gastos", "tecnologia"],
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
    bloques: [
      {
        titulo: "Otras tecnologías del hogar",
        indicadores: [
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
    bloques: [
      {
        titulo: "Hasta dónde llegó la escolaridad",
        indicadores: [
      {encuesta: "enigh", indicador: "Nivel más alto: Sin escolaridad", formato: "pct",
       nota: `Los siete niveles suman 100 % dentro de cada grupo: dicen dónde
         se detuvo la escolaridad, no cuántas pasaron un umbral. La brecha se
         produce abajo, no arriba — 40 % de las mujeres con discapacidad se
         quedó en primaria, contra 19 % de las mujeres sin discapacidad.`,
       explica: `Ninguna instrucción formal. Porcentaje de personas de 18 años o más de cada grupo.`},
      {encuesta: "enigh", indicador: "Nivel más alto: Primaria", formato: "pct",
       explica: `Primaria como nivel más alto, completa o no. Porcentaje de personas de 18 años o más de cada grupo.`},
      {encuesta: "enigh", indicador: "Nivel más alto: Secundaria", formato: "pct",
       explica: `Secundaria como nivel más alto. Porcentaje de personas de 18 años o más de cada grupo.`},
      {encuesta: "enigh", indicador: "Nivel más alto: Media superior", formato: "pct",
       explica: `Preparatoria o bachillerato como nivel más alto. Porcentaje de personas de 18 años o más de cada grupo.`},
      {encuesta: "enigh", indicador: "Nivel más alto: Técnica o normal", formato: "pct",
       explica: `Carrera técnica o normal, que la ENIGH separa de la licenciatura. Porcentaje de personas de 18 años o más de cada grupo.`},
      {encuesta: "enigh", indicador: "Nivel más alto: Licenciatura", formato: "pct",
       explica: `Estudios profesionales como nivel más alto. Porcentaje de personas de 18 años o más de cada grupo.`},
      {encuesta: "enigh", indicador: "Nivel más alto: Posgrado", formato: "pct",
       explica: `Maestría o doctorado. Agrupa los tres códigos de posgrado porque la escala cambió en 2024 y separarlos produciría una serie falsa. Porcentaje de personas de 18 años o más de cada grupo.`},
        ],
      },
      {
        titulo: "Rezago educativo",
        indicadores: [
      {encuesta: "enigh", indicador: "Sin ningún grado de escolaridad", formato: "pct",
       nota: `El extremo opuesto del indicador principal, y donde la brecha por
         discapacidad es más brutal: 16.2% contra 3.8% entre mujeres.`,
       explica: `Porcentaje de personas que declararon no haber aprobado ningún
         grado escolar.`},
      {encuesta: "enigh", indicador: "No sabe leer ni escribir (ENIGH)", formato: "pct",
       explica: `Porcentaje de personas que declararon no saber leer ni
         escribir. Es la misma pregunta que hace la ENADIS, así que las dos
         cifras se pueden contrastar.`},
        ],
      },
      {
        titulo: "Escolaridad en curso",
        indicadores: [
      {encuesta: "enigh", indicador: "Asiste a la escuela (18 a 29 años, ENIGH)", formato: "pct",
       explica: `Porcentaje de personas de 18 a 29 años inscritas y asistiendo
         a la escuela.`},
        ],
      },
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
    bloques: [
      {
        titulo: "Quién sostiene económicamente el hogar",
        indicadores: [
      {encuesta: "enigh", indicador: "La jefatura aporta la mitad o más del ingreso", formato: "pct",
       nota: `Encabezar el hogar y sostenerlo económicamente no son lo mismo.
         Una jefa con discapacidad aporta la mitad o más del ingreso en la
         mitad de los casos; un jefe sin discapacidad, en siete de cada diez.`,
       explica: `Porcentaje de quienes encabezan un hogar cuyo ingreso propio
         representa la mitad o más del ingreso total de ese hogar. Solo entre
         hogares con ingreso mayor que cero.`},
      {encuesta: "enigh", indicador: "Ingreso mensual de quien encabeza el hogar", formato: "pesos",
       explica: `Promedio mensual del ingreso propio de quien encabeza el
         hogar, en pesos constantes. Solo entre hogares con ingreso.`},
        ],
      },
      {
        titulo: "Edad de quien encabeza",
        indicadores: [
      {encuesta: "enigh", indicador: "Jefatura de 18-29 años", formato: "pct",
       explica: `Porcentaje de quienes encabezan un hogar en ese rango de edad.
         Los cuatro rangos suman 100 % dentro de cada grupo.`},
      {encuesta: "enigh", indicador: "Jefatura de 30-44 años", formato: "pct",
       explica: `Porcentaje de quienes encabezan un hogar en ese rango de edad.
         Los cuatro rangos suman 100 % dentro de cada grupo.`},
      {encuesta: "enigh", indicador: "Jefatura de 45-59 años", formato: "pct",
       explica: `Porcentaje de quienes encabezan un hogar en ese rango de edad.
         Los cuatro rangos suman 100 % dentro de cada grupo.`},
      {encuesta: "enigh", indicador: "Jefatura de 60+ años", formato: "pct",
       nota: `Es la cifra que reencuadra toda la sección: 68 % de las jefas con
         discapacidad tiene 60 años o más, contra 32 % de las jefas sin ella.
         La jefatura femenina en este grupo refleja sobre todo viudez, no
         autonomía económica.`,
       explica: `Porcentaje de quienes encabezan un hogar que tienen 60 años o
         más. El denominador son las jefaturas, no toda la población.`},
        ],
      },
      {
        titulo: "Escolaridad de quien encabeza",
        indicadores: [
      {encuesta: "enigh", indicador: "Jefatura con escolaridad: Sin escolaridad", formato: "pct",
       nota: `La escolaridad de quien encabeza el hogar, con la misma escala
         de la página de Educación para que las dos se lean igual.`,
       explica: `Porcentaje de quienes encabezan un hogar cuyo nivel más alto
         es sin escolaridad. Los seis niveles suman 100 % dentro de cada grupo.`},
      {encuesta: "enigh", indicador: "Jefatura con escolaridad: Primaria", formato: "pct",
       explica: `Porcentaje de quienes encabezan un hogar cuyo nivel más alto
         es primaria. Los seis niveles suman 100 % dentro de cada grupo.`},
      {encuesta: "enigh", indicador: "Jefatura con escolaridad: Secundaria", formato: "pct",
       explica: `Porcentaje de quienes encabezan un hogar cuyo nivel más alto
         es secundaria. Los seis niveles suman 100 % dentro de cada grupo.`},
      {encuesta: "enigh", indicador: "Jefatura con escolaridad: Media superior", formato: "pct",
       explica: `Porcentaje de quienes encabezan un hogar cuyo nivel más alto
         es media superior. Los seis niveles suman 100 % dentro de cada grupo.`},
      {encuesta: "enigh", indicador: "Jefatura con escolaridad: Licenciatura", formato: "pct",
       explica: `Porcentaje de quienes encabezan un hogar cuyo nivel más alto
         es licenciatura. Los seis niveles suman 100 % dentro de cada grupo.`},
      {encuesta: "enigh", indicador: "Jefatura con escolaridad: Posgrado", formato: "pct",
       explica: `Porcentaje de quienes encabezan un hogar cuyo nivel más alto
         es posgrado. Los seis niveles suman 100 % dentro de cada grupo.`},
        ],
      },
    ],
  },

  ingreso: {
    encuesta: "enigh",
    titulo: "Ingreso y apoyos",
    kicker: "Ingreso",
    entrada: `De dónde viene el dinero del hogar y cuánto aporta cada persona.
      Un mismo ingreso total no significa lo mismo según su origen: el que
      viene de programas sociales depende de que esos programas sigan
      existiendo, y el del trabajo no. Lo que SALE del bolsillo del hogar
      —aparatos, cuidados, transporte— vive en la sección de Gastos.`,
    fuentePrincipal: "enigh",
    indicadorPrincipal: "Ingreso mensual propio",
    formato: "pesos",
    explica: `Promedio mensual del ingreso de la propia persona, sumando
      todas sus fuentes. A diferencia del resto de la página, este SÍ es
      individual: la ENIGH registra el ingreso por renglón de persona, no
      solo por hogar. Solo entre quienes viven en un hogar con ingreso
      registrado, y en pesos constantes.`,
    bloques: [
      {
        titulo: "De dónde viene el ingreso del hogar",
        indicadores: [
      {encuesta: "enigh", indicador: "Su hogar recibe ingreso de trabajo", formato: "pct",
       nota: `Las cinco fuentes van juntas porque la comparación entre ellas
         ES el análisis: un hogar que vive de su trabajo y otro que vive de
         programas sociales tienen el mismo ingreso con distinta fragilidad.`,
       explica: `Porcentaje de personas que viven en un hogar con al menos un
         ingreso por trabajo: sueldos, salarios, horas extra o aguinaldo. Es
         un dato de HOGAR heredado a la persona, así que no dice que ella
         trabaje sino que alguien en su hogar percibe ingreso laboral.`},
      {encuesta: "enigh", indicador: "Su hogar recibe ingreso de programas sociales", formato: "pct",
       nota: `Es el contraste que da sentido a la página: 61.8 % de las mujeres
         con discapacidad vive en un hogar que recibe programas sociales,
         contra 33.9 % de las mujeres sin discapacidad. Su ingreso depende
         mucho más de la política pública que del mercado laboral.`,
       explica: `Incluye los programas del Bienestar —entre ellos la pensión
         de discapacidad y la de adultos mayores— y los programas sociales
         previos. Porcentaje de personas cuyo hogar recibe al menos uno.`},
      {encuesta: "enigh", indicador: "Su hogar recibe ingreso de transferencias (pensiones, remesas)", formato: "pct",
       explica: `Jubilaciones y pensiones contributivas, indemnizaciones,
         remesas, donativos y becas privadas. Se reportan aparte de los
         programas sociales porque una pensión se ganó trabajando y una beca
         del gobierno es política social vigente: no son lo mismo para leer
         qué tan estable es el ingreso.`},
      {encuesta: "enigh", indicador: "Su hogar recibe ingreso de negocio propio", formato: "pct",
       explica: `Ingreso por negocio del hogar, cooperativas o sociedades.`},
      {encuesta: "enigh", indicador: "Su hogar recibe ingreso de rentas y alquileres", formato: "pct",
       explica: `Alquiler de inmuebles y tierras, intereses y rendimientos.
         Es la fuente menos frecuente en los cuatro grupos.`},
        ],
      },
      {
        titulo: "Cuánto aporta cada fuente",
        indicadores: [
      {encuesta: "enigh", indicador: "Ingreso mensual del hogar por trabajo", formato: "pesos",
       nota: `Entre los hogares que sí tienen esa fuente. Las mujeres con
         discapacidad viven en hogares que reciben tres cuartas partes de lo
         que reciben los de las mujeres sin discapacidad.`,
       explica: `Promedio mensual que aporta el trabajo al hogar, solo entre
         hogares con ingreso laboral. En pesos constantes: cada edición viene
         en pesos de su año y se deflactó con el INPC del levantamiento.`},
      {encuesta: "enigh", indicador: "Ingreso mensual del hogar por programas sociales", formato: "pesos",
       nota: `Es la única fuente donde los hogares con discapacidad reciben
         MÁS que los demás (1.15 veces), y tiene una explicación directa:
         existe una pensión dirigida a ellos.`,
       explica: `Promedio mensual por programas sociales, entre hogares que
         reciben alguno. En pesos constantes.`},
      {encuesta: "enigh", indicador: "Ingreso mensual del hogar por transferencias (pensiones, remesas)", formato: "pesos",
       explica: `Promedio mensual por transferencias, entre hogares que las
         reciben. En pesos constantes.`},
        ],
      },
      {
        titulo: "Apoyos y becas",
        indicadores: [
      {encuesta: "enigh", indicador: "Recibe la beca de discapacidad", formato: "pct",
       nota: `La pensión federal para personas con discapacidad, que dentro de
         la composición de arriba forma parte de los programas sociales.`,
       explica: `Porcentaje de personas que viven en un hogar donde alguien
         recibe la pensión federal para personas con discapacidad. Es un dato
         de HOGAR heredado a la persona: la encuesta registra el ingreso por
         hogar, no por individuo, así que no dice que cada persona reciba la
         beca sino que su hogar la recibe.`},
      {encuesta: "enigh", indicador: "Recibe la pensión de adultos mayores", formato: "pct",
       nota: `Sirve de contraste: es el programa social de mayor cobertura del
         país, y muestra cómo se ve un apoyo verdaderamente masivo frente a la
         beca de discapacidad.`,
       explica: `Porcentaje de personas que viven en un hogar donde alguien
         recibe la pensión para adultos mayores.`},
        ],
      },
      {
        titulo: "Quién sostiene el hogar",
        indicadores: [
      {encuesta: "enigh", indicador: "Aporta la mitad o más del ingreso de su hogar", formato: "pct",
       nota: `Responde quién sostiene económicamente al hogar. Un hombre sin
         discapacidad lo hace en la mitad de los casos; una mujer con
         discapacidad, en poco más de una cuarta parte.`,
       explica: `Porcentaje de personas cuyo ingreso propio representa la
         mitad o más del ingreso total de su hogar. Solo entre hogares con
         ingreso mayor que cero: sin denominador la proporción no existe, y
         contar esos casos como "no aporta" mezclaría no tener ingreso propio
         con vivir en un hogar sin ingreso alguno.`},
        ],
      },
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
    bloques: [
      {
        titulo: "Cuánto se gasta en aparatos y cuidados",
        indicadores: [
      {encuesta: "enigh", indicador: "Gasto trimestral en aparatos o cuidados por discapacidad", formato: "pesos",
       nota: `El promedio se calcula solo entre quienes gastan algo: "cuánto
         gasta el que gasta", no diluido con los hogares en cero.`,
       explica: `Promedio de pesos gastados en el trimestre, entre las
         personas cuyo hogar registró algún gasto asociado a discapacidad.
         No incluye a quienes viven en un hogar sin ese gasto. En pesos
         constantes de 2024: la ENIGH estandariza el gasto a precios de
         agosto de su propia edición, lo que lo deja comparable dentro de un
         año pero no entre años.`},
        ],
      },
      {
        titulo: "En qué se gasta, por concepto",
        indicadores: [
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
        ],
      },
      {
        titulo: "Transporte: quiénes gastan",
        indicadores: [
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
      {
        titulo: "Transporte: cuánto gastan",
        indicadores: [
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
        ],
      },
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
    bloques: [
      {
        titulo: "Los otros ámbitos donde ocurre",
        indicadores: [
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
      },
    ],
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

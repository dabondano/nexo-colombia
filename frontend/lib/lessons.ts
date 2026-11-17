/**
 * First learning path of the Academia module.
 *
 * DRAFT: written from the text of the Constitution loaded in NEXO (Función
 * Pública's edition) and pending review by a legally qualified person before
 * publication (docs/ASSUMPTIONS.md, A-007). Every statement carries an Epistemic
 * Label and cites the articles it rests on, so a reader can check it.
 */

export type Label = "hecho_documentado" | "interpretacion_juridica";

export type Statement = {
  text: string;
  label: Label;
  /** Article numbers of the Constitution, as printed: "11", "238A". */
  articles: string[];
};

export type Step = { heading: string; statements: Statement[] };

export type Question = {
  question: string;
  options: string[];
  /** Index in `options`. */
  answer: number;
  explanation: string;
  articles: string[];
};

export type Term = { term: string; definition: string; articles: string[] };

export type Lesson = {
  slug: string;
  title: string;
  summary: string;
  steps: Step[];
  related?: { label: string; href: string }[];
  glossary: Term[];
  quiz: Question[];
};

export const REVIEW_STATUS =
  "Borrador pendiente de revisión por una persona con formación jurídica. No es asesoría legal.";

const fact = (text: string, ...articles: string[]): Statement => ({
  text,
  label: "hecho_documentado",
  articles,
});
const reading = (text: string, ...articles: string[]): Statement => ({
  text,
  label: "interpretacion_juridica",
  articles,
});

export function articlePath(article: string): string {
  return `/constitucion/articulo-${article.toLowerCase().replace(/^(\d+)([a-z])$/, "$1-$2")}`;
}

export const LESSONS: Lesson[] = [
  {
    slug: "estructura-del-estado",
    title: "Cómo está organizado el Estado",
    summary:
      "Las ramas del poder público, los órganos de control, la organización electoral y las entidades territoriales, según la Constitución.",
    steps: [
      {
        heading: "La Constitución, norma de normas",
        statements: [
          fact(
            "La Constitución es norma de normas: si una ley u otra norma es incompatible con ella, se aplica la Constitución.",
            "4",
          ),
          fact(
            "Colombia es un Estado social de derecho, organizado como república unitaria, descentralizada, con autonomía de sus entidades territoriales, democrática, participativa y pluralista.",
            "1",
          ),
          fact(
            "Ninguna autoridad del Estado puede ejercer funciones distintas de las que le atribuyen la Constitución y la ley.",
            "121",
          ),
        ],
      },
      {
        heading: "Tres ramas y otros órganos",
        statements: [
          fact(
            "Las ramas del poder público son la legislativa, la ejecutiva y la judicial. Además existen otros órganos, autónomos e independientes, para cumplir las demás funciones del Estado.",
            "113",
          ),
          fact(
            "Los diferentes órganos del Estado tienen funciones separadas, pero colaboran armónicamente para realizar sus fines.",
            "113",
          ),
          reading(
            "Esta fórmula suele describirse como separación de poderes con colaboración armónica: cada órgano tiene sus funciones, pero ninguno actúa aislado de los demás.",
            "113",
          ),
        ],
      },
      {
        heading: "La rama legislativa: el Congreso",
        statements: [
          fact(
            "Al Congreso le corresponde reformar la Constitución, hacer las leyes y ejercer control político sobre el gobierno y la administración. Lo integran el Senado y la Cámara de Representantes.",
            "114",
          ),
          fact(
            "El Senado tiene cien miembros elegidos en circunscripción nacional, más dos elegidos en una circunscripción nacional especial por comunidades indígenas.",
            "171",
          ),
          fact(
            "La Cámara de Representantes se elige en circunscripciones territoriales y especiales. Cada departamento y el Distrito Capital de Bogotá forman una circunscripción territorial.",
            "176",
          ),
          fact(
            "Senadores y representantes se eligen para un período de cuatro años, que empieza el 20 de julio siguiente a la elección.",
            "132",
          ),
        ],
      },
      {
        heading: "La rama ejecutiva: el Presidente y el Gobierno",
        statements: [
          fact(
            "El Presidente de la República es Jefe del Estado, Jefe del Gobierno y suprema autoridad administrativa.",
            "115",
          ),
          fact(
            "El Gobierno Nacional está formado por el Presidente, los ministros del despacho y los directores de departamentos administrativos.",
            "115",
          ),
          fact(
            "El Presidente se elige para cuatro años con la mitad más uno de los votos. Si nadie la obtiene, tres semanas después hay una nueva votación entre los dos candidatos con más votos.",
            "190",
          ),
        ],
      },
      {
        heading: "La rama judicial",
        statements: [
          fact(
            "Administran justicia, entre otros, la Corte Constitucional, la Corte Suprema de Justicia, el Consejo de Estado, la Comisión Nacional de Disciplina Judicial, la Fiscalía General de la Nación, los tribunales y los jueces.",
            "116",
          ),
          fact(
            "A la Corte Constitucional se le confía la guarda de la integridad y supremacía de la Constitución.",
            "241",
          ),
        ],
      },
      {
        heading: "Órganos de control y organización electoral",
        statements: [
          fact(
            "El Ministerio Público y la Contraloría General de la República son órganos de control.",
            "117",
          ),
          fact(
            "El Ministerio Público lo ejercen el Procurador General de la Nación, el Defensor del Pueblo, los personeros municipales y otros funcionarios. Le corresponde la guarda y promoción de los derechos humanos, la protección del interés público y la vigilancia de la conducta oficial de quienes desempeñan funciones públicas.",
            "118",
          ),
          fact(
            "La Contraloría General de la República vigila la gestión fiscal y controla los resultados de la administración.",
            "119",
          ),
          fact(
            "La organización electoral está conformada por el Consejo Nacional Electoral, la Registraduría Nacional del Estado Civil y los demás organismos que establezca la ley.",
            "120",
          ),
        ],
      },
      {
        heading: "El territorio",
        statements: [
          fact(
            "Son entidades territoriales los departamentos, los distritos, los municipios y los territorios indígenas. La ley puede dar ese carácter a regiones y provincias.",
            "286",
          ),
        ],
      },
    ],
    related: [
      { label: "Directorio de entidades públicas", href: "/instituciones" },
    ],
    glossary: [
      {
        term: "Control político",
        definition:
          "Función del Congreso de vigilar al gobierno y a la administración, distinta de la función de hacer leyes.",
        articles: ["114"],
      },
      {
        term: "Órganos autónomos e independientes",
        definition:
          "Órganos del Estado que no pertenecen a ninguna de las tres ramas, como los órganos de control y la organización electoral.",
        articles: ["113", "117", "120"],
      },
    ],
    quiz: [
      {
        question: "¿Qué ramas del poder público reconoce la Constitución?",
        options: [
          "Legislativa, ejecutiva y judicial",
          "Legislativa, ejecutiva, judicial y electoral",
          "Ejecutiva y judicial",
        ],
        answer: 0,
        explanation:
          "La organización electoral existe, pero no es una rama: es uno de los órganos autónomos.",
        articles: ["113", "120"],
      },
      {
        question:
          "¿Cuántos senadores se eligen en la circunscripción nacional ordinaria?",
        options: ["Cincuenta", "Cien", "Ciento ocho"],
        answer: 1,
        explanation:
          "Cien, más dos en la circunscripción nacional especial indígena.",
        articles: ["171"],
      },
      {
        question: "¿Cuáles son los órganos de control?",
        options: [
          "La Fiscalía y la Registraduría",
          "El Ministerio Público y la Contraloría General de la República",
          "La Corte Constitucional y el Consejo de Estado",
        ],
        answer: 1,
        explanation:
          "La Fiscalía administra justicia y la Registraduría es parte de la organización electoral.",
        articles: ["117", "116", "120"],
      },
    ],
  },
  {
    slug: "como-se-hace-una-ley",
    title: "Cómo se hace una ley",
    summary:
      "Quién puede presentar un proyecto, cuántos debates necesita, qué pasa con la sanción y las objeciones, y qué leyes tienen reglas especiales.",
    steps: [
      {
        heading: "Quién puede proponer una ley",
        statements: [
          fact("Corresponde al Congreso hacer las leyes.", "150"),
          fact(
            "Los proyectos pueden originarse en cualquiera de las cámaras, por propuesta de sus miembros, del Gobierno Nacional, de las entidades señaladas en el artículo 156, o por iniciativa popular.",
            "154",
          ),
          fact(
            "Algunas leyes solo pueden dictarse o reformarse por iniciativa del Gobierno, como las que decretan exenciones de impuestos, contribuciones o tasas nacionales.",
            "154",
          ),
          fact(
            "Pueden presentar proyectos de ley o de reforma constitucional un número de ciudadanos igual o superior al cinco por ciento del censo electoral, o el treinta por ciento de los concejales o diputados del país.",
            "155",
          ),
        ],
      },
      {
        heading: "Un solo tema y un título que corresponda",
        statements: [
          fact(
            "Todo proyecto de ley debe referirse a una misma materia; las disposiciones que no se relacionen con ella son inadmisibles.",
            "158",
          ),
          fact(
            "El título de las leyes debe corresponder precisamente a su contenido.",
            "169",
          ),
        ],
      },
      {
        heading: "Los debates",
        statements: [
          fact(
            "Ningún proyecto será ley sin haber sido publicado oficialmente por el Congreso, aprobado en primer debate en la comisión permanente de cada cámara, aprobado en segundo debate en cada cámara y sancionado por el Gobierno.",
            "157",
          ),
          reading(
            "Por regla general son entonces cuatro debates: comisión y plenaria en cada una de las dos cámaras. El reglamento del Congreso define los casos en que el primer debate se hace en sesión conjunta de las comisiones.",
            "157",
          ),
          fact(
            "Entre el primero y el segundo debate deben pasar al menos ocho días, y entre la aprobación en una cámara y el inicio del debate en la otra, al menos quince días.",
            "160",
          ),
          fact(
            "Si las cámaras aprueban textos distintos, comisiones de conciliadores de ambas procuran conciliarlos, y el texto escogido se somete a las plenarias.",
            "161",
          ),
        ],
      },
      {
        heading: "Plazos y urgencia",
        statements: [
          fact(
            "Un proyecto que recibió primer debate y no terminó su trámite en una legislatura continúa en la siguiente, pero ningún proyecto puede ser considerado en más de dos legislaturas.",
            "162",
          ),
          fact(
            "El Presidente puede pedir trámite de urgencia para cualquier proyecto; en ese caso la cámara debe decidir dentro de treinta días.",
            "163",
          ),
        ],
      },
      {
        heading: "Sanción y objeciones",
        statements: [
          fact(
            "Aprobado por ambas cámaras, el proyecto pasa al Gobierno. Si no lo objeta, ordena promulgarlo como ley; si lo objeta, lo devuelve a la cámara de origen.",
            "165",
          ),
          fact(
            "El Gobierno tiene seis días para objetar un proyecto de hasta veinte artículos, diez días si tiene de veintiuno a cincuenta, y hasta veinte días si tiene más de cincuenta.",
            "166",
          ),
          fact(
            "Si el proyecto fue objetado por inconstitucional y las cámaras insisten, pasa a la Corte Constitucional, que decide dentro de los seis días siguientes.",
            "167",
          ),
          fact(
            "Si el Presidente no cumple el deber de sancionar, sanciona y promulga el Presidente del Congreso.",
            "168",
          ),
        ],
      },
      {
        heading: "Leyes con reglas especiales",
        statements: [
          fact(
            "Las leyes orgánicas, a las que se sujeta la actividad legislativa, requieren la mayoría absoluta de los votos de los miembros de una y otra cámara.",
            "151",
          ),
          fact(
            "Las leyes estatutarias requieren mayoría absoluta de los miembros del Congreso, deben tramitarse en una sola legislatura y tienen revisión previa de la Corte Constitucional.",
            "153",
          ),
          fact(
            "Las reformas a la Constitución por el Congreso (actos legislativos) se tramitan en dos períodos ordinarios y consecutivos.",
            "375",
          ),
        ],
      },
    ],
    related: [
      {
        label: "Proyectos de ley de la Cámara de Representantes",
        href: "/legislacion",
      },
    ],
    glossary: [
      {
        term: "Sanción",
        definition:
          "Aprobación del proyecto por el Gobierno, último requisito para que sea ley.",
        articles: ["157", "165"],
      },
      {
        term: "Objeción",
        definition:
          "Devolución del proyecto por el Gobierno, por razones de inconveniencia o de inconstitucionalidad.",
        articles: ["165", "167"],
      },
      {
        term: "Iniciativa popular",
        definition:
          "Proyecto presentado por ciudadanos, concejales o diputados en el número que fija la Constitución.",
        articles: ["155"],
      },
    ],
    quiz: [
      {
        question:
          "¿Cuál es el último requisito para que un proyecto aprobado por el Congreso sea ley?",
        options: [
          "La revisión de la Corte Constitucional",
          "La sanción del Gobierno",
          "La publicación en un periódico",
        ],
        answer: 1,
        explanation:
          "La revisión previa de la Corte es obligatoria solo para algunos proyectos, como los estatutarios.",
        articles: ["157", "153"],
      },
      {
        question:
          "¿En cuántas legislaturas puede considerarse como máximo un proyecto de ley?",
        options: ["Una", "Dos", "Cuatro"],
        answer: 1,
        explanation:
          "Si recibió primer debate, puede continuar en la legislatura siguiente, pero no en una tercera.",
        articles: ["162"],
      },
      {
        question:
          "Si el Presidente no sanciona una ley en los términos de la Constitución, ¿quién la sanciona?",
        options: [
          "El Presidente del Congreso",
          "La Corte Constitucional",
          "El Vicepresidente",
        ],
        answer: 0,
        explanation: "Lo dispone el artículo 168.",
        articles: ["168"],
      },
    ],
  },
];

/** Every article the path cites, for checking that each link resolves. */
export function citedArticles(): string[] {
  const all = LESSONS.flatMap((lesson) => [
    ...lesson.steps.flatMap((step) =>
      step.statements.flatMap((s) => s.articles),
    ),
    ...lesson.glossary.flatMap((t) => t.articles),
    ...lesson.quiz.flatMap((q) => q.articles),
  ]);
  return [...new Set(all)];
}

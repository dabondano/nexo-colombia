/** The six modules of NEXO Colombia and their honest delivery stage. */

export type Stage = "Diseñado" | "Implementado" | "Probado" | "Integrado" | "Desplegado";

export type NexoModule = {
  number: string;
  name: string;
  summary: string;
  /** Stage of the module as a whole. */
  stage: Stage;
  /** A first part of the module that already works with real data. */
  available?: { label: string; href: string };
};

export const MODULES: NexoModule[] = [
  {
    number: "01",
    name: "Academia",
    summary:
      "Educación cívica y jurídica: la Constitución, la estructura del Estado, el trámite legislativo, el sistema electoral y la rama judicial.",
    stage: "Diseñado",
  },
  {
    number: "02",
    name: "Legislación",
    summary:
      "Investigación de normas, proyectos de ley y jurisprudencia, con historial de trámite y citas verificables.",
    stage: "Diseñado",
    available: { label: "Proyectos de ley de la Cámara", href: "/legislacion" },
  },
  {
    number: "03",
    name: "Instituciones",
    summary:
      "Directorio de entidades públicas y servidores, con cargos, períodos y relaciones documentadas.",
    stage: "Diseñado",
    available: { label: "Directorio de entidades públicas", href: "/instituciones" },
  },
  {
    number: "04",
    name: "Recursos Públicos",
    summary:
      "Contratación y presupuesto: valores apropiados, contratados y pagados, siempre diferenciados.",
    stage: "Diseñado",
  },
  {
    number: "05",
    name: "Análisis Político",
    summary:
      "Composición política, votaciones registradas y simulación de escenarios legislativos hipotéticos.",
    stage: "Diseñado",
  },
  {
    number: "06",
    name: "Observatorio",
    summary:
      "Búsqueda unificada y grafo de conocimiento que conecta todos los módulos.",
    stage: "Diseñado",
    available: { label: "Búsqueda en proyectos y entidades", href: "/buscar" },
  },
];

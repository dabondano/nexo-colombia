/** Every Constitution article a lesson cites, for checks of the learning path. */
import { LESSONS, articlePath, type Lesson } from "./lessons.ts";

export function citedArticles(lessons: Lesson[] = LESSONS): string[] {
  const cited = new Set<string>();
  for (const lesson of lessons) {
    for (const step of lesson.steps) step.statements.forEach((s) => s.articles.forEach((a) => cited.add(a)));
    lesson.glossary.forEach((term) => term.articles.forEach((a) => cited.add(a)));
    lesson.quiz.forEach((question) => question.articles.forEach((a) => cited.add(a)));
  }
  return [...cited].sort((a, b) => parseInt(a) - parseInt(b) || a.localeCompare(b));
}

/** The API path of a cited article, from its page path ("/constitucion/articulo-11" → key "articulo-11"). */
export function articleApiPath(article: string): string {
  const key = articlePath(article).slice("/constitucion/".length);
  return `/api/v1/instruments/constitucion-politica-1991/provisions/${key}`;
}

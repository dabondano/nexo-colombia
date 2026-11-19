import assert from "node:assert/strict";
import { test } from "node:test";
import { citedArticles } from "../lib/lesson-links.ts";
import { LESSONS, articlePath } from "../lib/lessons.ts";

test("lessons have unique slugs, a glossary and a quiz with valid answers", () => {
  assert.equal(new Set(LESSONS.map((l) => l.slug)).size, LESSONS.length);
  for (const lesson of LESSONS) {
    assert.match(lesson.slug, /^[a-z0-9]+(-[a-z0-9]+)*$/);
    assert.ok(lesson.glossary.length > 0, `${lesson.slug}: glossary`);
    assert.ok(lesson.quiz.length > 0, `${lesson.slug}: quiz`);
    for (const question of lesson.quiz) {
      assert.ok(question.answer >= 0 && question.answer < question.options.length, question.question);
      assert.ok(question.articles.length > 0, `${question.question}: cites an article`);
    }
    for (const step of lesson.steps) {
      for (const statement of step.statements) {
        assert.ok(statement.articles.length > 0, `${lesson.slug}: every statement cites an article`);
      }
    }
    for (const item of lesson.related ?? []) assert.match(item.href, /^\/[a-z]/, "related links stay on NEXO");
  }
});

test("cited article numbers are well formed and map to article pages", () => {
  const cited = citedArticles();
  assert.ok(cited.length > 10);
  for (const article of cited) assert.match(article, /^\d+[A-Z]?$/);
  assert.equal(articlePath("11"), "/constitucion/articulo-11");
  assert.equal(articlePath("238A"), "/constitucion/articulo-238-a");
});

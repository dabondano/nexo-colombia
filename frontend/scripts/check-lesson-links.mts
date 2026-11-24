/**
 * Checks that every Constitution article cited by the learning path exists in
 * the loaded data (M3: "every lesson link resolves").
 * Usage: node --experimental-strip-types scripts/check-lesson-links.mts http://localhost:8000
 */
import { articleApiPath, citedArticles } from "../lib/lesson-links.ts";

const base = process.argv[2] ?? process.env.NEXO_API_URL ?? "http://localhost:8000";
const missing: string[] = [];
const cited = citedArticles();
for (const article of cited) {
  const response = await fetch(new URL(articleApiPath(article), base), { method: "HEAD" });
  if (response.status !== 200) missing.push(`${article} (${response.status})`);
}
console.log(`${cited.length} cited articles checked against ${base}; missing: ${missing.length}`);
if (missing.length > 0) {
  console.log(missing.join("\n"));
  process.exit(1);
}

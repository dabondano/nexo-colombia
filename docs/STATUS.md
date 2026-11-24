# NEXO Colombia — Project Status

Last updated: 2026-11-19 (MVP review prepared, docs/08)

## Completed work

| Item | Stage | Evidence |
|---|---|---|
| Phase 0 discovery | Done | `00-technical-assessment.md` |
| Source verification, first pass (16 datos.gov.co datasets checked by API) | Done | `04-source-registry.md` |
| PRD, functional and non-functional requirements, user stories, journeys | Diseñado | `01-prd.md` |
| System architecture, ingestion strategy, security architecture, API outline, ADR-001 to ADR-005 | Diseñado | `02-architecture.md` |
| Data model and knowledge graph, ER overview | Diseñado | `03-data-model.md` |
| MVP scope, milestones, risk register | Diseñado | `05-mvp-roadmap-risks.md` |

## Current implementation

| Item | Stage | Evidence |
|---|---|---|
| API skeleton: health endpoints, settings, OpenAPI | Probado | `backend/tests/test_health.py` |
| Provenance tables (`core.source`, `core.sync_run`, `core.source_record`) with migration | Probado | `backend/tests/test_sources.py`, `test_migrations.py` (upgrade and downgrade) |
| Source registry API (`/api/v1/sources`) seeded with four sources verified on 2026-11-17 | Probado | `backend/tests/test_sources.py` |
| Controlled vocabularies (epistemic labels, confidence classes, data-quality status) | Probado | `backend/tests/test_labels.py` |
| Generic datos.gov.co (Socrata) connector: paging, crawl delay, retries with backoff | Probado | `backend/tests/test_socrata.py` (simulated portal); used for the real loads below |
| Ingestion pipeline: field allow-list, validation, rejects with reasons, append-only raw items, versioned updates, failed runs leave published data untouched | Probado | `backend/tests/test_pipeline.py`, `test_datasets.py` |
| "Universo de entidades" loaded into `core.institution` | Integrado (development database only) | Run of 2026-11-17: 6,404 rows seen, 6,404 loaded, 0 rejected; 304 national and 6,100 territorial, matching the source registry. A second run reported 6,404 unchanged |
| Cámara "Proyectos de Ley" loaded into `core.legislative_initiative` | Integrado (development database only) | Run of 2026-11-17: 6,606 rows seen, 6,605 loaded, 1 rejected (the placeholder row "FALLA EN EL APLICATIVO", stored in `core.sync_reject`) |
| Institutions API (`/api/v1/institutions`, filters, detail with provenance) | Probado | `backend/tests/test_records_api.py` |
| Initiatives API (`/api/v1/initiatives`, filters, detail with provenance) | Probado | `backend/tests/test_records_api.py` |
| Search index `search.document`, kept up to date as records are published and rebuildable from the records (`python -m app.search.reindex`) | Probado | `backend/tests/test_search.py`; 13,009 documents built from the loaded data in the development database |
| Unified search API (`/api/v1/search`): all words required, accents, capitals and plurals ignored, quoted phrases, exclusions, bill numbers and NIT, filter by record type and date range, counts per type | Probado | `backend/tests/test_search.py` |
| Search box on every page and results page "Buscar" | Probado | `frontend/e2e` (desktop and phone, sample data): header search to a record and its origin, results with and without matches under axe-core; earlier manual check against the real data (type tabs, paging, numbers, phrases, hostile input) |
| Web pages "Instituciones" and "Legislación": search, filters, paging, record page with the "Origen de este registro" panel; home page shows counts of loaded records with their source | Probado | `frontend/e2e` (desktop and phone, sample data): directory filters and paging, record pages and their origin panel under axe-core, 404 for unknown records; earlier manual check against the real data |
| Web shell in Spanish and "Fuentes" page reading the API | Probado | `frontend/e2e` (desktop and phone, sample data): Fuentes lists each source with its official link, home page shows each dataset with its count and source; checked on 2026-11-19 with an empty database and with the API unreachable: every page says so instead of showing figures |
| Law model (`core.legal_instrument`, `core.legal_provision`, `core.provision_version`): provisions as a tree with stable keys, wording versioned (a changed wording adds a version, at most one current) | Probado | `backend/tests/test_constitution.py`, `test_migrations.py` |
| Constitution reader for Función Pública's page: preamble, titles, chapters and articles; editor's notes, wording after "TEXTO ANTERIOR" and struck-through words kept apart; stops on an unexpected structure | Probado | `backend/tests/test_constitution.py` (page with the same HTML patterns) |
| Constitution loaded into the law tables | Integrado (development database only) | Run of 2026-11-17 from the live page: 448 rows (the instrument, the preamble, 13 titles, 49 chapters, 384 articles: 1 to 380 plus 22A, 178A, 238A and 257A), 0 rejected; 73 articles marked incomplete because the source mixes in earlier or struck-through wording; a second run reported 448 unchanged |
| Law API (`/api/v1/instruments`, `/instruments/{slug}` with outline, `/instruments/{slug}/provisions/{key}`, `/provisions/{id}`), with ancestors, previous and next, and provenance | Probado | `backend/tests/test_constitution.py` |
| Articles in the unified search (wording presented as in force only; records whose title has every word come first, so "artículo 86" finds the article) | Probado | `backend/tests/test_constitution.py`, `test_search.py`; 13,393 documents in the development database |
| Web pages "Constitución" (outline with edition note and review marks) and article page (wording, notes, earlier wording and struck words shown apart, warning, neighbours, provenance) | Probado | `frontend/e2e` (desktop and phone, sample data): outline to an article and its neighbours, article page under axe-core, 404 for a missing article; earlier manual check against the loaded text |
| First learning path "Aprender" (two lessons: how the State is organized, how a law is made; glossary and review questions), every statement labelled and linked to its articles | Probado (draft until approved in the review workflow) | `frontend/unit/lessons.test.ts` (structure: every statement and question cites an article, valid answers); `frontend/e2e` (lesson steps, glossary, quiz answer with its citation); `pnpm check:lesson-links` on 2026-11-19 against the real loaded Constitution: all 34 cited articles exist; **content not yet reviewed by a legally qualified person** (A-007) |
| CI workflow (backend lint, types, tests; frontend lint, build; interface and accessibility tests) | Integrado | `.github/workflows/ci.yml`; runs on every pull request |
| Staff accounts and sign-in (ADR-006): roles administrator, data steward and legal reviewer; Argon2id passwords; issued passwords must be changed at first sign-in; lockout after five failures; sessions of 12 hours (2 hours idle) revoked on sign-out, password or role change and deactivation; first administrator created with `python -m app.auth.cli create-admin` | Probado | `backend/tests/test_auth.py` (sign-in and out, identical answers for unknown and wrong accounts, lockout, idle expiry, permissions per role, issued passwords, last administrator kept); `frontend/e2e/staff.spec.ts` |
| Append-only audit log (`core.audit_event`; the database rejects updates and deletes): sign-ins, failed sign-ins, sign-outs, password changes and resets, account creation and changes, data synchronizations | Probado | `test_auth.py`; panel page "Registro de auditoría" (administrators) |
| Staff panel (`/ingresar`, `/panel`): accounts (administrators), synchronizations with their figures and the rejected rows with reasons and published content (data stewards), audit log (administrators), password change; not indexed by search engines | Probado | `frontend/e2e/staff.spec.ts`, including axe-core checks of the panel pages; no data is changed from the panel except accounts and reviews |
| Legal review workflow (A-007): legal reviewers (and administrators) approve or request changes on each lesson and on each article of the Constitution, with internal notes; each review is pinned to a fingerprint of exactly what was reviewed (a lesson's SHA-256, an article's current wording version), so an edit or a new wording makes the content pending again; history kept, never edited | Probado | `backend/tests/test_reviews.py`; `frontend/e2e/staff.spec.ts` (approve a lesson and see it on the public page; request changes on an article without the note becoming public) |
| Public review status: the learning path and each lesson say "Revisado por el equipo de revisión jurídica de NEXO el …" only for approved current content, "cambió después de su última revisión" when it was edited since, and the draft notice otherwise; an article shows a review note only when its current wording was approved. Reviewer names and notes are never public | Probado | `frontend/e2e/staff.spec.ts` (approval appears on the public lesson page; a request for changes does not); pages fall back to the draft notice while the status loads or if the API is unavailable (checked 2026-11-19) |
| National budget execution (MinHacienda, S-005 `xjxk-qhsc`) loaded into `core.budget_execution` | Integrado (development database only) | Run of 2026-11-18: 600 rows seen, 600 loaded, 0 rejected; 221 entities; total appropriation $543,188,100,676,463, commitments 79.47 %, payments 69.87 %; `backend/tests/test_budget.py` |
| Budget API (`/api/v1/budget/summary`, `/filters`, `/entities`, `/entities/{code}`) with rates computed from the published figures and the formula stated; alphabetical, no rankings (A-013) | Probado | `backend/tests/test_budget.py` |
| Web pages "Presupuesto" (totals, totals by sector, entity directory with search and sector filter) and entity page (amounts, rates, lines by funding source and resource, provenance); both state that the source gives no fiscal year or cut-off date | Probado | Checked with the real data at desktop and phone widths; `frontend/e2e` (flow from totals to an entity, axe-core on both pages, 404) |
| Automated interface tests (Playwright) of the core flows: header search to a record and its origin, directory filters and paging, bill to author and back, Constitution outline to an article and its neighbours, 404 for unknown records, skip link, visible focus on the header, current section in the navigation | Probado | `frontend/e2e/flows.spec.ts`; desktop and phone sizes; run against invented sample data (`backend/tests/seed_ui.py`) |
| Accessibility pass, WCAG 2.2 AA (automatic part): axe-core on 16 page types (home, search with and without results, the three directories, a record of each, Constitution outline and article, learning path and a lesson, sources, not-found) at desktop and phone sizes, plus failed requests and console errors | Probado | `frontend/e2e/a11y.spec.ts`: no violations. Manual checks on 2026-11-18: keyboard order and visible focus, reflow at 320 px without horizontal scrolling on four page types. Fixed: focus ring on the dark header was 2.0:1 against its background (now 7.1:1, WCAG 1.4.11); the skip link now moves focus into the content (`main` focusable); the navigation marks the current section (`aria-current`); favicon added |
| Deployment without a payment method (owner decision): Render free web service running web and API in one container (`deploy/render`, `render.yaml`), Neon free PostgreSQL, weekly data sync and daily backups as GitHub Actions (`sync.yml`, `backup.yml`); staff-form rate limit inside the web app keyed on Cloudflare's `True-Client-IP`; guide docs/07 | Probado (CI) | CI job `render-image` runs the container as Render does and checks pages, 404s, the panel redirect, that the API is internal, the 429 limit per IP, and reports memory use; `pnpm test:unit` tests the limiter. Not yet deployed |
| Production stack (`deploy/compose.yaml`): PostgreSQL, API, Next.js standalone server, and Caddy with automatic HTTPS, security headers and per-IP limits on POST (10 a minute on sign-in and panel, 60 elsewhere); backup, restore, sync and server setup scripts; guide for Oracle Cloud Always Free (docs/06) | Probado (CI) | CI job `deploy` builds and runs the stack and checks HTTPS, headers, 404s, panel redirect, the 429 limit, that API and database are not published, and the backup script. Not yet deployed; the Arm (aarch64) images are first built on the server |
| Reproduction from a clean workspace (2026-11-18) | Probado | Fresh clone, empty PostgreSQL 16: migrations, source registry, `python -m app.ingestion.cli all` from the live sources (entities 6,404 loaded, 0 rejected; bills 6,605 loaded, 1 rejected; Constitution 448 rows, 0 rejected), `python -m app.search.reindex` (13,393 documents), 77 backend tests, lint, types, frontend lint and build: all identical to the M3 figures |
| Representatives (Cámara, período 2026-2027) loaded into `core.person` and `core.position_holding`, with the shifted columns of the source reassigned by content (A-011) | Integrado (development database only) | Run of 2026-11-18: 362 rows seen, 181 loaded, 181 rejected as the second row of a member (kept in `core.sync_reject`); `backend/tests/test_representatives.py` |
| Links from bills to their authors among the representatives (`core.initiative_author`), exact name match only, bills filed from 2026-07-20 (A-012) | Integrado (development database only) | 302 bills, 2,325 author names, 1,753 links, 0 ambiguous; rebuilt by `python -m app.ingestion.cli all` or `python -m app.legislation.authors`; tests in `test_representatives.py` |
| Representatives API (`/api/v1/representatives`, filters, detail with contact, provenance and linked bills) and representatives in the unified search | Probado | `backend/tests/test_representatives.py` |
| Web pages "Representantes" (directory with name, constituency and party filters) and representative page (Cámara data, institutional contact, linked bills labelled "Hipótesis analítica", provenance with the column note); bill pages list linked authors | Probado | `frontend/e2e` (desktop and phone, sample data): bill to author and back, opposition seat, directory and record under axe-core, 404 for unknown representatives; checked against the real data at desktop and phone widths |
| Record pages answer HTTP 404 for unknown records | Probado | `frontend/proxy.ts` asks the API with a HEAD request (new HEAD routes on the institution, initiative and provision detail endpoints, covered in `test_records_api.py` and `test_constitution.py`) before the page renders; unknown lessons answer 404 from the lesson list. Checked against the loaded data: existing records 200, unknown or malformed identifiers 404 with `noindex`, client navigation 404; if the API is down the page still renders and says so (200) |

Module status: **Legislación**, **Instituciones** and **Observatorio** each have a first working part (Constitution explorer and bill registry; entity directory; unified search over all three). **Academia** has a first draft learning path awaiting legal review. Every other part of those modules, and the modules Recursos Públicos and Análisis Político, remain **Diseñado**. Nothing is deployed: the data above exists only in the development database of the build workspace and must be loaded again wherever the platform is installed (`python -m app.ingestion.cli all`, about one minute).

## Pending tasks

- Links between records beyond bill authors (for example from a bill to an entity); needs reliable identifiers.
- Search improvements for a later phase: related words and synonyms (semantic search, Phase 4), highlighted excerpts, date-range controls in the page (the API already accepts them).
- Scheduled synchronization (today the load is started by hand from the command line; the panel shows the results). Budget figures are monthly snapshots: earlier months stay only in the raw layer, with no page to compare them yet.
- Budget entities are not yet linked to the institutions directory (different codes; would need a matching rule like A-012) and are not in the unified search.
- Bill authors who are senators or other officials stay as text: no reliable Senate member dataset yet (S-023). Bills filed before 20 July 2026 are not linked.
- Inspect the owner's local `prototipo` folder if it contains earlier work (access not granted yet).
- Legal review of the learning path and of the Constitution explorer (A-007, A-009, A-010); name the reviewer.
- Transitory provisions of the Constitution; laws and decrees; links from a bill to the norm it would change.
- Compare the Constitution with a consolidated source with validity dates (SUIN-Juriscol) once it answers.
- Legal review: the workflow exists, but no reviewer has been named or has reviewed anything yet (A-007). A reviewer's approval of an article records that its presentation was checked; it does not yet change which wording NEXO shows as current (A-010). Accessibility: a screen-reader review (NVDA or VoiceOver) and a review by people who use assistive technology are still pending; automatic checks find only part of the problems.
- Phase 1 items not yet produced: full user-journey diagrams and detailed ER diagrams per module.

## Known issues

- SUIN-Juriscol gives an empty response (from the workspace and from a regular browser); Secretaría del Senado resets connections. Función Pública omits an intermediate certificate; NEXO supplies it (`backend/app/law/certs/README.md`).
- The Constitution edition loaded is informative, mentions reforms up to Acto Legislativo 01 de 2025, and its currency after that has not been checked. Pages say so.
- Hosts not yet allowed: Rama Judicial, Consejo de Estado, Corte Suprema, Registraduría, Imprenta Nacional, Portal de Transparencia Económica.
- Cámara "Representantes 2026-2027" dataset has misaligned columns and two rows per member; NEXO reassigns the columns and lists the second row of each member among the run's rejects (A-011). Each full load therefore reports 181 rejects.
- Author links use exact names: "Esneyder Gómez" (10 bills) is probably the representative Esneyder Gómez Salamanca but is not linked (A-012).
- Cámara "Proyectos de Ley": in 194 rows the Senate number is published with the text "No Aplica" inserted between every character. NEXO reconstructs the number only when the pattern is exact and the result looks like a bill number, keeps the published value in the raw record, and shows a note on the record page (assumption A-008). One reconstructed value was compared with the bill's page at camara.gov.co and matched; the other 193 were not checked individually.
- Bill status is the one published in the dataset (last updated by the source on 2026-09-17) and may lag behind actual proceedings.
- Search matches words and their plurals only: "educación" does not find "educativo". Results are ordered by text match alone.
- A database that already holds records must rebuild its search index once after this version is installed (`python -m app.search.reindex`), so that title matches are listed first; new loads index records as they are published.
- Per-IP limits: Caddy on the Oracle setup; the web app's own limiter on Render (in memory, one process). Local development has none. Expired sessions are not yet purged from `core.auth_session`. The application connects to PostgreSQL as the database owner, so it could truncate `core.audit_event`; a narrower application role is pending.
- Record pages for unknown identifiers now answer 404 (fixed 2026-11-18). Each record page request costs one extra lightweight HEAD request to the API. When the API is unreachable the check lets the request through, so the page shows its connection notice with status 200.

## Architectural decisions

ADR-001 modular monolith · ADR-002 PostgreSQL as single datastore · ADR-003 Next.js + FastAPI · ADR-004 append-only raw layer and versioned records · ADR-005 open-data APIs first. All **Proposed**.

## Outstanding questions

See PRD Section 9: prototype folder, legal reviewer, hosting, AI provider.

## Next recommended actions

See `05-mvp-roadmap-risks.md`, Section 4.

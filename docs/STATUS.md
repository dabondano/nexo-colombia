# NEXO Colombia — Project Status

Last updated: 2026-11-18 (M4 started: representatives and bill authors)

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
| Search box on every page and results page "Buscar" | Implementado | Builds and lints; exercised in a browser against the real data (header search, type tabs, paging, opening a record, numbers, phrases, empty and hostile input, phone width, no console errors); no automated UI tests yet |
| Web pages "Instituciones" and "Legislación": search, filters, paging, record page with the "Origen de este registro" panel; home page shows counts of loaded records with their source | Implementado | Builds and lints; exercised in a browser against the real data at desktop and phone widths (search, filters, paging, record pages, missing records, keyboard skip link, no console errors); no automated UI tests yet |
| Web shell in Spanish and "Fuentes" page reading the API | Implementado | Same manual check; no automated UI tests yet |
| Law model (`core.legal_instrument`, `core.legal_provision`, `core.provision_version`): provisions as a tree with stable keys, wording versioned (a changed wording adds a version, at most one current) | Probado | `backend/tests/test_constitution.py`, `test_migrations.py` |
| Constitution reader for Función Pública's page: preamble, titles, chapters and articles; editor's notes, wording after "TEXTO ANTERIOR" and struck-through words kept apart; stops on an unexpected structure | Probado | `backend/tests/test_constitution.py` (page with the same HTML patterns) |
| Constitution loaded into the law tables | Integrado (development database only) | Run of 2026-11-17 from the live page: 448 rows (the instrument, the preamble, 13 titles, 49 chapters, 384 articles: 1 to 380 plus 22A, 178A, 238A and 257A), 0 rejected; 73 articles marked incomplete because the source mixes in earlier or struck-through wording; a second run reported 448 unchanged |
| Law API (`/api/v1/instruments`, `/instruments/{slug}` with outline, `/instruments/{slug}/provisions/{key}`, `/provisions/{id}`), with ancestors, previous and next, and provenance | Probado | `backend/tests/test_constitution.py` |
| Articles in the unified search (wording presented as in force only; records whose title has every word come first, so "artículo 86" finds the article) | Probado | `backend/tests/test_constitution.py`, `test_search.py`; 13,393 documents in the development database |
| Web pages "Constitución" (outline with edition note and review marks) and article page (wording, notes, earlier wording and struck words shown apart, warning, neighbours, provenance) | Implementado | Builds and lints; exercised in a browser against the loaded text (outline counts, articles 11, 12 and 231, preamble, missing article, search, phone width, no console errors); no automated UI tests yet |
| First learning path "Aprender" (two lessons: how the State is organized, how a law is made; glossary and review questions), every statement labelled and linked to its articles | Implementado (draft) | Every one of the 38 links checked in a browser and resolving to the right article; **content not yet reviewed by a legally qualified person** (A-007) |
| CI workflow (backend lint, types, tests; frontend lint, build) | Integrado | `.github/workflows/ci.yml`; runs on every pull request |
| Docker Compose stack and API image | Implementado | Written but **not run**: on 2026-11-17 no Docker daemon was available; on 2026-11-18 the daemon ran but Docker Hub was not reachable from the workspace, so the `python` and `postgres` images could not be pulled |
| Reproduction from a clean workspace (2026-11-18) | Probado | Fresh clone, empty PostgreSQL 16: migrations, source registry, `python -m app.ingestion.cli all` from the live sources (entities 6,404 loaded, 0 rejected; bills 6,605 loaded, 1 rejected; Constitution 448 rows, 0 rejected), `python -m app.search.reindex` (13,393 documents), 77 backend tests, lint, types, frontend lint and build: all identical to the M3 figures |
| Representatives (Cámara, período 2026-2027) loaded into `core.person` and `core.position_holding`, with the shifted columns of the source reassigned by content (A-011) | Integrado (development database only) | Run of 2026-11-18: 362 rows seen, 181 loaded, 181 rejected as the second row of a member (kept in `core.sync_reject`); `backend/tests/test_representatives.py` |
| Links from bills to their authors among the representatives (`core.initiative_author`), exact name match only, bills filed from 2026-07-20 (A-012) | Integrado (development database only) | 302 bills, 2,325 author names, 1,753 links, 0 ambiguous; rebuilt by `python -m app.ingestion.cli all` or `python -m app.legislation.authors`; tests in `test_representatives.py` |
| Representatives API (`/api/v1/representatives`, filters, detail with contact, provenance and linked bills) and representatives in the unified search | Probado | `backend/tests/test_representatives.py` |
| Web pages "Representantes" (directory with name, constituency and party filters) and representative page (Cámara data, institutional contact, linked bills labelled "Hipótesis analítica", provenance with the column note); bill pages list linked authors | Implementado | Builds and lints; checked in a headless browser against the real data at desktop and phone widths; unknown representatives answer 404; no automated UI tests yet |
| Record pages answer HTTP 404 for unknown records | Probado | `frontend/proxy.ts` asks the API with a HEAD request (new HEAD routes on the institution, initiative and provision detail endpoints, covered in `test_records_api.py` and `test_constitution.py`) before the page renders; unknown lessons answer 404 from the lesson list. Checked against the loaded data: existing records 200, unknown or malformed identifiers 404 with `noindex`, client navigation 404; if the API is down the page still renders and says so (200) |

Module status: **Legislación**, **Instituciones** and **Observatorio** each have a first working part (Constitution explorer and bill registry; entity directory; unified search over all three). **Academia** has a first draft learning path awaiting legal review. Every other part of those modules, and the modules Recursos Públicos and Análisis Político, remain **Diseñado**. Nothing is deployed: the data above exists only in the development database of the build workspace and must be loaded again wherever the platform is installed (`python -m app.ingestion.cli all`, about one minute).

## Pending tasks

- Links between records beyond bill authors (for example from a bill to an entity); needs reliable identifiers.
- Search improvements for a later phase: related words and synonyms (semantic search, Phase 4), highlighted excerpts, date-range controls in the page (the API already accepts them).
- Scheduled synchronization (today the load is started by hand) and a sync dashboard for data stewards.
- Bill authors who are senators or other officials stay as text: no reliable Senate member dataset yet (S-023). Bills filed before 20 July 2026 are not linked.
- Inspect the owner's local `prototipo` folder if it contains earlier work (access not granted yet).
- Legal review of the learning path and of the Constitution explorer (A-007, A-009, A-010); name the reviewer.
- Transitory provisions of the Constitution; laws and decrees; links from a bill to the norm it would change.
- Compare the Constitution with a consolidated source with validity dates (SUIN-Juriscol) once it answers.
- Authentication and roles (M4); automated UI and accessibility tests.
- Phase 1 items not yet produced: full user-journey diagrams and detailed ER diagrams per module.

## Known issues

- SUIN-Juriscol gives an empty response (from the workspace and from a regular browser); Secretaría del Senado resets connections. Función Pública omits an intermediate certificate; NEXO supplies it (`backend/app/law/certs/README.md`).
- The Constitution edition loaded is informative, mentions reforms up to Acto Legislativo 01 de 2025, and its currency after that has not been checked. Pages say so.
- Hosts not yet allowed: Rama Judicial, Consejo de Estado, Corte Suprema, Registraduría, Imprenta Nacional, Portal de Transparencia Económica.
- Cámara "Representantes 2026-2027" dataset has misaligned columns and two rows per member; NEXO reassigns the columns and lists the second row of each member among the run's rejects (A-011). Each full load therefore reports 181 rejects.
- Author links use exact names: "Esneyder Gómez" (10 bills) is probably the representative Esneyder Gómez Salamanca but is not linked (A-012).
- The site has no favicon, so browsers log a 404 for `/favicon.ico`.
- Cámara "Proyectos de Ley": in 194 rows the Senate number is published with the text "No Aplica" inserted between every character. NEXO reconstructs the number only when the pattern is exact and the result looks like a bill number, keeps the published value in the raw record, and shows a note on the record page (assumption A-008). One reconstructed value was compared with the bill's page at camara.gov.co and matched; the other 193 were not checked individually.
- Bill status is the one published in the dataset (last updated by the source on 2026-09-17) and may lag behind actual proceedings.
- Search matches words and their plurals only: "educación" does not find "educativo". Results are ordered by text match alone.
- A database that already holds records must rebuild its search index once after this version is installed (`python -m app.search.reindex`), so that title matches are listed first; new loads index records as they are published.
- Record pages for unknown identifiers now answer 404 (fixed 2026-11-18). Each record page request costs one extra lightweight HEAD request to the API. When the API is unreachable the check lets the request through, so the page shows its connection notice with status 200.

## Architectural decisions

ADR-001 modular monolith · ADR-002 PostgreSQL as single datastore · ADR-003 Next.js + FastAPI · ADR-004 append-only raw layer and versioned records · ADR-005 open-data APIs first. All **Proposed**.

## Outstanding questions

See PRD Section 9: prototype folder, legal reviewer, hosting, AI provider.

## Next recommended actions

See `05-mvp-roadmap-risks.md`, Section 4.

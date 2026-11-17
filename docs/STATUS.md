# NEXO Colombia — Project Status

Last updated: 2026-11-17 (after M1)

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
| Web pages "Instituciones" and "Legislación": search, filters, paging, record page with the "Origen de este registro" panel; home page shows counts of loaded records with their source | Implementado | Builds and lints; exercised in a browser against the real data at desktop and phone widths (search, filters, paging, record pages, missing records, keyboard skip link, no console errors); no automated UI tests yet |
| Web shell in Spanish and "Fuentes" page reading the API | Implementado | Same manual check; no automated UI tests yet |
| CI workflow (backend lint, types, tests; frontend lint, build) | Integrado | `.github/workflows/ci.yml`; runs on every pull request |
| Docker Compose stack and API image | Implementado | Written but **not run**: no Docker daemon was available in the build workspace |

Module status: **Legislación** and **Instituciones** each have a first working part (bill registry; entity directory). Every other part of those modules, and the modules Academia, Recursos Públicos, Análisis Político and Observatorio, remain **Diseñado**. Nothing is deployed: the data above exists only in the development database of the build workspace and must be loaded again wherever the platform is installed (`python -m app.ingestion.cli all`, about one minute).

## Pending tasks

- M2 remainder: unified search across record types (full-text), links between records.
- Scheduled synchronization (today the load is started by hand) and a sync dashboard for data stewards.
- Link bill authors (free text in the source) to person records; needs a reliable member dataset (M4).
- Inspect the owner's local `prototipo` folder if it contains earlier work (access not granted yet).
- Confirm an official, reachable source for the Constitution text (M3).
- Authentication and roles (M4); automated UI and accessibility tests.
- Phase 1 items not yet produced: full user-journey diagrams and detailed ER diagrams per module.

## Known issues

- SUIN-Juriscol and Función Pública fail TLS verification from the workspace; Secretaría del Senado resets connections.
- Hosts not yet allowed: Rama Judicial, Consejo de Estado, Corte Suprema, Registraduría, Imprenta Nacional, Portal de Transparencia Económica.
- Cámara "Representantes 2026-2027" dataset has misaligned columns.
- Cámara "Proyectos de Ley": in 194 rows the Senate number is published with the text "No Aplica" inserted between every character. NEXO reconstructs the number only when the pattern is exact and the result looks like a bill number, keeps the published value in the raw record, and shows a note on the record page (assumption A-008). One reconstructed value was compared with the bill's page at camara.gov.co and matched; the other 193 were not checked individually.
- Bill status is the one published in the dataset (last updated by the source on 2026-09-17) and may lag behind actual proceedings.
- A record page for an unknown identifier shows "Página no encontrada" but answers with HTTP status 200, because the page shell is sent before the record is looked up. To revisit with the search work in M2.

## Architectural decisions

ADR-001 modular monolith · ADR-002 PostgreSQL as single datastore · ADR-003 Next.js + FastAPI · ADR-004 append-only raw layer and versioned records · ADR-005 open-data APIs first. All **Proposed**.

## Outstanding questions

See PRD Section 9: prototype folder, legal reviewer, hosting, AI provider.

## Next recommended actions

See `05-mvp-roadmap-risks.md`, Section 4.

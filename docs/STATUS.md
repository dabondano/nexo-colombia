# NEXO Colombia — Project Status

Last updated: 2026-11-17 (after M0)

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
| Web shell in Spanish: home page with honest project status, "Fuentes" page reading the API | Implementado | Builds and lints; checked manually in a browser at desktop and phone widths; no automated UI tests yet |
| CI workflow (backend lint, types, tests; frontend lint, build) | Implementado | `.github/workflows/ci.yml`; first run happens on the pull request |
| Docker Compose stack and API image | Implementado | Written but **not run**: no Docker daemon was available in the build workspace |

No module of the platform (Academia, Legislación, Instituciones, Recursos Públicos, Análisis Político, Observatorio) is beyond **Diseñado**. No data from any source has been ingested yet.

## Pending tasks

- M1: generic datos.gov.co connector; ingest "Universo de entidades" and "Proyectos de Ley" with field allow-lists, validation and sync reports.
- Inspect the owner's local `prototipo` folder if it contains earlier work (access not granted yet).
- Confirm an official, reachable source for the Constitution text.
- Authentication and roles (M4); automated UI and accessibility tests.
- Phase 1 items not yet produced: full user-journey diagrams and detailed ER diagrams per module.

## Known issues

- SUIN-Juriscol and Función Pública fail TLS verification from the workspace; Secretaría del Senado resets connections.
- Hosts not yet allowed: Rama Judicial, Consejo de Estado, Corte Suprema, Registraduría, Imprenta Nacional, Portal de Transparencia Económica.
- Cámara "Representantes 2026-2027" dataset has misaligned columns.

## Architectural decisions

ADR-001 modular monolith · ADR-002 PostgreSQL as single datastore · ADR-003 Next.js + FastAPI · ADR-004 append-only raw layer and versioned records · ADR-005 open-data APIs first. All **Proposed**.

## Outstanding questions

See PRD Section 9: prototype folder, legal reviewer, hosting, AI provider.

## Next recommended actions

See `05-mvp-roadmap-risks.md`, Section 4.

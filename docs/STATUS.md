# NEXO Colombia — Project Status

Last updated: 2026-11-17

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

No application code exists. No feature is beyond **Diseñado**.

## Pending tasks

- Scaffold M0 (repository created on 2026-11-17).
- Inspect the owner's local `prototipo` folder if it contains earlier work (access not granted yet).
- Confirm an official, reachable source for the Constitution text.
- Detailed API specification (OpenAPI) and SQL migrations: to be produced with M0/M1 so they are tested as written.
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

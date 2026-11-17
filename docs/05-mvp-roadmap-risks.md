# NEXO Colombia — MVP Scope, Risks and Roadmap

Version 0.1 · 2026-11-17 · Status: **Diseñado** (proposed). No dates are committed; milestones are ordered and sized relative to each other.

## 1. MVP definition

**One sentence:** a Spanish, accessible web application where a visitor can search and browse real Colombian institutions and bills, read the Constitution and a first learning path that links to those records, and see the provenance of everything shown.

### In the MVP

| # | Capability | Data | Requirement IDs |
|---|---|---|---|
| 1 | Application foundation: repository, Docker Compose, CI, migrations, settings | | NFR-07 |
| 2 | Core schema: provenance, institutions, people, positions, initiatives, instruments, provisions, budgets, relationships | | FR-DAT-03 |
| 3 | Generic datos.gov.co connector with raw snapshots, validation, field allow-lists and sync reports | | FR-DAT-02, FR-DAT-07 |
| 4 | Institution directory | Universo de entidades (6,404 entities, verified) | FR-INS-01 |
| 5 | Bills repository with filters | Proyectos de Ley, Cámara (6,606 rows, verified) | FR-LEG-01, FR-LEG-06 |
| 6 | Budget execution per entity | Ejecución PGN (verified) | FR-REC-02 (pulled forward: small and well structured) |
| 7 | Constitution explorer | Official text, once a reachable official source is confirmed | FR-ACA-02, FR-LEG-02 |
| 8 | Members of the Cámara | Representantes 2026-2027, after manual column mapping | FR-INS-02 |
| 9 | Unified search (full-text, Spanish) | All of the above | FR-OBS-01 |
| 10 | Academia: first learning path "El Estado y cómo se hace una ley", glossary, basic quiz, links to live records | Authored content, reviewed before publication | FR-ACA-01, 03, 04, 05 |
| 11 | Provenance panel, Epistemic Labels, public "Fuentes" page | | FR-PLT-03, 04; FR-DAT-01 |
| 12 | Authentication, roles, audit log | | FR-PLT-02 |
| 13 | Homepage and navigation with honest empty states | | FR-PLT-01, 05 |

### Explicitly not in the MVP

Contracts at scale (a limited labelled subset at most), voting records, simulation engine, AI assistant, jurisprudence, knowledge-graph view, workspaces, file uploads, sanctions data, Senate member directory (no official structured source found yet).

## 2. Milestones

| Milestone | Content | Done when |
|---|---|---|
| **M0 Foundation** | Repository, Compose stack, CI, base schema and migrations, health checks | CI green; stack starts from a clean clone |
| **M1 First real data** | Socrata connector; ingest entities and Cámara bills; sync reports; provenance stored | Row counts reconcile with the source; rejects are listed with reasons; tests pass |
| **M2 Browse and search** | API and pages for institutions and bills; unified search; provenance panel; Fuentes page | A visitor can find an entity or bill and open its source link |
| **M3 Law and learning** | Constitution loader and explorer; first learning path with live links; glossary; quiz | Content reviewed; every lesson link resolves |
| **M4 Accounts and trust** | Authentication, roles, audit log; budget execution; representatives; accessibility pass | Permission tests pass; no WCAG 2.2 AA blockers on core flows |
| **MVP review** | Owner review against Section 1 | Each MVP item is at least **Probado** |
| Phase 3 | Remaining connectors, SECOP at scale, file ingestion, entity resolution, quality monitoring | |
| Phase 4 | Semantic search, RAG assistant with evaluation suite, graph view, workspaces, version comparison, jurisprudence | |
| Phase 5 | Procurement analysis, voting records, affiliation history, relationship mapping, simulation engine | |
| Phase 6 | Hardening, security and accessibility testing, deployment, backup validation | |

Dependencies: M1 needs the repository; M3 needs a reachable official source for the Constitution; M4 needs a decision on the member data mapping; Phase 4 needs an AI provider decision; Phase 5 sanctions features need the legal review.

## 3. Risk register

Likelihood and impact: High / Medium / Low.

| ID | Risk | Type | L | I | Mitigation |
|---|---|---|---|---|---|
| R-01 | Legal texts, gacetas and jurisprudence have no structured API, so coverage depends on fragile HTML/PDF extraction | Technical / data | H | H | Start with APIs; build scraping per source with tests on saved snapshots; show coverage limits openly |
| R-02 | Official datasets contain errors, placeholders and misaligned columns (seen in the Cámara datasets) | Data quality | H | M | Validation in staging, reject reports, data-quality status, manual mapping documented per source |
| R-03 | Publishing personal data that sources expose (ID numbers, bank accounts, contact details) | Legal / privacy | M | H | Field allow-lists at ingestion; restricted schema; privacy review before each new source; Ley 1581 compliance notes per field |
| R-04 | Reputational or legal harm from implying wrongdoing (name matches, sanctions data, relationship graphs) | Legal / ethical | M | H | Identifier-based matching only; confidence classes; procedural-stage vocabulary; sanctions excluded until legal review; neutral wording review |
| R-05 | Voting data is partial: Senate individual votes only 2017–2024 with Sí/No values; no Cámara dataset found | Data | H | M | Store aggregates and availability flags; never infer individual votes; label coverage |
| R-06 | Simulation rules encoded incorrectly (wrong quorum or majority for a type of law) | Legal accuracy | M | H | Each rule cites its provision and needs a recorded verification by a legal reviewer before activation; unit tests per rule |
| R-07 | AI assistant fabricates or mis-cites | Technical / trust | M | H | Retrieval-only answers; citation verification step; evaluation suite; clear "informativa" notice |
| R-08 | Source sites block, change structure or have TLS problems (already seen with SUIN-Juriscol, Función Pública, Secretaría del Senado) | Operational | H | M | Monitoring per source; raw snapshots; alternative official sources; no bypass of restrictions or certificate checks |
| R-09 | Licence obligations (CC BY-SA 4.0 on datos.gov.co datasets) not met in exports or reuse | Legal | M | M | Attribution on every record and export; licence stored per source; review of share-alike implications |
| R-10 | Scope is very large for the available capacity | Project | H | H | Strict phase gates; MVP limited to verified sources; status reported with the five-stage scale |
| R-11 | Work kept only in a temporary workspace could be lost | Operational | L | H | Repository created on 2026-11-17; commit and push after each work session |
| R-12 | Perceived political bias in content or data selection | Reputational | M | H | Neutrality checklist for lessons and UI copy; symmetric treatment of all parties; published methodology |
| R-13 | Volume: SECOP tables have millions of rows | Technical | M | M | Incremental loads, partitioning by year, start with a subset |
| R-14 | Educational content contains legal inaccuracies | Legal accuracy | M | H | Every lesson cites provisions; review by a qualified person before publication; "last reviewed" date shown |

## 4. Next actions

1. Owner: confirm whether the `prototipo` folder holds earlier work.
2. Review these Phase 1 documents and answer the open questions in the PRD (legal reviewer, hosting, AI provider).
3. Build M0 and M1 as soon as the repository exists.
4. Find a reachable official source for the Constitution text, and request network access for the remaining hosts when each connector is started.

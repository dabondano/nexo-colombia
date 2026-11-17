# NEXO Colombia — Product Requirements Document

Version 0.1 · 2026-11-17 · Status: **Diseñado** (proposed, awaiting owner review)

## 1. Product summary

NEXO Colombia ("Sistema de Conocimiento e Inteligencia Pública") is a web platform that lets people learn how the Colombian State works and research what it does, with every displayed fact traceable to its source. It joins six modules (Academia, Legislación, Instituciones, Recursos Públicos, Análisis Político, Observatorio) over one shared database, so that a lesson, a law, an official, a contract and a vote are all linked records.

**Problem.** Colombian public information is abundant but scattered across dozens of portals with different formats, uneven quality and no links between them. A citizen cannot easily go from "what is a statutory law" to "which ones are in Congress now", or from a ministry to its budget and contracts.

**Product principles** (from the master brief, Section 2): Epistemic Labels on every statement; Checkable Claims; political neutrality; privacy by design (Ley 1581 de 2012); honest status reporting.

## 2. Goals and non-goals

| Goals | Non-goals (for now) |
|---|---|
| G1. Teach the constitutional, political, administrative, electoral and judicial systems interactively | Regional or comparative coverage beyond Colombia |
| G2. Provide searchable legal and legislative research with citations | Legal advice or conceptos jurídicos |
| G3. Provide a directory of institutions and officials with history | Predicting how officials will vote |
| G4. Make procurement and budget data explorable | Accusing or scoring individuals |
| G5. Connect everything in a navigable knowledge graph | Collecting data behind logins or access controls |
| G6. Keep provenance and data-quality status visible for every record | Claiming complete coverage |

## 3. Users

A. Citizens · B. Legal professionals · C. Journalists and investigative researchers · D. Academics and students · E. Data analysts · F. Public-sector researchers. Newcomers get guided entry points; experts get advanced search, exports and the graph.

## 4. Functional requirements

Priority: **MVP** (Phase 2), **P3**, **P4**, **P5** (later phases). IDs are stable references for tests and status reports.

### Platform (cross-cutting)

| ID | Requirement | Priority |
|---|---|---|
| FR-PLT-01 | Spanish-first interface with the seven-item navigation (Inicio, Academia, Legislación, Instituciones, Recursos Públicos, Análisis Político, Observatorio) and global search on every page | MVP |
| FR-PLT-02 | Authentication, role-based access (visitor, registered user, editor, data steward, administrator), server-side permission checks | MVP |
| FR-PLT-03 | Every record page shows provenance: source, link, acquisition date, last verification, data-quality status | MVP |
| FR-PLT-04 | Every statement type carries its Epistemic Label in the data and in the UI | MVP |
| FR-PLT-05 | Homepage shows only real data with provenance, or honest empty states | MVP |
| FR-PLT-06 | English interface on request | P4 |

### Module 01 — Academia

| ID | Requirement | Priority |
|---|---|---|
| FR-ACA-01 | Courses and lessons organized in learning paths (Constitution, State structure, legislative process, electoral system, judicial system, public administration) | MVP (first path: State structure and legislative process) |
| FR-ACA-02 | Constitution explorer: navigate titles, chapters and articles; link articles to institutions and norms | MVP |
| FR-ACA-03 | Lessons link to live records (a lesson on the Cámara links to current representatives, commissions, bills) | MVP |
| FR-ACA-04 | Glossary of legal and institutional terms | MVP |
| FR-ACA-05 | Quizzes and practical exercises | MVP (basic), P4 (full) |
| FR-ACA-06 | Interactive organizational charts and institutional maps | P3 |
| FR-ACA-07 | Legislative-process and electoral-formula simulators, timelines, comparison charts, case studies | P5 |

### Module 02 — Legislación

| ID | Requirement | Priority |
|---|---|---|
| FR-LEG-01 | Repository of legislative initiatives with number, period, title, summary, authors, commissions, status, links | MVP (Cámara dataset) |
| FR-LEG-02 | Repository of legal instruments by type and hierarchy, with article-level provisions | MVP (Constitution + a small verified set of laws) |
| FR-LEG-03 | Full procedural history per initiative: debates, amendments, reports, votes, outcome | P3 |
| FR-LEG-04 | Version history of norms and side-by-side comparison | P4 |
| FR-LEG-05 | Jurisprudence repository with structured extraction | P4 |
| FR-LEG-06 | Advanced search: full-text, by provision, institution, author, date, subject, status, hierarchy, citation; semantic and cross-document | MVP (full-text + filters), P4 (semantic) |
| FR-LEG-07 | AI legal assistant answering only from retrieved documents in the Legal Answer format | P4 |

### Module 03 — Instituciones

| ID | Requirement | Priority |
|---|---|---|
| FR-INS-01 | Directory of public entities (national and territorial) with sector, order, legal nature | MVP (Universo de entidades) |
| FR-INS-02 | Official profiles with position, institution, party, constituency, dates, sources | MVP (members of Congress where an official source exists) |
| FR-INS-03 | Historical positions and affiliations with validity dates; "who held this office on date X" | MVP (data model), P3 (history load) |
| FR-INS-04 | Relationship mapping with source, date, type and confidence class | P4 |
| FR-INS-05 | Sanctions and investigations with procedural stage and source | P5, after legal review |

### Module 04 — Recursos Públicos

| ID | Requirement | Priority |
|---|---|---|
| FR-REC-01 | Searchable contract records (SECOP II first), linked to contracting entities | P3 (a labelled, limited real subset may appear in the MVP) |
| FR-REC-02 | Budget execution by sector and entity, keeping appropriation, commitments, obligations and payments distinct | P3 |
| FR-REC-03 | Contractor and corporate relationships matched by official identifiers (NIT), never by name alone | P5 |
| FR-REC-04 | Analysis views: distributions, timelines, concentration, entity comparison, maps | P5 |

### Module 05 — Análisis Político

| ID | Requirement | Priority |
|---|---|---|
| FR-POL-01 | Party, caucus, coalition and opposition records with validity dates | P3 |
| FR-POL-02 | Voting records; individual votes only where the source provides them | P5 (Senate plenary 2017–2024 dataset available) |
| FR-POL-03 | Affinity analysis with visible, adjustable assumptions | P5 |
| FR-POL-04 | Legislative simulation engine applying the rule for each procedure, with the seven-point Simulation Result | P5 |
| FR-POL-05 | All simulation output labelled "Simulación hipotética"; no unsupported probabilities | P5 |

### Module 06 — Observatorio

| ID | Requirement | Priority |
|---|---|---|
| FR-OBS-01 | Unified search across all record types with filters, date ranges and entity types | MVP |
| FR-OBS-02 | Navigation from any record to its related records | MVP (direct links), P4 (graph view) |
| FR-OBS-03 | Research workspaces: saved searches, bookmarks, collections, notes, sharing, exports | P4 |
| FR-OBS-04 | AI research assistant across modules, with citations and labels | P4 |

### Data infrastructure

| ID | Requirement | Priority |
|---|---|---|
| FR-DAT-01 | Source registry with verification status | MVP |
| FR-DAT-02 | Connectors for datos.gov.co datasets with incremental sync, change detection, retries, monitoring | MVP (first connectors), P3 (all) |
| FR-DAT-03 | Raw snapshot retention and versioned canonical records; nothing overwritten silently | MVP |
| FR-DAT-04 | File ingestion (CSV, XLSX, XLS, JSON, XML, PDF, DOCX) with validation, mapping, preview, report, history, rollback | P3 (CSV/XLSX/JSON first) |
| FR-DAT-05 | Entity resolution and duplicate detection | P3 |
| FR-DAT-06 | Data-quality indicator per record from documented criteria | P3 |
| FR-DAT-07 | Personal-data filter at ingestion (field allow-list per source) | MVP |

## 5. Non-functional requirements

| ID | Requirement |
|---|---|
| NFR-01 Accessibility | WCAG 2.2 AA: keyboard, screen readers, semantic HTML, contrast, responsive layouts, clear errors |
| NFR-02 Security | Server-side authorization on every endpoint; input validation; output encoding; rate limiting; audit logs; secure file handling; protections against SQL injection, XSS and CSRF; secrets outside the repository |
| NFR-03 Privacy | Ley 1581 de 2012: data minimization, public-interest classification per field, no private contact details or ID numbers of natural persons in public views |
| NFR-04 Traceability | 100% of public records have provenance; every relationship has source, date, type, confidence class |
| NFR-05 Reliability | Daily backups; tested restore; sync failures alert and never corrupt canonical data |
| NFR-06 Performance | Search results in under 2 seconds at the 95th percentile on the MVP dataset (target to confirm with measurement) |
| NFR-07 Maintainability | Modular code, typed interfaces, automated tests for critical paths, migrations, CI |
| NFR-08 Neutrality | No ranking, scoring or wording that favours or disfavours any party or person; reviewed in UI copy and AI prompts |
| NFR-09 Portability | AI provider abstraction; jurisdiction kept as an explicit attribute for future expansion |
| NFR-10 Honesty of status | Features reported only as Diseñado, Implementado, Probado, Integrado or Desplegado |

## 6. User stories (selected)

| # | As a… | I want… | So that… | Acceptance check |
|---|---|---|---|---|
| US-01 | Citizen | to read a lesson on how a bill becomes law and open real bills at each stage | I understand the process with real examples | Lesson links resolve to initiative records with provenance |
| US-02 | Citizen | to search "Ministerio de Salud" and see what it is, who leads it, its sector and budget execution | I understand one institution in one place | Entity page shows directory data and, when loaded, budget rows, each with source |
| US-03 | Law student | to open an article of the Constitution and see linked norms and institutions | I can study it in context | Article page lists links with their Epistemic Label |
| US-04 | Journalist | to filter bills by author, commission, status and legislature | I can follow a topic | Filters return matching records from the Cámara dataset; placeholder rows are excluded and logged |
| US-05 | Journalist | to see how a senator voted on a recorded vote, or a clear note when only totals exist | I never report an invented vote | Individual votes appear only from sources that list them |
| US-06 | Analyst | to download search results as CSV with source columns | I can analyse them elsewhere | Export includes source URL and acquisition date per row |
| US-07 | Researcher | to see who held an office on a given date | I can reconstruct the context of a decision | Temporal query returns the position record valid on that date |
| US-08 | Data steward | to see each source's last sync, row counts and errors | I can trust or fix the pipeline | Source dashboard shows status per connector |
| US-09 | Any user | to see where every fact comes from and how reliable it is | I can verify it myself | Provenance panel on every record |
| US-10 | Administrator | to grant roles and review an audit log | access stays controlled | Role change is enforced server-side and logged |

## 7. User journeys

1. **Learn, then verify (citizen).** Inicio → Academia → "Cómo se hace una ley" → step "Primer debate" → link to bills currently in commission → a bill's page → its source on the Cámara site.
2. **Follow the institution (journalist).** Global search "Ministerio…" → entity page → budget execution (appropriation vs payments) → contracts by that entity → one contract → its SECOP process page.
3. **Study a norm (law student).** Legislación → Constitution → an article → linked statutory law → its legislative initiative → authors' profiles.
4. **Check the pipeline (data steward).** Sign in → Sources → SECOP II connector → last sync and rejected rows → validation report.

## 8. Success measures (to refine with the owner)

- Share of public records with complete provenance: 100%.
- Share of MVP data from real, verified sources versus labelled samples: reported on the homepage.
- Accessibility audit: zero WCAG 2.2 AA blockers on core flows.
- Evaluation suite for the AI assistant (Phase 4): agreed thresholds for citation correctness and correct labelling.

## 9. Open questions for the owner

1. Is there earlier work in the `prototipo` folder that should be kept?
2. Who is the legal reviewer for privacy and for publishing sanctions data?
3. Hosting preference and budget (this drives deployment choices in Phase 6).
4. Which AI provider(s) should the first implementation use?

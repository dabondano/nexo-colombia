# NEXO Colombia — Assumptions Register

### Assumption A-001
- Assumption: NEXO is a new project with no existing code to preserve.
- Reason: the workspace and shared folder contain no code and no repository is connected · Impact if wrong: design choices may conflict with the existing prototype and need rework.
- Owner/verification: owner confirms the contents of the local `prototipo` folder; to be checked before M0.

### Assumption A-002
- Assumption: the reference stack from the brief (Next.js, FastAPI, PostgreSQL, Redis, Docker) is acceptable.
- Reason: it fits the requirements and the tooling is already installed · Impact if wrong: ADR-003 is revised before code is written; low cost now.
- Owner/verification: owner review of `02-architecture.md`.

### Assumption A-003
- Assumption: datos.gov.co datasets may be reused with attribution under CC BY-SA 4.0, as stated in each dataset's metadata.
- Reason: licence field returned by the API on 2026-11-17 · Impact if wrong: export and reuse terms must change.
- Owner/verification: legal reviewer confirms share-alike implications before public launch.

### Assumption A-004
- Assumption: personal identifiers found in open datasets (document numbers of natural persons, bank accounts, private contact details) are not published by NEXO even though the source publishes them.
- Reason: data minimization under Ley 1581 de 2012 and the brief's privacy baseline · Impact if wrong: some matching and research features would be richer; none are blocked.
- Owner/verification: legal reviewer; revisit per source.

### Assumption A-005
- Assumption: sanctions and disciplinary records (for example Procuraduría SIRI) stay out of scope until a legal review.
- Reason: high risk of harm to individuals; the brief requires procedural context and precise status · Impact if wrong: Module 03 profile completeness is delayed.
- Owner/verification: legal reviewer, before Phase 5.

### Assumption A-006
- Assumption: Spanish is the only interface language for the MVP; English follows in Phase 4.
- Reason: Spanish is the stated default; English is "on request" · Impact if wrong: i18n work moves earlier.
- Owner/verification: owner review of the PRD.

### Assumption A-007
- Assumption: educational content is drafted by the engineering lead and published only after review by a legally qualified person.
- Reason: legal precision requirement · Impact if wrong: lessons could contain inaccuracies.
- Owner/verification: owner names the reviewer (PRD open question 2).

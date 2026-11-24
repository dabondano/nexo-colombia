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
- Owner/verification: owner names the reviewer (PRD open question 2). Since 2026-11-18 the review is recorded in the staff panel (role "Revisión jurídica"); each approval applies only to the exact content reviewed, and public pages show the date of approval, never the reviewer's name or notes.

### Assumption A-008
- Assumption: when the Cámara bills dataset publishes a Senate number with the text "No Aplica" inserted before, after and between every character, removing that text gives the number the source intended (for example "068/2012 S").
- Reason: the pattern is exact in all 194 affected rows and every result has the form of a bill number; one case (Cámara 343/2013 C) was compared with the bill's page at camara.gov.co on 2026-11-17 and matched · Impact if wrong: a Senate number shown for some of those bills would be incorrect; the published value is kept in the raw record and the record page states that the number was reconstructed.
- Owner/verification: data steward; sample more rows against camara.gov.co, and report the defect to the Cámara.

### Assumption A-009
- Assumption: the Constitution's titles and first chapters that Función Pública's page prints without their label ("TÍTULO II", "CAPÍTULO 1") can be numbered by their order on the page.
- Reason: the page prints every title name in order and the reader stops if a printed label ("TÍTULO XII") does not match the deduced count, or if the page does not end with thirteen titles; the outline was compared with the Senate's 2005 edition, which differs only in the two omissions listed for source S-024 · Impact if wrong: a division would carry the wrong number; each deduced number is declared on its record.
- Owner/verification: legal reviewer, while reviewing the explorer.

### Assumption A-010
- Assumption: in Función Pública's edition, wording printed after the mark "TEXTO ANTERIOR" in an article cannot be safely classified as earlier or current wording.
- Reason: the page marks where earlier wording begins but not where it ends, and in some articles current paragraphs follow it · Impact if wrong: none for accuracy, since NEXO shows that part apart with a warning and leaves it out of search; the cost is that 73 articles are marked "Requiere revisión".
- Owner/verification: legal reviewer; a consolidated source with validity dates (SUIN-Juriscol) would remove the need.

### Assumption A-011
- Assumption: in the Cámara representatives dataset (S-010) each column holds the value named by the next column, and the two rows published for each member describe the same member, the more complete one being correct.
- Reason: checked on all 362 rows on 2026-11-18: every "circunscripcion" value is an e-mail, every "_" value is a name, the 181 pairs differ only by added fields · Impact if wrong: a value could appear under the wrong heading. A row in any other layout is rejected instead of being guessed, and every record says the columns were reassigned.
- Owner/verification: data steward; report the defect to the Cámara and re-check when the dataset changes.

### Assumption A-012
- Assumption: a bill author whose published name matches exactly (ignoring case, accents and punctuation) the name of exactly one representative of the 2026-2027 list, on a bill filed from 20 July 2026, is that representative.
- Reason: rule chosen by the owner on 2026-11-18; the source does not identify authors. On the first run 1,753 of 2,325 author names on 302 bills were linked, none was ambiguous, and only one probable shortened name ("Esneyder Gómez", 10 bills) was left unlinked · Impact if wrong: a bill could be shown under the wrong person. Links are labelled "Hipótesis analítica" and the published text is always shown.
- Owner/verification: data steward; sample links against the bills' pages at camara.gov.co.

### Assumption A-013
- Assumption: the budget figures of MinHacienda's dataset (S-005, `xjxk-qhsc`) can be shown without a fiscal year, and execution rates (commitments, obligations and payments divided by the current appropriation) describe progress without judging an entity.
- Reason: owner decisions of 2026-11-18: state only what the source publishes (pages say the source does not give the year or cut-off date, and show its update date); show amounts and rates with the formula, alphabetical lists, no rankings. The one-line meanings of commitments, obligations and payments are general explanations of the budget stages, not legal definitions · Impact if wrong: readers could compare figures from different cut-off dates; each record shows the source's update date.
- Owner/verification: data steward; legal reviewer for the wording of the stage explanations.

### Assumption A-014
- Assumption: a budget entity of the PGN (S-005) and an entity of Función Pública's directory are the same body when their names are equal after removing case, accents, punctuation and extra spaces, and exactly one directory entry has that name.
- Reason: the two sources share no identifier (the budget has a budget code and no NIT; the directory has neither). Same strictness the owner chose for bill authors (A-012). Measured on 2026-11-24: 44 of 221 budget entities linked, 0 ambiguous. Dropping suffixes such as " - GESTIÓN GENERAL" would add 7 links but also map distinct bodies (the regulator CREG onto the Ministry of Mines), so it was rejected · Impact if wrong: a page could point to the wrong body; every link is labelled "Hipótesis analítica" with the rule shown, and links are rebuilt on every load.
- Owner/verification: data steward; a reviewed mapping table would replace the rule for unlinked entities.

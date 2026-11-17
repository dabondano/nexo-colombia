# NEXO Colombia — Technical Assessment (Phase 0)

Date: 2026-11-17 · Status of this document: complete for what could be inspected; three items are blocked and listed under Constraints.

## Technical Assessment

### Summary

NEXO Colombia is treated as a **new project** for now. The cloud workspace is empty and no GitHub repository is connected. A folder named `prototipo` exists on the owner's computer, but it could not be opened in this session, so whether earlier NEXO work exists there is **not verified**. The development tooling needed for the reference architecture is already installed. Network access to the national open-data portal was opened during this phase, and several official datasets were verified live.

### Current state

| Item | Finding | Evidence |
|---|---|---|
| Codebase | None in the workspace | `/home/user` is empty and is not a git repository (`ls -la`) |
| Shared project folder | Contains only the prompt files | `/mnt/project-files/nexo-prompt/` |
| GitHub | No account linked at the time of the assessment; the repository was created afterwards | Repository listing returned "no GitHub account linked" |
| Local folders | A folder named `prototipo` exists on the owner's computer | Device listing; not approved for this session |
| Tooling | Node 22.23, npm 10.9, pnpm 10.28, Python 3.13, uv 0.11, Docker 29.9, PostgreSQL client 16.15, git 2.43 | `--version` of each tool |
| Machine | 4 CPUs, 15 GB RAM, about 31 GB free disk | `nproc`, `free`, `df` |
| Browser automation | Chromium and Playwright preinstalled | Environment documentation |

### Gaps

Everything in the specification is still to be built: application foundation, database, ingestion, search, the six modules, AI layer, tests, CI and documentation. Status of every feature: not yet **Diseñado**, except the design documents produced in Phase 1.

### Constraints

1. **Network (partly resolved).** The workspace network policy is "limited". At the start, requests to `www.datos.gov.co` were refused by the network proxy (HTTP 403 on CONNECT). Eight official hosts were then added to the allow-list with the owner's approval. Result: datos.gov.co, Corte Constitucional, Senado, Cámara and Colombia Compra Eficiente now respond. SUIN-Juriscol and Función Pública fail TLS certificate verification from this workspace (`curl: (60) unable to get local issuer certificate`, which points to an incomplete certificate chain on their servers), and Secretaría del Senado resets the connection. These three need a fix that keeps certificate verification on. Other hosts (Rama Judicial, Consejo de Estado, Corte Suprema, Registraduría, Imprenta Nacional, Portal de Transparencia Económica) are still not allowed.
2. **Prototype folder (unverified).** The request to open the `prototipo` folder was denied automatically. If it holds earlier NEXO work, it must be reviewed before any design is finalized (Rule 1: inspect before acting).
3. **Repository (blocking for durable code).** The workspace is temporary. Code needs a GitHub repository to persist; this session cannot create one.
4. **Legal and privacy.** Ley 1581 de 2012 applies to personal data even when published. This is concrete, not theoretical: the official SECOP II contracts dataset includes contractors' ID numbers (`documento_proveedor`), legal representatives' ID numbers and gender, and bank account numbers (`n_mero_de_cuenta`); the Cámara dataset includes e-mail addresses and phone extensions. NEXO must filter these at ingestion (data minimization).

### Integrations

All rows below were **verified on 2026-11-17** by calling the datos.gov.co API from the workspace (dataset metadata, row count and sample rows), unless marked otherwise. Licence for all listed datasets: CC BY-SA 4.0. Details: [04-source-registry.md](04-source-registry.md).

| Domain | Dataset (ID) | Rows | Data last updated | Notes |
|---|---|---|---|---|
| Procurement | SECOP II – Contratos Electrónicos (`jbjy-vk9h`) | 5,717,409 | 2026-11-16 | 95 columns; distinguishes contract value, invoiced, paid and pending amounts; contains personal data to exclude |
| Procurement | SECOP II – Procesos de Contratación (`p6dx-8zbt`) | 9,047,771 | 2026-11-16 | Processes, including those without a contract |
| Procurement | SECOP I – Procesos de Compra Pública (`f789-7hwg`); SECOP Integrado (`rpmr-utcd`) | count timed out | 2026-11-16 | Very large; must be loaded incrementally |
| Procurement | SECOP II – Multas y Sanciones (`it5q-hg94`) | 586 | 2026-11-16 | |
| Budget | Ejecución Presupuestal del PGN (`xjxk-qhsc`); detailed by item (`bpij-5vy9`) | 600; 3,856 | 2026-11-07 | Has the four distinct amounts: apropiación vigente, compromisos, obligaciones, pagos |
| Institutions | Universo de entidades, Función Pública (`h7zv-k39x`) | 6,404 | 2026-10-09 | 304 national and 6,100 territorial entities, with NIT, sector, legal nature |
| Officials | Conjunto servidores públicos, Función Pública (`2jzx-383z`) | 272,228 | 2026-10-20 | Anonymous records (no names): useful for statistics, not for profiles |
| Bills | Proyectos de Ley, Cámara (`kcxp-nxum`) | 6,606 | 2026-09-17 | Covers legislatures through 2026-2027; number, title, type of law, authors, status, commission, link. Contains placeholder rows (for example "FALLA EN EL APLICATIVO") |
| Bills | Proyectos de ley del Senado (`feim-cysj`) | 2,274 | 2023-12-07 | Stale |
| Votes | Votaciones plenaria Senado (`ucmr-52df`) | 16,733 | 2024-10-29 | Individual votes, 2017-02-14 to 2024-09-25; only Sí/No (no abstentions or absences); bill identified by free text. No Cámara equivalent found |
| Congress members | Representantes período 2026-2027 (`5pt5-nxdp`) | 362 | 2026-11-11 | Column headers are misaligned with their contents (the "partido" column holds legal citations or party, "circunscripción" holds e-mail). Needs careful mapping. No Senate equivalent found |
| Sanctions | Antecedentes de SIRI, Procuraduría (`iaeu-rcn6`) | 42,070 | 2026-11-16 | Named individuals with ID numbers and sanctions: highly sensitive; out of MVP scope until a legal review |
| Elections | Resultados electorales 2018 Senado (`75f2-fe2s`) | 5,191,659 | 2021-03-15 | Table-level results for 2018 only; 2022 and 2026 not found on the portal |

Other findings:

- **Corte Constitucional**: reachable; its robots.txt explicitly allows `/relatoria/`. Structure of the relatoría not yet examined (**not verified**).
- **Senado**: its transparency page offers no structured downloads for bills, votes or senators; bills are consulted at `leyes.senado.gov.co` and Gacetas at the Imprenta Nacional (verified by reading the page).
- **Open Contracting (OCDS) publication**: covers 2011 to April 2022 and is no longer updated (verified). Historical use only.
- **Congreso Visible (Universidad de los Andes)**: hosts bill documents through 2026; API and terms of use **not verified**. It is a secondary source (tier 5).
- **Función Pública website**: its information inventory page disallows automated access; use its datos.gov.co datasets instead (verified).
- **Not yet verified**: SUIN-Juriscol, Diario Oficial, Consejo de Estado, Corte Suprema, Rama Judicial, Registraduría (2022 and 2026 results), CNE, Portal de Transparencia Económica, Contraloría, Fiscalía, Defensoría.

Conclusion: the national open-data portal gives NEXO a confirmed, structured, mostly current base for procurement, budget execution, the entity directory and Cámara bills. Legal texts, jurisprudence, Senate bills after 2023, Cámara votes and full debate histories will require document extraction from official sites.

### Security findings

No code exists, so there are no code findings. Two design-level points: the prompt files are the only shared assets and contain no secrets; and AI provider keys, when introduced, must be stored as environment secrets, never in the repository.

### Recommendation

1. Proceed to Phase 1 (requirements and design) immediately; it does not depend on the blocked items.
2. Unblock in parallel: connect GitHub with an empty repository, confirm whether `prototipo` contains earlier work, and resolve access to SUIN-Juriscol, Función Pública and Secretaría del Senado.
3. Start the MVP data work with the verified datos.gov.co datasets (entities, Cámara bills, budget execution, SECOP II) and the Constitution text, because they are the lowest-risk real sources.

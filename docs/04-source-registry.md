# NEXO Colombia — Source Registry (initial)

Verification method for all "Verified" entries: on 2026-11-17 the dataset's metadata (`/api/views/{id}.json`), row count (`$select=count(*)`) and sample rows were requested from the datos.gov.co API (Socrata SODA) from the project workspace. Row counts and dates are as returned that day. Reliability class refers to the source hierarchy in the master brief (Section 11.1).

Common properties of datos.gov.co datasets: API endpoint `https://www.datos.gov.co/resource/{id}.json`; exports in CSV, JSON, XML; licence CC BY-SA 4.0 (attribution and share-alike apply to NEXO's reuse); robots.txt sets `Crawl-delay: 1` and does not disallow `/resource/` or `/api/views/`.

## A. Verified sources (structured, official)

### Source S-001: SECOP II – Contratos Electrónicos
- Institution: Agencia Nacional de Contratación Pública – Colombia Compra Eficiente · ID `jbjy-vk9h` · Category: procurement · Data types: contracts
- Acquisition method: API · Update frequency: daily (per CCE manual) · Data last updated: 2026-11-16 · Rows: 5,717,409 · Reliability class: 3 (official database)
- Key fields: `id_contrato`, `nombre_entidad`, `nit_entidad`, `orden`, `sector`, `rama`, `proceso_de_compra`, `estado_contrato`, `tipo_de_contrato`, `modalidad_de_contratacion`, `fecha_de_firma`, `fecha_de_inicio_del_contrato`, `fecha_de_fin_del_contrato`, `proveedor_adjudicado`, `tipodocproveedor`, `documento_proveedor`, `valor_del_contrato`, `valor_facturado`, `valor_pagado`, `valor_pendiente_de_pago`, `valor_pendiente_de_ejecucion`, `origen_de_los_recursos`, funding-source columns (PGN, SGP, regalías, own resources, credit), `urlproceso`, `ultima_actualizacion`
- Known limitations: entities are responsible for accuracy (CCE manual); atypical values must be checked against process documents via `urlproceso`
- Access restrictions: **contains personal data** (natural-person ID numbers, legal-representative ID and gender, bank name and account number, names and IDs of spending officers and supervisors). NEXO ingests none of the bank fields and no ID numbers of natural persons into public tables
- Verification status: Verified on 2026-11-17 by API
- In NEXO since 2026-11-24 (A-015): national-order contracts signed in the last 90 days; 32 named fields requested with `$select` (no officials, legal representatives or bank fields); supplier name and number kept only when the supplier's document type is NIT. Checked in scope: payments never exceed invoices or value; one row with invoices above value; 860 with value 0.

### Source S-002: SECOP II – Procesos de Contratación
- ID `p6dx-8zbt` · Rows: 9,047,771 · Data last updated: 2026-11-16 · Category: procurement processes (including processes without a contract, invited suppliers, base price, phases)
- Verification status: Verified on 2026-11-17 by API

### Source S-003: SECOP I – Procesos de Compra Pública / SECOP Integrado
- IDs `f789-7hwg` (SECOP I), `qddk-cgux` (SECOP I histórico), `rpmr-utcd` (integrated SECOP I + II) · Data last updated: 2026-11-16
- Known limitations: the count query timed out (very large tables); load incrementally by date
- Verification status: metadata Verified on 2026-11-17; row counts not obtained

### Source S-004: SECOP II – related tables
- `cb9c-h8sn` Adiciones · `mfmm-jqmq` Ejecución Contratos · `cwhv-7fnp` Rubros Presupuestales · `qmzu-gj57` Proveedores Registrados · `gra4-pcp2` Ubicaciones ejecución · `it5q-hg94` Multas y Sanciones (586 rows) · `tauh-5jvn` SECOP I Proponentes · `4n4q-k399` Multas y Sanciones SECOP I
- Verification status: listed in the portal catalogue on 2026-11-17; only `it5q-hg94` inspected in detail

### Source S-005: Ejecución Presupuestal del Presupuesto General de la Nación
- Institution: Ministerio de Hacienda y Crédito Público · IDs `xjxk-qhsc` (by entity, 600 rows) and `bpij-5vy9` (by budget item, 3,856 rows) · Data last updated: 2026-11-07
- Key fields: sector, entity code and name, `apropiaci_n_vigente`, `compromisos`, `obligaciones`, `pagos`
- Known limitations: no column for the fiscal year (vigencia) or the cut-off date, only the dataset's update date (monthly); each update replaces the previous figures; historical series not yet located. Labels contain non-breaking spaces
- Verification status: Verified on 2026-11-17 by API; `xjxk-qhsc` profiled in full on 2026-11-18 (600 rows, 221 entities, unique by entity code, funding source, funds situation and resource; whole pesos, none negative; payments ≤ obligations ≤ commitments ≤ appropriation in every row; total appropriation $543.2 billones) and loaded

### Source S-006: Universo de entidades
- Institution: Departamento Administrativo de la Función Pública · ID `h7zv-k39x` · Rows: 6,404 (304 national, 6,100 territorial) · Data last updated: 2026-10-09
- Key fields: institution code, name, NIT, order, sub-order, level, organic classification, sector, legal nature, type, municipality, department, website, coordinates, status, representative's name and position
- Access restrictions: includes institutional e-mail, phone and address (institutional contact data, acceptable to publish; the representative's name is public-office information)
- Verification status: Verified on 2026-11-17 by API

### Source S-007: Conjunto servidores públicos
- Institution: Función Pública (SIGEP) · ID `2jzx-383z` · Rows: 272,228 · Data last updated: 2026-10-20
- Key fields: sex, birthplace, months of experience, education level, entity, type of appointment, hierarchical level, job title, base salary, start date. **No names.**
- Use: aggregate statistics for Academia and Instituciones; cannot build individual profiles
- Verification status: Verified on 2026-11-17 by API

### Source S-008: Proyectos de Ley (Cámara de Representantes)
- ID `kcxp-nxum` · Rows: 6,606 · Data last updated: 2026-09-17 · Legislatures through 2026-2027 (302 rows for 2026-2027; 579 for 2025-2026)
- Key fields: Cámara and Senado numbers and dates, title, purpose, type of law, authors, status, origin, commission, legislature, link to the Cámara page
- Known limitations: free-text authors; placeholder rows exist (one row reads "FALLA EN EL APLICATIVO"); "No Aplica" used for missing values; no debate history or votes; in 194 rows the Senate number has "No Aplica" inserted between every character (see assumption A-008); the list number `no_` is a position, not a stable identifier, so the bill's page URL is used as its key
- Verification status: Verified on 2026-11-17 by API

### Source S-009: Votaciones sesiones plenaria Senado
- Institution: Senado de la República · ID `ucmr-52df` · Rows: 16,733 · Data last updated: 2024-10-29 · Vote dates 2017-02-14 to 2024-09-25
- Key fields: `fecha`, `fullname`, `proyecto` (free text), `vote`
- Known limitations: only "Si" (16,096) and "No" (637) values, so abstentions and absences are not recorded; bill is identified by free text, not by number; not updated since 2024; coverage of all plenary votes is unconfirmed
- Verification status: Verified on 2026-11-17 by API

### Source S-010: Representantes período 2026-2027
- Institution: Cámara de Representantes · ID `5pt5-nxdp` · Rows: 362 · Data last updated: 2026-11-11
- Known limitations: every column holds the value of the next column's name ("_" holds the name, "apelidos_y_nombre" the constituency, "partido_o_movimiento" the party or, for the opposition seat, its legal basis, "circunscripcion" the e-mail, "comision_const" the office, "comision_legal" the phone). Each of the 181 members appears in two rows; the second usually adds the office. No commissions and no dates of taking office
- Access restrictions: institutional e-mail, office and phone extensions present; shown as institutional contact (owner decision of 2026-11-18)
- Verification status: Verified on 2026-11-17 by API (structure only); all 362 rows profiled on 2026-11-18 and loaded with the mapping above (see `backend/app/ingestion/datasets/representatives.py`)

### Source S-011: Other datasets found, not yet inspected in detail
- `feim-cysj` Proyectos de ley del Senado (2,274 rows; stale since 2023-12-07)
- `48i3-vuny` Asistencia representantes sesiones plenarias (one column per session; 2026)
- `7w3p-s9ve` Integrantes de las UTL de los Representantes
- `75f2-fe2s`, `vkjr-c6fe` Resultados electorales 2018 Senado and Cámara (Registraduría; table-level; 2018 only)
- `iaeu-rcn6` Antecedentes de SIRI (Procuraduría; 42,070 rows; named sanctions with ID numbers: **excluded from the MVP pending legal review**)
- `jr8e-e8tu` Responsabilidad Fiscal (Contraloría; 60 rows; stale since 2022)
- `h8rs-jxum` Caracterización del Empleo Público; `5u9e-g5w9` Puestos Sensibles a la Corrupción (Función Pública)

## B. Verified by reading documentation or pages (not by API)

### Source S-020: Colombia Compra Eficiente – Manual de datos abiertos
- Confirms 14 SECOP/TVEC datasets on datos.gov.co, daily updates, entity responsibility for accuracy. Verified on 2026-11-17 by reading the manual.

### Source S-021: Open Contracting Partnership – Colombia OCDS publication
- Coverage January 2011 to April 2022; no longer updated; licence PDDL; documented quality issues (placeholder supplier IDs, multi-supplier awards). Historical use only. Verified on 2026-11-17.

### Source S-022: Corte Constitucional – Relatoría
- Site reachable; robots.txt explicitly allows `/relatoria/`. Search interface, document formats and completeness: Not yet verified.

### Source S-023: Senado de la República – website
- Transparency/open-data page has no structured downloads for bills, votes or senators; bills at `leyes.senado.gov.co`; Gacetas del Congreso at the Imprenta Nacional. robots.txt is the default Joomla file. Verified on 2026-11-17 by reading the page.

### Source S-024: Función Pública – Gestor Normativo, Constitución Política de 1991
- Institution: Departamento Administrativo de la Función Pública · Page: `https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=4125` · Category: legal texts · Acquisition method: HTML page (one request per synchronization) · Reliability class: 2 (official institutional record)
- Verified on 2026-11-17: robots.txt has an empty `Disallow` (every path allowed); the page carries no robots meta tag; the whole page was read and loaded. The page is about 1.2 MB.
- Status of the text: the page states that the data are informative, that Función Pública does not answer for the validity of the norm, and that contents are updated permanently. The most recent constitutional reform it mentions is Acto Legislativo 01 de 2025. NEXO has not checked whether later reforms exist. The text with legal value is the one published in the Gaceta Constitucional and the Diario Oficial.
- TLS: the server sends its certificate without the Let's Encrypt intermediate that issued it. Browsers fetch the missing certificate themselves; NEXO ships the two public Let's Encrypt certificates (`backend/app/law/certs/`) so that the connection is verified normally. Verification is never switched off.
- Known limitations: earlier wording follows the mark "TEXTO ANTERIOR" with no mark where it ends (69 articles); some words are struck through (inexequible passages); the labels "TÍTULO I" to "TÍTULO XI" and most "CAPÍTULO 1" labels are not printed (NEXO deduces them by order and says so on each division); the page does not print Chapter 3 of Title IV ("Del estatuto de la oposición"), so article 112 appears under Chapter 2, nor the name of Chapter 4 of Title III ("Del territorio"), both confirmed against the Senate's 2005 edition; the transitory provisions restart their numbering several times and are not loaded yet.
- Not loaded (data minimization): the editor's lists of cross-references "(Ver Ley …)" and the collapsed case-law lists. Loaded as notes, apart from the wording: notes on reforms and court rulings.
- Licence: legal texts may be reproduced freely (Ley 23 de 1982, article 41); the site's own terms of use were not reviewed.
- Why not SUIN-Juriscol: chosen first, but on 2026-11-17 it answered with an empty response both from the workspace and from the owner's browser.

## C. Not yet verified (leads only)

| Source | Why it matters | Blocker today |
|---|---|---|
| SUIN-Juriscol | Consolidated legal texts with validity information | Empty response from the workspace and from a regular browser on 2026-11-17 |
| Función Pública – Gestor Normativo, other norms | Laws and decrees with concordances | Each norm page must be checked like S-024 |
| Secretaría del Senado (basedoc) | Constitution and laws, annotated | Connection reset |
| Diario Oficial / Imprenta Nacional (Gacetas) | Official publication of norms; debate and vote records | Host not allowed yet |
| Consejo de Estado, Corte Suprema, Rama Judicial | Jurisprudence | Hosts not allowed yet |
| Registraduría, CNE | 2022 and 2026 results, party registry | Hosts not allowed yet |
| Portal de Transparencia Económica, Contraloría | Budget history, fiscal control | Hosts not allowed yet |
| Congreso Visible (Uniandes) | Secondary source for bills and votes | Terms of use not reviewed |
| Fiscalía, Defensoría | Oversight information | Not examined |

### Source S-024b: Gestor Normativo, selected laws
- Publisher: Departamento Administrativo de la Función Pública. One HTML page per law (`norma.php?i=<id>`); ids checked on 2026-11-24 by downloading each page and reading its title (app/law/statute_catalog.py).
- Registered as `funcionpublica.gov.co:gestor-normativo:leyes`. Informative edition: the publisher does not answer for the norms' validity; the official text is the Diario Oficial's.
- Loaded since 2026-11-24: 17 laws (Ley 610 de 2000 and Ley 1952 de 2019 added the same day) and Decreto 111 de 1996, which compiles the Estatuto Orgánico del Presupuesto, one request per law and synchronization, a second apart. Pages that no longer fit the reader are recorded as rejected rows with the reason.
- Verification status: Verified on 2026-11-24 by download.

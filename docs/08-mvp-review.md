# 08 — MVP review (prepared 2026-11-19)

The roadmap's "MVP review" step: the owner checks each MVP item of
`05-mvp-roadmap-risks.md` section 1; the review passes when each item is at least
**Probado** (tested). This page prepares that review: for each item, its stage,
the evidence, and what is still open. Stages follow `STATUS.md`.

All of this is in pull requests #5 to #14, not yet merged into `main`, and
nothing is deployed yet.

## Items

| # | Capability | Stage | Evidence | Open |
|---|---|---|---|---|
| 1 | Foundation: repository, Docker Compose, CI, migrations, settings | Probado | CI on every pull request: backend lint, types and 110 tests; frontend lint, unit tests and build; 68 browser tests; the production Compose stack and the Render container run end to end in CI | — |
| 2 | Core schema: provenance, institutions, people, positions, initiatives, instruments, provisions, budgets, relationships | Probado | `test_migrations.py`, the table tests and `test_relationships.py` (the source-or-method constraint, one link per subject and object, unverified claims never public) | — (the deviation found on 2026-11-19 is fixed: bill-to-author links moved into `core.relationship` on 2026-11-24, all 1,753 links kept) |
| 3 | Generic datos.gov.co connector: raw snapshots, validation, allow-lists, sync reports | Probado | `test_socrata.py`, `test_pipeline.py`; four live datasets loaded with every reject listed | — |
| 4 | Institution directory | Probado | API and pages tested; 6,404 entities from the live source (development database) | Load in production after deployment |
| 5 | Bills repository with filters | Probado | API and pages tested; 6,605 bills, 1 reject with its reason | Same |
| 6 | Budget execution per entity | Probado | `test_budget.py`; pages in browser tests; 600 rows, 221 entities | The source states no fiscal year (A-013, pages say so) |
| 7 | Constitution explorer | Probado | Law API and pages tested; 448 rows from Función Pública's page | The text is an informative edition, not the official gazette (pages say so); 73 articles flagged "Requiere revisión" (A-010) await legal review |
| 8 | Members of the Cámara | Probado | `test_representatives.py`; pages in browser tests; 181 members with the shifted columns reassigned (A-011) | — |
| 9 | Unified search (Spanish full text) | Probado | Search API tests; browser tests from the header search to a record | Budget entities are not in search yet |
| 10 | Learning path, glossary, quiz, links to live records | Probado as software; **content not reviewed** | Unit tests of the lesson structure; browser test of a lesson; all 34 cited articles exist in the real data (2026-11-19) | **Blocker:** the MVP requires the content reviewed before publication. Name a legally qualified reviewer, create their account (role "Revisión jurídica"), and have them approve both lessons in the panel. |
| 11 | Provenance panel, Epistemic Labels, "Fuentes" page | Probado | Origin panel on every record page in browser tests; labels tested in the API; Fuentes lists each source with its official link | — |
| 12 | Authentication, roles, audit log | Probado | `test_auth.py` (permissions by role, lockout, sessions, append-only log), `staff.spec.ts` | An independent security review before real accounts are used |
| 13 | Homepage and navigation with honest empty states | Probado | Browser tests of the home page and navigation; on 2026-11-19, with an empty database and with the API unreachable, every page said so instead of showing figures | — |

## What stands between this and a passed review

1. **Merge** pull requests #5 to #14, in order (owner).
2. **Legal review of the two lessons** (item 10): name the reviewer; they approve in the panel (owner, reviewer).
3. **Deploy** following `07-deployment-render-neon.md` and load the data in production (owner, about an hour).
4. **The owner's own review** of each item above, in the deployed site.

## Known limits accepted for the MVP (from STATUS)

- Senators, ministers and other non-representative bill authors stay as text;
  bills before 20 July 2026 are not linked to authors.
- Budget figures are snapshots without a stated year; earlier months stay only in
  the raw layer.
- Screen-reader testing (NVDA, VoiceOver) and a review by people who use assistive
  technology have not been done; automatic checks find only part of the problems.
- On Render, the first visit after 15 idle minutes waits about a minute; the free
  bandwidth suits a pilot.

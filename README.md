# NEXO Colombia

**Sistema de Conocimiento e Inteligencia Pública**

> Comprende el Estado. Explora sus instituciones. Investiga sus decisiones.

NEXO Colombia is a legal intelligence, public institutional research, civic education and government transparency platform for the Colombian State. Its goal is to make the State understandable, searchable, traceable and analytically accessible, with every displayed fact linked to its source.

## Status

**Milestone M2 (browse and search).** The platform loads two official datasets from datos.gov.co, the directory of public entities (Función Pública) and the bills registry of the Cámara de Representantes, shows them in pages where every record links to its source, and searches both from one box on every page. Everything else is still at the design stage, and nothing is deployed. See [docs/STATUS.md](docs/STATUS.md).

Status stages used in this project: Diseñado → Implementado → Probado → Integrado → Desplegado.

## Repository layout

| Path | Content |
|---|---|
| `backend/` | API (Python, FastAPI, SQLAlchemy, Alembic) and its tests |
| `frontend/` | Web application (Next.js, React, TypeScript, Tailwind CSS) |
| `docs/` | Requirements, architecture, data model, source registry, status |
| `docker-compose.yml` | Local database and API |
| `.github/workflows/ci.yml` | Lint, type checks, tests and build on every pull request |

## Development

Requirements: Python 3.12+, [uv](https://docs.astral.sh/uv/), Node 22, pnpm, PostgreSQL 16 (or Docker).

```bash
# Database (either Docker or a local PostgreSQL with a role and database named "nexo")
docker compose up -d db

# API
cd backend
cp .env.example .env
uv sync
uv run alembic upgrade head          # create the tables
uv run python -m app.sources.registry  # register the verified sources
uv run python -m app.ingestion.cli all # load entities and bills from datos.gov.co (about a minute)
uv run python -m app.search.reindex    # only needed to rebuild the search index for existing data
uv run uvicorn app.main:app --reload   # http://localhost:8000/api/v1/docs

# Checks
uv run ruff check . && uv run mypy app tests
uv run pytest                        # needs a database named "nexo_test"

# Web
cd ../frontend
pnpm install
pnpm dev                             # http://localhost:3000
```

## Documentation

| Document | Content |
|---|---|
| [Master engineering brief](docs/brief/master-engineering-brief.md) | Standing instructions, standards and scope for the project |
| [Technical assessment](docs/00-technical-assessment.md) | Phase 0 findings |
| [PRD](docs/01-prd.md) | Product requirements, functional and non-functional requirements, user stories |
| [Architecture](docs/02-architecture.md) | System design, ingestion strategy, security, ADRs |
| [Data model](docs/03-data-model.md) | Canonical schema and knowledge graph |
| [Source registry](docs/04-source-registry.md) | Official data sources and their verification status |
| [MVP, risks and roadmap](docs/05-mvp-roadmap-risks.md) | MVP scope, milestones, risk register |
| [Assumptions](docs/ASSUMPTIONS.md) | Assumptions register |

## Principles

1. Every statement carries an epistemic label: hecho documentado, interpretación jurídica, hipótesis analítica, simulación hipotética or no verificado.
2. Every claim is checkable against a cited source.
3. Political neutrality; individuals are described only through sourced, legally contextualized evidence.
4. Privacy by design under Ley 1581 de 2012.
5. Honest status reporting.

# Interface and accessibility tests

Playwright tests of the core flows, plus automatic WCAG 2.2 AA checks with axe-core
on every main page, at desktop and phone sizes. They run against invented sample
data, never the real database.

```bash
# backend, in one terminal
createdb nexo_ui                      # once
export NEXO_DATABASE_URL=postgresql+psycopg://nexo:nexo@localhost:5432/nexo_ui
uv run alembic upgrade head && uv run python -m tests.seed_ui
uv run uvicorn app.main:app --port 8000

# frontend, in another
pnpm build && pnpm start &
pnpm exec playwright install chromium   # once
pnpm test:e2e
```

Automatic checks find only part of the accessibility problems; keyboard use,
reading order and screen-reader wording still need a manual review.

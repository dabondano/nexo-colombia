# 07 — Deployment without a payment method: Render + Neon

Owner decision of 2026-11-18: host NEXO on free tiers that need no card.
(The one-server option on Oracle Cloud, docs/06, stays available for later.)

```
Visitor ──HTTPS──▶ Render free web service (one container)
                     ├─ web: Next.js server, public, rate-limits staff forms
                     └─ api: FastAPI on 127.0.0.1 only ──▶ Neon PostgreSQL (free)
GitHub Actions ── weekly data sync, daily backup ──▶ Neon
```

| Piece | Free allowance it relies on | What happens at the limit |
|---|---|---|
| Neon (database) | 1 GB storage per project, 100 compute-hours a month, scales to zero after 5 minutes idle. NEXO's full data is about 90 MB. | Usage is capped; no charge. |
| Render (web + API) | One free web service; 750 instance hours a month per workspace; sleeps after 15 minutes without visits and takes about a minute to wake. | Suspended until the next month if bandwidth or hours run out. |
| GitHub Actions | Weekly sync (~5 min) and daily backup (~1 min) use a small part of the private-repository minutes. | Jobs stop until the next month. |

Trade-offs to know: the first visit after a quiet spell waits about a minute;
the free bandwidth is small (enough for a pilot, not for heavy traffic); the
data is stored outside Colombia (Neon and Render have no Colombian region), so
have the Ley 1581 transfer question checked by someone qualified. Render has
occasionally asked for card verification even for free services; if it does,
Oracle (docs/06) or the Neon + Cloud Run combination are the fallbacks.

## 1. Database on Neon

1. Sign up at neon.com (GitHub or e-mail; no card).
2. Create a project named `nexo`: PostgreSQL 17 (or 16), region **AWS US East (N. Virginia)** —
   the same area as the Render service, so the pages' queries stay fast.
3. Open **Connect**, turn **off** "Connection pooling", and copy the connection string
   (`postgresql://…neon.tech/neondb?sslmode=require…`). The direct connection is needed
   for migrations; keep the string secret.

## 2. Web service on Render

1. Sign up at render.com with your GitHub account and allow it to read
   `dabondano/nexo-colombia`.
2. **New → Blueprint**, pick the repository and branch `main`. Render reads
   `render.yaml` and proposes one free web service, `nexo-colombia`.
3. When asked for `NEXO_DATABASE_URL`, paste the Neon connection string. Apply.
4. The first build takes several minutes. On start, the container applies the
   database migrations, then serves the site at `https://nexo-colombia.onrender.com`
   (or the name Render assigns). You can add your own domain later in the service's
   **Settings → Custom Domains**; Render issues the certificate.

## 3. Scheduled jobs on GitHub

1. In GitHub: repository → **Settings → Secrets and variables → Actions → New
   repository secret**: name `NEXO_DATABASE_URL`, value the same Neon string.
2. **Actions → Data sync → Run workflow** loads every dataset the first time
   (a few minutes). After that it runs every Sunday; **Database backup** runs daily
   and keeps each dump for 30 days as a downloadable artifact of the run.
   Scheduled workflows run from `main`, so they start once the work is merged.

## 4. First administrator

On your computer, with the backend set up (`uv sync` in `backend/`):

```bash
cd backend
NEXO_DATABASE_URL='<the Neon string>' uv run python -m app.auth.cli create-admin you@example.org "Your name"
```

Then open `https://<your-service>.onrender.com/ingresar` with the one-time password
it prints; you will be asked to choose your own.

## 5. Everyday operation

| Task | How |
|---|---|
| Deploy a change | Merge to `main`; Render rebuilds and redeploys automatically. |
| Synchronize data now | GitHub → Actions → Data sync → Run workflow. Results appear in the panel ("Sincronizaciones"). |
| Get a backup | GitHub → Actions → Database backup → the latest run → Artifacts. |
| Restore a backup | `pg_restore --clean --if-exists --no-owner -d '<Neon string>' nexo-<date>.dump` (PostgreSQL 17 client tools). |
| See logs | Render dashboard → the service → Logs. |
| Wake-up delay | Optional: a free uptime monitor requesting the home page every 10 minutes keeps the service awake (one service fits in the 750 monthly hours). Render's documentation neither allows nor forbids this. |

## 6. Security notes

- Only the web server is public; the API listens on 127.0.0.1 inside the container.
- Staff sign-in and panel forms are limited to 10 submissions a minute per IP
  address (`frontend/lib/rate-limit.ts`). The address comes from the
  `True-Client-IP` header that Cloudflare, in front of Render, sets; Render's
  `X-Forwarded-For` can be forged by the visitor and is not used. Per-account
  lockout in the API applies as well.
- The database connection string lives only in Render's environment and in the
  GitHub secret. Backup artifacts contain staff e-mail addresses and password
  hashes and are visible to everyone with access to the repository.

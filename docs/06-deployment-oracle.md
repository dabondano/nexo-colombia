# 06 — Deployment on Oracle Cloud (Always Free)

Owner decision of 2026-11-18: host NEXO on one Oracle Cloud Always Free Arm
server, with the whole stack in Docker Compose (`deploy/compose.yaml`).

```
Internet ──443/80──▶ Caddy (HTTPS, security headers, per-IP limits)
                        │
                        ▼
                     web (Next.js server) ──▶ api (FastAPI) ──▶ db (PostgreSQL 16)
```

Only Caddy publishes ports. The API and the database are reachable inside the
stack only. Caddy obtains and renews the HTTPS certificate by itself.

The CI job `deploy` builds and runs this same stack on every pull request and
checks HTTPS, headers, 404s, the panel redirect, the sign-in rate limit, that the
API and database are not published, and the backup script.

## 1. Decide before creating the account

| Decision | Recommendation | Why |
|---|---|---|
| Home region | **Colombia Central (Bogota), `sa-bogota-1`** | Always Free servers can only be created in the home region, which cannot be changed later. A Colombian region keeps the data in Colombia (Ley 1581; have the transfer and storage questions confirmed by someone qualified). |
| Account type | Start Always Free; consider **Pay As You Go** once it runs | Oracle may reclaim Always Free servers it considers idle: over 7 days, 95th-percentile CPU, network and memory all below 20 %. A low-traffic site fits that description. Oracle's notices offer converting to Pay As You Go to avoid it; Always Free resources stay free after upgrading, and only usage above the free limits is charged. If you upgrade, set a budget alert at a small amount (Billing → Budgets) and keep to the shapes below. |
| Domain | A domain you control (e.g. a `.co` or `.org`), or a free subdomain from a dynamic DNS service | HTTPS certificates need a name, not a bare IP address. |

You need a phone number and a card to create the account; Oracle does not charge
the card for Always Free resources.

## 2. Create the server

1. Sign up at oracle.com/cloud/free and choose **Colombia Central (Bogota)** as home region.
2. **Compute → Instances → Create instance**:
   - Image: **Canonical Ubuntu 24.04** (the aarch64 image is chosen automatically for Arm).
   - Shape: **Ampere → VM.Standard.A1.Flex**, **2 OCPU, 12 GB memory** (the current Always Free allowance).
   - Networking: create a new virtual cloud network with a public subnet; assign a public IPv4 address.
   - SSH keys: upload your public key (keep the private key safe; password login stays disabled).
   - Boot volume: 100 GB (the Always Free storage total is 200 GB).
   - If Oracle answers "Out of capacity", try again later; Bogotá has a single availability domain.
3. **Networking → your VCN → public subnet → Default security list → Add ingress rules**, source `0.0.0.0/0`:
   TCP 80, TCP 443, UDP 443. (SSH, TCP 22, is already open.)
4. Point your domain's **A record** to the server's public IP and wait until `ping your-domain` shows it.

## 3. Prepare the server

```bash
ssh ubuntu@<public-ip>

# Read access to the private repository: create a deploy key on the server...
ssh-keygen -t ed25519 -C "nexo-server" -f ~/.ssh/github_nexo -N ""
cat ~/.ssh/github_nexo.pub
# ...and add it in GitHub: repository → Settings → Deploy keys → Add (read-only).
printf 'Host github.com\n  IdentityFile ~/.ssh/github_nexo\n' >> ~/.ssh/config

git clone git@github.com:dabondano/nexo-colombia.git
cd nexo-colombia
bash deploy/scripts/server-setup.sh   # Docker, host firewall (80/443), swap, security updates
exit                                  # log in again so the docker group applies
```

Oracle's Ubuntu images block everything but SSH in the host firewall even when the
security list allows it; `server-setup.sh` opens 80 and 443 there too.

## 4. Start NEXO

```bash
ssh ubuntu@<public-ip>
cd nexo-colombia/deploy
cp .env.example .env
nano .env        # NEXO_DOMAIN, ACME_EMAIL, POSTGRES_PASSWORD, NEXO_APP_DB_PASSWORD (openssl rand -hex 24 each)
chmod 600 .env

docker compose up -d --build --wait     # first build on Arm takes several minutes
./scripts/sync.sh                       # load every dataset from its official source
docker compose exec api python -m app.auth.cli create-admin you@example.org "Your name"
```

Open `https://<your-domain>`, then `https://<your-domain>/ingresar` with the
one-time password printed above; you will be asked to choose your own.

Then schedule the backups and the weekly data synchronization:

```bash
crontab -e      # paste deploy/crontab.example, adjusting paths if needed
```

## 5. Everyday operation

| Task | Command (in `~/nexo-colombia/deploy`) |
|---|---|
| Update to the latest `main` | `git pull && docker compose up -d --build --wait` |
| See status / logs | `docker compose ps` · `docker compose logs -f web api` |
| Synchronize data now | `./scripts/sync.sh` (results in the panel, "Sincronizaciones") |
| Back up now | `./scripts/backup.sh` (dumps in `deploy/backups/`, kept 14 days) |
| Restore a backup | `./scripts/restore.sh backups/nexo-<date>.dump` |
| Create staff accounts | In the panel, "Cuentas" (administrators) |

**Copy backups off the server.** A backup on the same disk does not survive the
loss of the server (including reclamation). At least weekly, copy the newest
dump elsewhere, for example to your computer:
`scp ubuntu@<public-ip>:nexo-colombia/deploy/backups/<file>.dump .`,
or to an Oracle Object Storage bucket.

**Watch that it is up.** A free external uptime monitor pinging the home page
every few minutes also tells you quickly if Oracle stops the server.

## 6. Security notes

- Public surface: ports 80 (redirects to HTTPS) and 443, served by Caddy. SSH (22)
  accepts keys only.
- Caddy limits each IP address to 10 POST requests a minute on the sign-in page
  and the staff panel, and 60 on any page; beyond that it answers 429 (ADR-006).
- The database password lives only in `deploy/.env` (permissions 600, never
  committed). Ubuntu installs security updates automatically.
- The application connects as `nexo_app` (created on the database's first start by
  `deploy/db-init/`), which cannot change or delete the audit log, the raw records,
  the rejected rows or the legal reviews, nor alter tables; the owner account runs
  only migrations and privileges (`backend/app/core/grants.py`).

# Local demo

The whole platform on your own computer, with real public data: the Constitution, 18 laws, the directory of public entities, bills, representatives, the national budget and recent contracts. Search, the learning paths and the staff panel all work.

## What you need

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows or Mac), running.
- This repository on your computer (`git clone https://github.com/dabondano/nexo-colombia.git`, or GitHub Desktop).
- About 3 GB of free disk space and an internet connection for the first start.

## Start it

From the repository folder, in PowerShell, Terminal or the VS Code terminal:

```
docker compose -f demo/compose.yaml up --build
```

1. The first build takes 5 to 10 minutes. Later starts take seconds.
2. Open <http://localhost:3000> when the log shows `Loading public data`. The site works from that point; sections fill in as each dataset lands (a few more minutes).
3. The log ends with `Done. Open http://localhost:3000`.

## Staff panel

The first start creates an administrator, `demo@nexo.local`, and prints a one-time password in the log, on the line that starts with `Contraseña de un solo uso`. Sign in at <http://localhost:3000/ingresar> and choose a new password.

If you missed it: `docker compose -f demo/compose.yaml logs loader`.

## Stop, restart, reset

| To | Run |
| --- | --- |
| Stop | `Ctrl+C`, or `docker compose -f demo/compose.yaml stop` |
| Start again (keeps the data) | `docker compose -f demo/compose.yaml up` |
| Download the data again | `NEXO_DEMO_RELOAD=1 docker compose -f demo/compose.yaml up` (PowerShell: `$env:NEXO_DEMO_RELOAD=1; docker compose -f demo/compose.yaml up`) |
| Delete everything | `docker compose -f demo/compose.yaml down -v` |

## Notes

- Everything stays on your computer. The passwords in `compose.yaml` are for this demo only.
- Port 3000 in use? Change `"3000:3000"` to `"3001:3000"` in `compose.yaml` and open <http://localhost:3001>.
- If a dataset fails to download (a source site is down), the rest still loads; run the reload command later.

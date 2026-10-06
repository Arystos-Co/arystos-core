# ARYSTOS Core

ARYSTOS Core is the FastAPI service and React dashboard for managing registered
clients, their status and payment information, and dashboard user access.

## Requirements

- Python 3.12 or newer
- Node.js 22 or newer and npm

## Setup

From the project root, install the Python package and development dependencies:

```powershell
python -m pip install -e ".[dev]"
```

Configure the server using a `.env` file in the project root. At minimum, set a
private `ADMIN_TOKEN` for local administration:

```env
ADMIN_TOKEN=replace-with-a-private-random-token
```

Generate a token locally with:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

Never commit `.env` or share the token. The built-in development fallback is
not suitable for deployment or for a server accessible to other people.
Additional settings include `DATABASE_URL`, `RELEASES_DIR`, and `ENV`; defaults
are defined in `server/config.py`.

## Run locally

Build the dashboard, then start the API server from the project root:

```powershell
cd dashboard
npm ci
npm run build
cd ..
python -m uvicorn server.main:app --reload --host 127.0.0.1 --port 8000
```

Open <http://localhost:8000/dashboard/>. On first setup, choose **Use admin
token instead**, sign in with `ADMIN_TOKEN`, then open **Users** and create an
owner account with a password of at least 12 characters. Sign out and use that
account for normal dashboard access.

## Roles and access

- **Owner**: full dashboard access, including user management and token
  regeneration.
- **Operator**: client operations, but not user management or token
  regeneration.
- **Read only**: view client and audit information.

The Users navigation item and `/dashboard/users` page are owner-only. Operators
and read-only users are sent back to Clients when they navigate directly to
that route. The server independently enforces these permissions.

## Checks

Run the backend checks from the project root:

```powershell
python tools/check_sql.py
ruff check server/
mypy server/
pytest server/tests/ -x
```

Run the dashboard checks:

```powershell
cd dashboard
npm ci
npm run lint
npm run build
```

The production dashboard build is emitted to `server/dashboard/static/` and is
served by the FastAPI application under `/dashboard/`. GitHub Actions runs both
the Python checks and the dashboard lint/build.

## Git and GitHub

Git records project changes locally; GitHub hosts a copy of the repository.
Install Git for Windows and sign in to GitHub in your browser before pushing.
Create a **private** repository named `ARYSTOS-CODE` under your GitHub account.
Leave the options to add a README, `.gitignore`, or license unchecked so the
new repository starts empty.

From the project root, configure the author information Git will put on commits
(use the email associated with your GitHub account):

```powershell
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

For this new local repository, initialize the `main` branch and check what Git
will track:

```powershell
git init -b main
git status --short
```

Review the status. Confirm that `.env`, database files, `node_modules`, caches,
and credentials are not listed. Stage and review files before committing:

```powershell
git add .
git status --short
git diff --cached --check
git diff --cached --stat
```

If the staged changes look right, create the initial commit and connect it to
your empty private GitHub repository:

```powershell
git commit -m "Build ARYSTOS Core dashboard and user management" -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
git remote add origin https://github.com/0br13n14/ARYSTOS-CODE.git
git push -u origin main
```

For future updates, inspect changes, stage only the files you intend to include,
commit, and push:

```powershell
git status
git add path/to/changed-file
git diff --cached
git commit -m "Describe the change"
git push
```

Never commit credentials or use `git push --force` as a routine workflow.

## Design references

- [Dashboard design](../docs/arystos-dashboard-design.md)
- [Core low-level design](../docs/arystos-core-lld-final.md)

# Build

Use this command when you want the agent to **build and sanity-check the project** in a way that works across macOS, Windows, and Linux.

## Rules

- Start by reading **README.md** for the canonical build/run steps.
- Prefer commands that are **cross-platform** (avoid hard-coded absolute paths).
- **Do not push** images or publish artifacts unless explicitly requested.
- If secrets are needed, use local `.env` / 1Password and **never** write keys into git-tracked files.

## Typical Docker workflow (if applicable)

If this repo includes a `docker-compose.yml`:

1. From the repo root, run:
   - `docker compose build`
   - `docker compose up -d`
2. If a platform-specific build is required (e.g., linux/amd64), use:
   - `docker buildx build --platform linux/amd64 -t <tag> -f Dockerfile .`
   - (add `--load` for local usage; do **not** add `--push` unless told)

## What to report back

- The exact commands you ran
- Whether the build succeeded
- Any errors/warnings and the most likely fix

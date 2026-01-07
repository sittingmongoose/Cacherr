# Design

Use this command when you want the agent to **propose or refine a design** for this repo.

## Do this first

1. Read (in order):
   - `README.md`
   - `.cursorrules`
   - `.claude/CLAUDE.md` (if present)
   - any docs referenced by the README
2. Summarize the current architecture in 5–10 bullets.

## Constraints

- Keep everything **cross-platform** (macOS + Windows + Linux + SSH dev servers).
- Avoid machine-specific assumptions:
  - No absolute paths
  - No OS-specific shell commands unless you also provide an alternative
- Never commit secrets. If config needs a token, use `.env` / 1Password and keep the secret files gitignored.

## Output format

- Goals / non-goals
- Proposed approach (high level)
- Key components + responsibilities
- Data model / APIs (if relevant)
- Risks & tradeoffs
- Implementation plan (small, reviewable steps)
- Testing / validation plan

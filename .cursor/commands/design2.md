# Design (Deep Dive)

Use this command when you want a **more detailed** design than `design.md`, including migration steps and edge cases.

## Required reading

- `README.md`
- `.cursorrules`
- `.claude/CLAUDE.md` (if present)
- Existing code for the area being changed (identify entrypoints + call graph)

## Deliverables

1. **Detailed proposal**
   - Interfaces (types, function signatures)
   - Error handling strategy
   - Logging/telemetry changes
   - Backwards compatibility and migration steps
2. **Operational concerns**
   - Config/secrets strategy (must be safe for GitHub)
   - Cross-platform dev ergonomics (mac/windows/linux)
   - CI considerations (if any)
3. **Acceptance criteria**
   - Measurable “done” conditions
   - How to validate locally and in CI

## Guardrails

- No hard-coded absolute paths.
- Prefer standard tooling that works on all platforms.
- If you introduce a dependency, explain why and where it’s used.

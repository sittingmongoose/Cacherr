# Secrets Setup (1Password + MCP)

This repo keeps **settings** in git, but keeps **secrets** (API keys, tokens) out of git.

## Context7 MCP (Cursor)

Cursor reads MCP configuration from:

- `.cursor/mcp-config.json`

That file is **gitignored** because it must contain secrets.

### 1Password recommended flow

1. Store the Context7 key in 1Password.
2. Create a 1Password *Secret Reference* for the field, e.g.

   `op://Your Vault/Your Item/CONTEXT7_API_KEY`

3. On each machine, run one of the bootstrap scripts to generate `.cursor/mcp-config.json`:

**macOS / Linux / Unraid**

```sh
export OP_CONTEXT7_API_KEY_REF='op://Your Vault/Your Item/CONTEXT7_API_KEY'
./bin/setup-mcp-context7.sh
```

**Windows (PowerShell)**

```powershell
$env:OP_CONTEXT7_API_KEY_REF = 'op://Your Vault/Your Item/CONTEXT7_API_KEY'
.\bin\setup-mcp-context7.ps1
```

> The scripts will also use `CONTEXT7_API_KEY` if it is already set in your environment or found in a local `.env` file.

### Shared config vs local secrets

- **Tracked:** `.cursor/mcp-config.example.json` (no secrets)
- **Local-only:** `.cursor/mcp-config.json` (contains secrets, gitignored)

If you add/remove MCP servers, update the example config and re-run the setup script to regenerate the local file.

## .env

- `.env` is gitignored.
- `.env.example` is committed as a template.


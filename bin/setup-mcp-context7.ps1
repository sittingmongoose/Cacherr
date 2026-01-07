param(
  [string]$RepoRoot = $(Resolve-Path "$PSScriptRoot\.." | Select-Object -ExpandProperty Path)
)

$CursorDir = Join-Path $RepoRoot ".cursor"
$OutFile = Join-Path $CursorDir "mcp-config.json"

function Get-KeyFromDotEnv {
  $dotenv = Join-Path $RepoRoot ".env"
  if (-not (Test-Path $dotenv)) { return $null }

  $line = (Get-Content $dotenv | Where-Object { $_ -match '^[\s]*CONTEXT7_API_KEY=' } | Select-Object -First 1)
  if (-not $line) { return $null }

  return ($line -replace '^[\s]*CONTEXT7_API_KEY=', '')
}

function Get-Context7Key {
  if ($env:CONTEXT7_API_KEY -and $env:CONTEXT7_API_KEY.Trim().Length -gt 0) {
    return $env:CONTEXT7_API_KEY
  }

  $fromEnv = Get-KeyFromDotEnv
  if ($fromEnv -and $fromEnv.Trim().Length -gt 0) {
    return $fromEnv
  }

  if ($env:OP_CONTEXT7_API_KEY_REF -and $env:OP_CONTEXT7_API_KEY_REF.Trim().Length -gt 0) {
    if (Get-Command op -ErrorAction SilentlyContinue) {
      return (op read $env:OP_CONTEXT7_API_KEY_REF)
    }
  }

  return $null
}

$key = Get-Context7Key
if (-not $key -or $key.Trim().Length -eq 0) {
  Write-Error "Could not find CONTEXT7_API_KEY. Set env:CONTEXT7_API_KEY, add it to .env, or set env:OP_CONTEXT7_API_KEY_REF (op://...) and install/sign-in to 1Password CLI (op)."
  exit 1
}

New-Item -ItemType Directory -Force -Path $CursorDir | Out-Null

@"
{
  \"mcpServers\": {
    \"context7\": {
      \"httpUrl\": \"https://mcp.context7.com/mcp\",
      \"headers\": {
        \"CONTEXT7_API_KEY\": \"$key\"
      }
    }
  }
}
"@ | Set-Content -NoNewline -Encoding UTF8 $OutFile

Write-Output "Wrote $OutFile (gitignored)."

$RepoRoot = (Resolve-Path "$PSScriptRoot\..").Path
$env:CODEX_HOME = "$RepoRoot\.codex"
codex --config "$RepoRoot\.codex\config.toml" @args

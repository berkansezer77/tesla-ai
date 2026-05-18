param(
  [string]$RepoRoot = ""
)

$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
  $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}

$manifestPath = Join-Path $RepoRoot "custom_components\pom_tesla_report\manifest.json"
$readmePath = Join-Path $RepoRoot "README.md"

$manifest = Get-Content -Path $manifestPath -Raw | ConvertFrom-Json
$version = [string]$manifest.version
$today = Get-Date -Format "yyyy-MM-dd"
$autoLine = "Version: $version | Last updated: $today"

$readme = Get-Content -Path $readmePath -Raw
$pattern = '(?s)<!-- AUTO:BADGES_START -->.*?<!-- AUTO:BADGES_END -->'
$replacement = "<!-- AUTO:BADGES_START -->`r`n$autoLine`r`n<!-- AUTO:BADGES_END -->"

if ($readme -match $pattern) {
  $readme = [regex]::Replace($readme, $pattern, $replacement)
} else {
  $readme = $readme -replace "# POM Tesla Report\r?\n", "# POM Tesla Report`r`n`r`n$replacement`r`n"
}

Set-Content -Path $readmePath -Value $readme -Encoding UTF8
Write-Host "README updated: version=$version, date=$today"

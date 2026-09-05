param(
    [string]$OutputPath = "expense-tracker-share.zip"
)

if (Test-Path -LiteralPath $OutputPath) {
    throw "$OutputPath already exists. Choose a new name or remove it first."
}

$trackedEnvironmentFiles = git ls-files -- .env frontend/.env
if ($trackedEnvironmentFiles) {
    throw "A private environment file is tracked by Git. Remove it from Git before sharing."
}

git diff --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Warning "The archive contains committed HEAD only; uncommitted changes are not included."
}

git archive --format=zip --output=$OutputPath HEAD
if ($LASTEXITCODE -ne 0) {
    throw "Git could not create the archive."
}

Write-Host "Created $OutputPath without .env, .venv, node_modules, or build output."

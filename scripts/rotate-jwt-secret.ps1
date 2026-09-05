param(
    [string]$EnvPath = (Join-Path $PSScriptRoot "..\.env")
)

if (-not (Test-Path -LiteralPath $EnvPath)) {
    throw ".env was not found. Create it from .env.example first."
}

$secretBytes = New-Object byte[] 48
$random = [System.Security.Cryptography.RandomNumberGenerator]::Create()
$random.GetBytes($secretBytes)
$random.Dispose()
$newSecret = [Convert]::ToBase64String($secretBytes)
$content = [System.IO.File]::ReadAllText((Resolve-Path -LiteralPath $EnvPath))
$updated = [regex]::Replace(
    $content,
    '(?m)^JWT_SECRET_KEY=.*$',
    "JWT_SECRET_KEY=$newSecret"
)

if ($updated -eq $content) {
    throw "JWT_SECRET_KEY was not found in .env."
}

[System.IO.File]::WriteAllText(
    (Resolve-Path -LiteralPath $EnvPath),
    $updated,
    [System.Text.UTF8Encoding]::new($false)
)

Write-Host "JWT secret rotated. Restart the API and log in again."

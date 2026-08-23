# Regenerate local session.secret (workbench)
# Run from the directory that holds session.secret. Never commit the output.

$bytes = New-Object byte[] 32
[System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
$secret = [Convert]::ToHexString($bytes).ToLower()
Set-Content -Path "session.secret" -Value $secret -NoNewline
Write-Host "Wrote new session.secret ($( $secret.Length ) hex chars). Rotate any service that read the old file."

if (Test-Path "credentials.once.txt") {
  Remove-Item "credentials.once.txt" -Force
  Write-Host "Removed credentials.once.txt — re-issue one-time credentials if needed."
}

$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$taskPython = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
if (Test-Path -LiteralPath $taskPython) {
    & $taskPython run.py
} else {
    Write-Host 'Complete the Windows setup in README.md first.'
    Write-Host 'python -m venv .venv'
    Write-Host '.\.venv\Scripts\python.exe -m pip install -r requirements.txt'
    exit 1
}

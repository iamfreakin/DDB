. "$PSScriptRoot\resolve_python.ps1"

$python = Resolve-ProjectPython
& $python -m uvicorn backend.app.main:app --reload --port 8000


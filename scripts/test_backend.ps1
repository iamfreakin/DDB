. "$PSScriptRoot\resolve_python.ps1"

$python = Resolve-ProjectPython
& $python -m unittest discover -s backend/tests -v
exit $LASTEXITCODE


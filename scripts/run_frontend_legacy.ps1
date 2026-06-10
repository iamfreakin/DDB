. "$PSScriptRoot\resolve_python.ps1"

$python = Resolve-ProjectPython
& $python -m streamlit run frontend/app.py

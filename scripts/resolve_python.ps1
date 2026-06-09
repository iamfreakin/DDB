function Resolve-ProjectPython {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCommand) {
        return $pythonCommand.Source
    }

    $pyCommand = Get-Command py -ErrorAction SilentlyContinue
    if ($pyCommand) {
        return $pyCommand.Source
    }

    $bundledPython = Join-Path $env:USERPROFILE `
        ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
    if (Test-Path -LiteralPath $bundledPython) {
        return $bundledPython
    }

    throw "Python 3.10 이상을 찾을 수 없습니다. Python을 설치하고 PATH에 추가해 주세요."
}


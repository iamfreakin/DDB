$npm = Get-Command npm.cmd -ErrorAction SilentlyContinue
if (-not $npm) {
    throw "npm.cmd를 찾을 수 없습니다. Node.js 20.9 이상을 설치해 주세요."
}

$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
& $npm.Source --prefix (Join-Path $projectRoot "web") run dev

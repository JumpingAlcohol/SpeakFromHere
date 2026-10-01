$ErrorActionPreference = 'Stop'
$projectDirectory = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$projectPython = Join-Path $projectDirectory '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $projectPython)) {
    throw 'Create the project virtual environment and install .[build] first.'
}

$previousCache = $env:PYINSTALLER_CONFIG_DIR
try {
    $env:PYINSTALLER_CONFIG_DIR = Join-Path $projectDirectory 'work\pyinstaller-cache'
    & $projectPython -m PyInstaller `
        --noconfirm `
        --distpath (Join-Path $projectDirectory 'outputs') `
        --workpath (Join-Path $projectDirectory 'work\pyinstaller') `
        (Join-Path $projectDirectory 'AIChatReader.spec')
    if ($LASTEXITCODE -ne 0) { throw 'The executable build failed.' }
    $executable = Join-Path $projectDirectory 'outputs\AIChatReader.exe'
    if (-not (Test-Path -LiteralPath $executable)) { throw 'The executable was not produced.' }
    $englishGuide = Join-Path $projectDirectory 'outputs\QuickStart.en.txt'
    $chineseGuide = Join-Path $projectDirectory 'outputs\QuickStart.zh-CN.txt'
    Copy-Item -LiteralPath (Join-Path $projectDirectory 'docs\QuickStart.en.txt') -Destination $englishGuide
    Copy-Item -LiteralPath (Join-Path $projectDirectory 'docs\QuickStart.zh-CN.txt') -Destination $chineseGuide
    $portableArchive = Join-Path $projectDirectory 'outputs\AIChatReader-Windows-x64.zip'
    Compress-Archive -LiteralPath $executable,$englishGuide,$chineseGuide -DestinationPath $portableArchive -Force
    Write-Output "Built: $executable"
    Write-Output "Portable package (English + Simplified Chinese): $portableArchive"
} finally {
    $env:PYINSTALLER_CONFIG_DIR = $previousCache
}

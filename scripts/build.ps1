param([string]$OutputDirectory = 'outputs\v0.4.0\SpeakFromHere', [switch]$Clean)
$ErrorActionPreference = 'Stop'
$projectDirectory = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$buildOutput = Join-Path $projectDirectory $OutputDirectory
$projectPython = Join-Path $projectDirectory '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $projectPython)) {
    throw 'Create the project virtual environment and install .[build,paragraph] first.'
}

$previousCache = $env:PYINSTALLER_CONFIG_DIR
try {
    $env:PYINSTALLER_CONFIG_DIR = Join-Path $projectDirectory 'work\pyinstaller-cache'
    $extraBuildArguments = @()
    if ($Clean) { $extraBuildArguments += '--clean' }
    & $projectPython -m PyInstaller `
        @extraBuildArguments `
        --noconfirm `
        --distpath $buildOutput `
        --workpath (Join-Path $projectDirectory 'work\pyinstaller') `
        (Join-Path $projectDirectory 'SpeakFromHere.spec')
    if ($LASTEXITCODE -ne 0) { throw 'The executable build failed.' }
    $executable = Join-Path $buildOutput 'SpeakFromHere.exe'
    if (-not (Test-Path -LiteralPath $executable)) { throw 'The executable was not produced.' }
    $consoleExecutable = Join-Path $buildOutput 'SpeakFromHereConsole.exe'
    if (-not (Test-Path -LiteralPath $consoleExecutable)) { throw 'The console executable was not produced.' }
    $workerDirectory = Join-Path $buildOutput 'reader-worker'
    if (-not (Test-Path -LiteralPath (Join-Path $workerDirectory 'SpeakFromHereWorker.exe'))) {
        throw 'The paragraph helper was not produced.'
    }
    $englishGuide = Join-Path $buildOutput 'QuickStart.en.txt'
    $chineseGuide = Join-Path $buildOutput 'QuickStart.zh-CN.txt'
    Copy-Item -LiteralPath (Join-Path $projectDirectory 'docs\QuickStart.en.txt') -Destination $englishGuide
    Copy-Item -LiteralPath (Join-Path $projectDirectory 'docs\QuickStart.zh-CN.txt') -Destination $chineseGuide
    $portableArchive = Join-Path $buildOutput 'SpeakFromHere-Windows-x64.zip'
    Compress-Archive -LiteralPath $executable,$consoleExecutable,$englishGuide,$chineseGuide,$workerDirectory -DestinationPath $portableArchive -Force
    $checksum = (Get-FileHash -LiteralPath $portableArchive -Algorithm SHA256).Hash.ToLowerInvariant()
    Set-Content -LiteralPath (Join-Path $buildOutput 'SHA256SUMS.txt') -Value "$checksum  SpeakFromHere-Windows-x64.zip" -Encoding ascii
    Write-Output "Built: $executable"
    Write-Output "Portable package (English + Simplified Chinese): $portableArchive"
} finally {
    $env:PYINSTALLER_CONFIG_DIR = $previousCache
}

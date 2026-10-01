$ErrorActionPreference = 'Stop'
$projectDirectory = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$sourceExecutable = Join-Path $projectDirectory 'outputs\AIChatReader.exe'
if (-not (Test-Path -LiteralPath $sourceExecutable)) { throw 'Build the executable first.' }
$testDirectory = Join-Path $projectDirectory ('work\exe-smoke-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $testDirectory -Force | Out-Null
$testExecutable = Join-Path $testDirectory 'AIChatReader.exe'
Copy-Item -LiteralPath $sourceExecutable -Destination $testExecutable

if (-not ('ReaderTest.NativeMethods' -as [type])) {
    Add-Type -Namespace ReaderTest -Name NativeMethods -MemberDefinition @'
[System.Runtime.InteropServices.DllImport("user32.dll", SetLastError = true)]
public static extern bool PostThreadMessage(uint threadId, uint message, System.UIntPtr wParam, System.IntPtr lParam);
'@
}

function Wait-ReaderOutput {
    param([string]$Path, [string]$Expected, [System.Diagnostics.Process]$Process)
    $deadline = [DateTime]::UtcNow.AddSeconds(15)
    while ([DateTime]::UtcNow -lt $deadline) {
        if (Test-Path -LiteralPath $Path) {
            $output = Get-Content -LiteralPath $Path -Raw
            if ($output -and $output.Contains($Expected)) { return }
        }
        if ($Process.HasExited) { break }
        Start-Sleep -Milliseconds 50
    }
    throw "Reader did not report: $Expected. Check test logs in $testDirectory."
}

function Send-ReaderEvent {
    param([uint32]$ThreadId, [uint32]$EventId)
    # Only the process spawned by this test receives messages; no keyboard input is injected.
    if (-not [ReaderTest.NativeMethods]::PostThreadMessage(
        $ThreadId, 0x0312, [UIntPtr]::new($EventId), [IntPtr]::Zero)) {
        throw 'Could not deliver the test hotkey message.'
    }
}

for ($attempt = 1; $attempt -le 2; $attempt++) {
    $stdout = Join-Path $testDirectory "run-$attempt.stdout.log"
    $stderr = Join-Path $testDirectory "run-$attempt.stderr.log"
    $testProcess = Start-Process -FilePath $testExecutable -WorkingDirectory $testDirectory `
        -WindowStyle Hidden -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr
    try {
        Wait-ReaderOutput $stdout 'AI Chat Reader is running.' $testProcess
        # A one-file bundle starts a child process after unpacking its runtime.
        $children = @(Get-CimInstance Win32_Process -Filter "ParentProcessId = $($testProcess.Id)" |
            Where-Object { $_.ExecutablePath -eq $testExecutable })
        $runtimeProcess = if ($children.Count -eq 1) {
            Get-Process -Id $children[0].ProcessId
        } elseif ($children.Count -eq 0) {
            $testProcess
        } else {
            throw 'Could not uniquely identify the bundled reader process.'
        }
        $mainThread = $runtimeProcess.Threads | Sort-Object StartTime | Select-Object -First 1
        Send-ReaderEvent $mainThread.Id 3
        Wait-ReaderOutput $stdout 'Nothing is currently being read.' $testProcess
        Send-ReaderEvent $mainThread.Id 4
        Wait-ReaderOutput $stdout 'Speech stopped.' $testProcess
        Send-ReaderEvent $mainThread.Id 2
        if (-not $testProcess.WaitForExit(10000)) { throw 'Reader did not exit after its quit event.' }
        if ($testProcess.ExitCode -ne 0) { throw "Reader exited with code $($testProcess.ExitCode)." }
        Wait-ReaderOutput $stdout 'AI Chat Reader stopped.' $testProcess
        if ((Get-Item -LiteralPath $stderr).Length -ne 0) { throw 'Reader wrote unexpected error output.' }
        Write-Output "Portable executable run ${attempt}: startup, pause/idle, stop, and graceful exit passed."
    } finally {
        if (-not $testProcess.HasExited) {
            # Cleanup is restricted to the process tree created by this test.
            $testProcess.Kill($true)
            $testProcess.WaitForExit(5000) | Out-Null
        }
    }
}
Write-Output 'Two successive standalone runs passed; hotkeys were released between runs.'

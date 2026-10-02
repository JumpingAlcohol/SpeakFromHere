param([string]$ExecutablePath = 'outputs\v0.3.0\SpeakFromHere\SpeakFromHereConsole.exe')
$ErrorActionPreference = 'Stop'
$projectDirectory = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$sourceExecutable = Join-Path $projectDirectory $ExecutablePath
if (-not (Test-Path -LiteralPath $sourceExecutable)) { throw 'Build the executable first.' }
$testDirectory = Join-Path $projectDirectory ('work\exe-smoke-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $testDirectory -Force | Out-Null
$testExecutable = Join-Path $testDirectory 'SpeakFromHere.exe'
Copy-Item -LiteralPath $sourceExecutable -Destination $testExecutable
$testSettings = Join-Path $testDirectory 'settings.json'
# All smoke-test settings are isolated from the user's LOCALAPPDATA profile.
& $testExecutable --settings-file $testSettings --set-rate 3 --set-hotkey 'pause=Alt+J'
if ($LASTEXITCODE -ne 0) { throw 'Portable settings command failed.' }
& $testExecutable --settings-file $testSettings --show-settings
if ($LASTEXITCODE -ne 0) { throw 'Portable settings reload failed.' }
$stored = Get-Content -LiteralPath $testSettings -Raw | ConvertFrom-Json
if ($stored.rate -ne 3 -or $stored.hotkeys.pause -ne 'Alt + J') { throw 'Settings did not persist.' }

if (-not ('ReaderTest.NativeMethods' -as [type])) {
    Add-Type -Namespace ReaderTest -Name NativeMethods -MemberDefinition @'
[System.Runtime.InteropServices.DllImport("user32.dll", SetLastError = true)]
public static extern bool PostThreadMessage(uint threadId, uint message, System.UIntPtr wParam, System.IntPtr lParam);
[System.Runtime.InteropServices.DllImport("user32.dll", SetLastError = true)]
public static extern bool RegisterHotKey(System.IntPtr hwnd, int id, uint modifiers, uint key);
[System.Runtime.InteropServices.DllImport("user32.dll", SetLastError = true)]
public static extern bool UnregisterHotKey(System.IntPtr hwnd, int id);
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

function Assert-ReaderOwnsHotkey {
    param([uint32]$Modifiers, [uint32]$Key, [string]$Label)
    # Probe the actual OS registration, not merely a posted test message.
    if ([ReaderTest.NativeMethods]::RegisterHotKey([IntPtr]::Zero, 200, $Modifiers, $Key)) {
        [ReaderTest.NativeMethods]::UnregisterHotKey([IntPtr]::Zero, 200) | Out-Null
        throw "Reader did not own the expected shortcut: $Label"
    }
    $nativeError = [System.Runtime.InteropServices.Marshal]::GetLastWin32Error()
    if ($nativeError -ne 1409) { throw "Unexpected hotkey probe error for ${Label}: $nativeError" }
}

for ($attempt = 1; $attempt -le 2; $attempt++) {
    $stdout = Join-Path $testDirectory "run-$attempt.stdout.log"
    $stderr = Join-Path $testDirectory "run-$attempt.stderr.log"
    $testProcess = Start-Process -FilePath $testExecutable -WorkingDirectory $testDirectory `
        -ArgumentList @('--settings-file', ('"' + $testSettings + '"')) `
        -WindowStyle Hidden -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr
    try {
        Wait-ReaderOutput $stdout 'SpeakFromHere is running.' $testProcess
        Wait-ReaderOutput $stdout 'Experimental paragraphs:' $testProcess
        Wait-ReaderOutput $stdout 'Rate: 3' $testProcess
        Wait-ReaderOutput $stdout 'Alt + J to pause/resume' $testProcess
        Assert-ReaderOwnsHotkey 0x4001 83 'Alt + S'
        Assert-ReaderOwnsHotkey 0x4001 69 'Alt + E'
        Assert-ReaderOwnsHotkey 0x4001 74 'Alt + J'
        Assert-ReaderOwnsHotkey 0x4001 88 'Alt + X'
        Assert-ReaderOwnsHotkey 0x4005 81 'Alt + Shift + Q'
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
        Wait-ReaderOutput $stdout 'SpeakFromHere stopped.' $testProcess
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

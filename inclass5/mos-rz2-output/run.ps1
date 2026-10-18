$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    $toolDir = Join-Path $PSScriptRoot '../iot-rz/test'
    $log = [System.Collections.Generic.List[string]]::new()
    $log.Add('MOS-RZ2 | Compile, assemble, run')
    $log.Add('Executed: ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz'))
    $log.Add('Tools: ../iot-rz/test (local course bundle)')
    $log.Add('')
    $log.Add('> rz36.exe mos-rz2.txt > mos-rz2-s.txt')
    $assembly = @(& (Join-Path $toolDir 'rz36.exe') 'mos-rz2.txt')
    $compileExit = $LASTEXITCODE
    $assembly | Set-Content -Encoding ascii 'mos-rz2-s.txt'
    $log.Add("Compiler exit code: $compileExit")
    if ($compileExit -ne 0 -or $assembly -notcontains '.symbol') { throw 'Compilation failed.' }
    $log.Add('')
    $log.Add('> as21.exe mos-rz2-s.txt')
    $assemblerOutput = @(& (Join-Path $toolDir 'as21.exe') 'mos-rz2-s.txt' 2>&1)
    $assembleExit = $LASTEXITCODE
    [System.IO.File]::WriteAllText((Join-Path $PSScriptRoot 'assemble-output.txt'), ($assemblerOutput -join [Environment]::NewLine))
    foreach ($line in $assemblerOutput) { $log.Add([string]$line) }
    $log.Add("Assembler exit code: $assembleExit")
    if ($assembleExit -ne 0 -or !(Test-Path 'mos-rz2-s.obj')) { throw 'Assembly failed.' }
    $log.Add('')
    $log.Add('> sim21.exe mos-rz2-s.obj  [input: g, then q]')
    $runOutput = @(@('g', 'q') | & (Join-Path $toolDir 'sim21.exe') 'mos-rz2-s.obj' 2>&1)
    $runExit = $LASTEXITCODE
    $runOutput | Set-Content -Encoding ascii 'run-output.txt'
    foreach ($line in $runOutput) { $log.Add([string]$line) }
    $log.Add("Simulator exit code: $runExit")
    $numbers = [regex]::Matches(($runOutput -join "`n"), '\+(\d+)') | ForEach-Object { $_.Groups[1].Value }
    if ($runExit -ne 0 -or ($numbers -join ',') -ne '1,2,3,4,5') { throw 'Unexpected simulator result.' }
    $log.Add('')
    $log.Add('Verified program output: +1 +2 +3 +4 +5')
    $transcript = $log -join [Environment]::NewLine
    $transcript | Set-Content -Encoding utf8 'build-and-run-log.txt'
    Write-Output $transcript
    $escaped = [System.Net.WebUtility]::HtmlEncode($transcript)
    $html = @"
<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>MOS-RZ2 execution output</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#10141b;color:#eef3fa;padding:24px;font-family:Consolas,monospace}
main{max-width:1000px;margin:auto}h1{font:600 25px system-ui;margin:0 0 8px;color:#98e4b6}
p{color:#adb9c9;font:14px system-ui;margin:0 0 18px}
pre{margin:0;background:#171e28;border:1px solid #3a4655;padding:20px;white-space:pre-wrap;font:15px/1.45 Consolas,monospace}
</style></head><body><main><h1>MOS-RZ2 execution output</h1>
<p>Recorded command log from the local course tools. Source: mos-rz2.txt (unchanged).</p>
<pre>$escaped</pre></main></body></html>
"@
    $html | Set-Content -Encoding utf8 'output.html'
} finally {
    Pop-Location
}

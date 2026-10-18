$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

$Host.UI.RawUI.WindowTitle = 'RZ: 12 x 2 Multiplication Table'
cmd /c 'mode con cols=110 lines=40' | Out-Null
Clear-Host

Write-Host 'RZ 12 x 2 MULTIPLICATION TABLE' -ForegroundColor Cyan
Write-Host '================================' -ForegroundColor Cyan
Write-Host '[SOURCE] multiplication-table-rz.txt' -ForegroundColor Yellow
Get-Content '.\multiplication-table-rz.txt'

Write-Host '[1/3] Compile RZ source -> assembly' -ForegroundColor Yellow
& '.\rz36.exe' '.\multiplication-table-rz.txt' |
    Set-Content -Encoding ascii '.\multiplication-table-s.txt'
Write-Host '      OK: multiplication-table-s.txt' -ForegroundColor Green

Write-Host '[2/3] Assemble -> object code' -ForegroundColor Yellow
$null = 'multiplication-table-s.txt' | python '.\as21.py'
Write-Host '      OK: multiplication-table-s.obj' -ForegroundColor Green

Write-Host '[3/3] Run, then dump table[24] at RAM address 1100' -ForegroundColor Yellow
@('multiplication-table-s.obj', 'g', 'd 1100 24', 'q') | python '.\sim21.py'

Write-Host ''
Write-Host 'Expected rows:' -ForegroundColor Yellow
Write-Host '2x1..2x12 = 2 4 6 8 10 12 14 16 18 20 22 24'
Write-Host '3x1..3x12 = 3 6 9 12 15 18 21 24 27 30 33 36'

Add-Type -AssemblyName System.Drawing
Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class ScreenCaptureWindow {
    [StructLayout(LayoutKind.Sequential)]
    public struct Rect { public int Left, Top, Right, Bottom; }
    [DllImport("user32.dll")]
    public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")]
    public static extern bool GetWindowRect(IntPtr hWnd, out Rect rect);
}
'@

Start-Sleep -Milliseconds 750
$rect = New-Object ScreenCaptureWindow+Rect
$handle = [ScreenCaptureWindow]::GetForegroundWindow()
[void][ScreenCaptureWindow]::GetWindowRect($handle, [ref]$rect)
$width = $rect.Right - $rect.Left
$height = $rect.Bottom - $rect.Top
$bitmap = New-Object System.Drawing.Bitmap($width, $height)
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.CopyFromScreen($rect.Left, $rect.Top, 0, 0, $bitmap.Size)
$screenshot = Join-Path $PSScriptRoot 'multiplication-table-result.png'
$bitmap.Save($screenshot, [System.Drawing.Imaging.ImageFormat]::Png)
$graphics.Dispose()
$bitmap.Dispose()

Write-Host "Screenshot saved: $screenshot" -ForegroundColor Green
Read-Host 'Press Enter to close' | Out-Null

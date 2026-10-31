$base = Split-Path -Parent $MyInvocation.MyCommand.Path
$pidFile = Join-Path $base 'server.pid'
if (-not (Test-Path -LiteralPath $pidFile)) { Write-Output 'No recorded background service.'; exit }
$serviceId = [int](Get-Content -LiteralPath $pidFile)
$processInfo = Get-CimInstance Win32_Process -Filter "ProcessId = $serviceId"
$expected = Join-Path $base 'server.mjs'
if ($processInfo -and $processInfo.Name -eq 'node.exe' -and $processInfo.CommandLine.Contains($expected)) { Stop-Process -Id $serviceId; Write-Output 'Workbench stopped.' } else { Write-Output 'Recorded process does not match; nothing stopped.' }
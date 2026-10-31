$base = Split-Path -Parent $MyInvocation.MyCommand.Path
$pidFile = Join-Path $base 'streamlit.pid'
if (-not (Test-Path -LiteralPath $pidFile)) { Write-Output 'No recorded M1 service.'; exit }
$serviceId = [int](Get-Content -LiteralPath $pidFile)
$info = Get-CimInstance Win32_Process -Filter "ProcessId = $serviceId"
$expected = Join-Path $base '.venv\Scripts\python.exe'
if ($info -and $info.ExecutablePath -eq $expected -and $info.CommandLine.Contains('streamlit') -and $info.CommandLine.Contains('app.py')) { Stop-Process -Id $serviceId; Write-Output 'M1 stopped.' } else { Write-Output 'Process mismatch; nothing stopped.' }
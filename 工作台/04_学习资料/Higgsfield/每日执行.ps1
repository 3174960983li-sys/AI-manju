$ErrorActionPreference = 'Stop'
$OutputEncoding = New-Object System.Text.UTF8Encoding($false)
[Console]::OutputEncoding = $OutputEncoding
$libraryPath = $PSScriptRoot
$projectPath = Split-Path (Split-Path $libraryPath -Parent) -Parent
$logPath = Join-Path $libraryPath '运行记录'
New-Item -ItemType Directory -Path $logPath -Force | Out-Null
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$runLog = Join-Path $logPath ($stamp + '.log')
$summaryPath = Join-Path $logPath ($stamp + '-结果.md')
$statusPath = Join-Path $logPath '最近运行状态.json'
$started = (Get-Date).ToString('o')
function Write-RunStatus($state, $message) {
    [ordered]@{status=$state;started_at=$started;updated_at=(Get-Date).ToString('o');message=$message;log=$runLog;summary=$summaryPath} |
        ConvertTo-Json | Set-Content -LiteralPath $statusPath -Encoding UTF8
}
try {
    Write-RunStatus 'running' 'Daily collection started'
    $codexCommand = Get-Command codex -ErrorAction SilentlyContinue
    if ($codexCommand) { $codexPath = $codexCommand.Source }
    else {
        $binPath = Join-Path $env:LOCALAPPDATA 'OpenAI\Codex\bin'
        $candidate = Get-ChildItem -LiteralPath $binPath -Filter codex.exe -File -Recurse |
            Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if (-not $candidate) { throw 'Codex executable not found' }
        $codexPath = $candidate.FullName
    }
    $taskPrompt = Get-Content -LiteralPath (Join-Path $libraryPath '每日搜集任务指令.md') -Raw -Encoding UTF8
    Push-Location -LiteralPath $projectPath
    try {
        $taskPrompt | & $codexPath --search -a never exec --ephemeral --skip-git-repo-check -s workspace-write --color never -o $summaryPath - 2>&1 |
            Out-File -LiteralPath $runLog -Encoding UTF8
        $runExit = $LASTEXITCODE
    }
    finally { Pop-Location }
    if ($runExit -ne 0) { throw "Codex exit code: $runExit" }
    $day = [TimeZoneInfo]::ConvertTimeBySystemTimeZoneId([DateTime]::UtcNow, 'China Standard Time').ToString('yyyy-MM-dd')
    $reportPath = Join-Path $libraryPath ("每日精选\" + $day + "\日报.md")
    if (-not (Test-Path -LiteralPath $reportPath)) { throw 'Codex finished but the daily report is missing' }
    Write-RunStatus 'completed_check_report' 'Daily report written; inspect report for source/access limitations'
    exit 0
}
catch {
    $_ | Out-String | Add-Content -LiteralPath $runLog -Encoding UTF8
    Write-RunStatus 'failed' $_.Exception.Message
    exit 1
}


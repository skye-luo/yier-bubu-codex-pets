[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$TaskName = "YierBubuCodexPetSleep"
$TestRoot = Join-Path ([IO.Path]::GetTempPath()) ("yier-bubu-win-test-" + [Guid]::NewGuid().ToString("N"))
$TestCodexHome = Join-Path $TestRoot ".codex"

try {
    $parseErrors = New-Object System.Collections.Generic.List[object]
    foreach ($script in Get-ChildItem -LiteralPath $RepoRoot -Filter *.ps1 -Recurse) {
        $tokens = $null
        $errors = $null
        [void][System.Management.Automation.Language.Parser]::ParseFile(
            $script.FullName,
            [ref]$tokens,
            [ref]$errors
        )
        foreach ($errorRecord in $errors) { $parseErrors.Add($errorRecord) }
    }
    if ($parseErrors.Count -gt 0) {
        throw "PowerShell 语法校验失败：`n$($parseErrors -join "`n")"
    }

    . (Join-Path $RepoRoot 'scripts\activity_state.ps1')
    foreach ($case in @(@('帮我查资料做调研', 'research'), @('帮我写文章和润色', 'writing'), @('修复代码并测试', 'coding'), @('写一篇文章', 'writing'), @('查一下资料', 'research'), @('做个PPT', 'writing'))) {
        if ((Get-TaskKind -Text $case[0]).kind -ne $case[1]) { throw '任务类型识别失败' }
    }

    & (Join-Path $RepoRoot "verify.ps1")
    & (Join-Path $RepoRoot "install.ps1") -CodexHome $TestCodexHome

    foreach ($petId in @("yier", "bubu", "dianzai")) {
        $installedDir = Join-Path $TestCodexHome "pets\$petId"
        if (-not (Test-Path -LiteralPath (Join-Path $installedDir "pet.json"))) {
            throw "$petId 未正确安装 pet.json"
        }
        if (-not (Test-Path -LiteralPath (Join-Path $installedDir "spritesheet.webp"))) {
            throw "$petId 未正确安装 spritesheet.webp"
        }
    }

    & (Join-Path $RepoRoot "install-sleep-mode.ps1") -CodexHome $TestCodexHome
    & schtasks.exe /Query /TN $TaskName | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Windows 睡眠定时任务没有创建成功" }

    $scheduler = Join-Path $TestCodexHome "pet-sleep-mode\pet_sleep_scheduler.ps1"
    & $scheduler -Mode Sleep -CodexHome $TestCodexHome
    foreach ($petId in @("yier", "bubu", "dianzai")) {
        $expected = (Get-FileHash -LiteralPath (Join-Path $RepoRoot "pets\$petId\spritesheet-night.webp") -Algorithm SHA256).Hash
        $actual = (Get-FileHash -LiteralPath (Join-Path $TestCodexHome "pets\$petId\spritesheet.webp") -Algorithm SHA256).Hash
        if ($expected -ne $actual) { throw "$petId 没有切换到夜间图集" }
    }

    & $scheduler -Mode Awake -CodexHome $TestCodexHome
    foreach ($petId in @("yier", "bubu", "dianzai")) {
        $expected = (Get-FileHash -LiteralPath (Join-Path $RepoRoot "pets\$petId\spritesheet.webp") -Algorithm SHA256).Hash
        $actual = (Get-FileHash -LiteralPath (Join-Path $TestCodexHome "pets\$petId\spritesheet.webp") -Algorithm SHA256).Hash
        if ($expected -ne $actual) { throw "$petId 没有恢复白天图集" }
    }

    foreach ($kind in @('research', 'writing')) {
        foreach ($period in @('Awake', 'Sleep')) {
            $expectedPath = Join-Path $RepoRoot "pets\yier\variants\$kind-$($period.ToLowerInvariant()).webp"
            if (Test-Path -LiteralPath $expectedPath) {
                & $scheduler -Mode $period -Activity $kind -CodexHome $TestCodexHome
                foreach ($petId in @('yier', 'bubu')) {
                    $expected = (Get-FileHash -LiteralPath (Join-Path $RepoRoot "pets\$petId\variants\$kind-$($period.ToLowerInvariant()).webp")).Hash
                    $actual = (Get-FileHash -LiteralPath (Join-Path $TestCodexHome "pets\$petId\spritesheet.webp")).Hash
                    if ($expected -ne $actual) { throw "$petId $kind $period 造型切换失败" }
                }
            }
        }
    }

    $sessionDir = Join-Path (Join-Path $TestCodexHome 'sessions') (Get-Date).ToString('yyyy/MM/dd')
    New-Item -ItemType Directory -Path $sessionDir -Force | Out-Null
    $sample = @(
        @{ type = 'event_msg'; payload = @{ type = 'task_started'; turn_id = 'fixture' } },
        @{ type = 'event_msg'; payload = @{ type = 'user_message'; message = '帮我搜索资料' } }
    ) | ForEach-Object { $_ | ConvertTo-Json -Compress }
    $sample | Set-Content -LiteralPath (Join-Path $sessionDir 'fixture.jsonl') -Encoding UTF8
    if ((Get-RecentTaskActivity -CodexRoot $TestCodexHome -Now (Get-Date).AddSeconds(1)).kind -ne 'research') { throw '本地任务日志识别失败' }

    & (Join-Path $RepoRoot "uninstall-sleep-mode.ps1") -CodexHome $TestCodexHome
    & (Join-Path $RepoRoot "uninstall.ps1") -CodexHome $TestCodexHome
    Write-Host "Windows 安装、定时切换与卸载流程通过。"
}
finally {
    $previousErrorAction = $ErrorActionPreference
    $ErrorActionPreference = "SilentlyContinue"
    & schtasks.exe /Delete /TN $TaskName /F 2>$null | Out-Null
    $ErrorActionPreference = $previousErrorAction
    if (Test-Path -LiteralPath $TestRoot) {
        Remove-Item -LiteralPath $TestRoot -Recurse -Force
    }
}

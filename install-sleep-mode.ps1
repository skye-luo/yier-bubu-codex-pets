[CmdletBinding()]
param(
    [string]$CodexHome = $(
        if ($env:CODEX_HOME) { $env:CODEX_HOME }
        else { Join-Path $HOME ".codex" }
    )
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$RuntimeRoot = Join-Path $CodexHome "pet-sleep-mode"
$RuntimeAssets = Join-Path $RuntimeRoot "assets"
$SchedulerPath = Join-Path $RuntimeRoot "pet_sleep_scheduler.ps1"
$TaskName = "YierBubuCodexPetSleep"
$InstallStamp = Get-Date -Format "yyyyMMdd-HHmmss"
$BackupRoot = Join-Path $CodexHome "pets-backups\yier-bubu-sleep-mode-$InstallStamp"

foreach ($petId in @("yier", "bubu", "dianzai")) {
    $sourceDir = Join-Path $RepoRoot "pets\$petId"
    foreach ($fileName in @("pet.json", "spritesheet.webp", "spritesheet-night.webp")) {
        if (-not (Test-Path -LiteralPath (Join-Path $sourceDir $fileName) -PathType Leaf)) {
            throw "安装失败：$sourceDir 缺少 $fileName。"
        }
    }
    $targetDir = Join-Path $CodexHome "pets\$petId"
    New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $sourceDir "pet.json") -Destination (Join-Path $targetDir "pet.json") -Force
    if (-not (Test-Path -LiteralPath (Join-Path $targetDir "spritesheet.webp"))) {
        Copy-Item -LiteralPath (Join-Path $sourceDir "spritesheet.webp") -Destination (Join-Path $targetDir "spritesheet.webp")
    }
}

$previousErrorAction = $ErrorActionPreference
$ErrorActionPreference = "SilentlyContinue"
& schtasks.exe /End /TN $TaskName 2>$null | Out-Null
& schtasks.exe /Delete /TN $TaskName /F 2>$null | Out-Null
$ErrorActionPreference = $previousErrorAction

$LegacyRuntime = Join-Path $CodexHome 'yier-bubu-pet-sleep-mode'
if (Test-Path -LiteralPath $LegacyRuntime) {
    New-Item -ItemType Directory -Path $BackupRoot -Force | Out-Null
    Move-Item -LiteralPath $LegacyRuntime -Destination (Join-Path $BackupRoot 'legacy-runtime')
}

if (Test-Path -LiteralPath $RuntimeRoot) {
    New-Item -ItemType Directory -Path $BackupRoot -Force | Out-Null
    Move-Item -LiteralPath $RuntimeRoot -Destination (Join-Path $BackupRoot "runtime")
}

New-Item -ItemType Directory -Path $RuntimeAssets -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $RepoRoot "scripts\pet_sleep_scheduler.ps1") -Destination $SchedulerPath
Copy-Item -LiteralPath (Join-Path $RepoRoot "scripts\activity_state.ps1") -Destination (Join-Path $RuntimeRoot 'activity_state.ps1')
foreach ($petId in @("yier", "bubu", "dianzai")) {
    Copy-Item -LiteralPath (Join-Path $RepoRoot "pets\$petId\spritesheet.webp") -Destination (Join-Path $RuntimeAssets "$petId-awake.webp")
    Copy-Item -LiteralPath (Join-Path $RepoRoot "pets\$petId\spritesheet-night.webp") -Destination (Join-Path $RuntimeAssets "$petId-sleep.webp")
    foreach ($activityName in @('research', 'writing')) {
        foreach ($modeName in @('awake', 'sleep')) {
            $variant = Join-Path $RepoRoot "pets\$petId\variants\$activityName-$modeName.webp"
            if (Test-Path -LiteralPath $variant) {
                Copy-Item -LiteralPath $variant -Destination (Join-Path $RuntimeAssets "$petId-$activityName-$modeName.webp")
            }
        }
    }
}

$taskCommand = "powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$SchedulerPath`" -WatchSeconds 55"
& schtasks.exe /Create /TN $TaskName /SC MINUTE /MO 1 /TR $taskCommand /F | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "创建 Windows 定时任务失败（退出码 $LASTEXITCODE）。"
}

& powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $SchedulerPath -Mode Auto -CodexHome $CodexHome
if ($LASTEXITCODE -ne 0) {
    throw "首次执行睡眠模式失败（退出码 $LASTEXITCODE）。"
}

Write-Host ""
Write-Host "睡眠模式已启用：设置中为“一二”“布布”和“点仔”，不会新增独立睡觉角色。"
Write-Host "22:00–08:00 无任务时睡觉；工作、等待和检查动作保持正常。"
Write-Host "Windows 每分钟启动一次本地状态检查，在运行期间每 5 秒检查任务类型。"
if (Test-Path -LiteralPath $BackupRoot) {
    Write-Host "旧定时组件备份在：$BackupRoot"
}

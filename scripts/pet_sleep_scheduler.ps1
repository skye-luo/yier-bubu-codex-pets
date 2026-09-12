[CmdletBinding()]
param(
    [ValidateSet("Auto", "Sleep", "Awake")]
    [string]$Mode = "Auto",
    [string]$CodexHome,
    [string]$Assets,
    [string]$StatePath,
    [ValidateSet("Auto", "Coding", "Research", "Writing")]
    [string]$Activity = "Auto",
    [ValidateRange(0, 55)][int]$WatchSeconds = 0
)

$ErrorActionPreference = "Stop"
$PetIds = @("yier", "bubu", "dianzai")
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
. (Join-Path $ScriptRoot 'activity_state.ps1')
if (-not $CodexHome) {
    if ((Split-Path -Leaf $ScriptRoot) -eq "pet-sleep-mode") {
        $CodexHome = Split-Path -Parent $ScriptRoot
    }
    elseif ($env:CODEX_HOME) { $CodexHome = $env:CODEX_HOME }
    else { $CodexHome = Join-Path $HOME ".codex" }
}
$RuntimeRoot = Join-Path $CodexHome "pet-sleep-mode"
if (-not $Assets) { $Assets = Join-Path $RuntimeRoot "assets" }
if (-not $StatePath) { $StatePath = Join-Path $RuntimeRoot "state.json" }

function Copy-FileAtomicallyIfChanged {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Target
    )

    if (-not (Test-Path -LiteralPath $Source -PathType Leaf)) {
        throw "缺少睡眠模式图集：$Source"
    }
    if (Test-Path -LiteralPath $Target -PathType Leaf) {
        $sourceHash = (Get-FileHash -LiteralPath $Source -Algorithm SHA256).Hash
        $targetHash = (Get-FileHash -LiteralPath $Target -Algorithm SHA256).Hash
        if ($sourceHash -eq $targetHash) { return $false }
    }

    $targetDir = Split-Path -Parent $Target
    New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    $tempPath = Join-Path $targetDir (".{0}.{1}.tmp" -f (Split-Path -Leaf $Target), $PID)
    $backupPath = Join-Path $targetDir (".{0}.{1}.bak" -f (Split-Path -Leaf $Target), $PID)
    Copy-Item -LiteralPath $Source -Destination $tempPath -Force
    try {
        if (Test-Path -LiteralPath $Target -PathType Leaf) {
            [IO.File]::Replace($tempPath, $Target, $backupPath, $true)
        }
        else {
            Move-Item -LiteralPath $tempPath -Destination $Target
        }
    }
    finally {
        if (Test-Path -LiteralPath $tempPath) {
            Remove-Item -LiteralPath $tempPath -Force
        }
        if (Test-Path -LiteralPath $backupPath) {
            Remove-Item -LiteralPath $backupPath -Force
        }
    }
    return $true
}

function Request-PetOverlayRefresh {
    $debugPort = if ($env:CODEX_REMOTE_DEBUGGING_PORT) {
        $env:CODEX_REMOTE_DEBUGGING_PORT
    }
    else { "9341" }

    try {
        $targets = Invoke-RestMethod -Uri "http://127.0.0.1:$debugPort/json/list" -TimeoutSec 2
        $overlay = $targets | Where-Object {
            $_.type -eq "page" -and
            $_.url -like "*initialRoute=%2Favatar-overlay*" -and
            $_.webSocketDebuggerUrl
        } | Select-Object -First 1
        if (-not $overlay) { return $false }

        $socket = New-Object System.Net.WebSockets.ClientWebSocket
        $timeout = New-Object System.Threading.CancellationTokenSource
        $timeout.CancelAfter(5000)
        $socket.ConnectAsync([Uri]$overlay.webSocketDebuggerUrl, $timeout.Token).GetAwaiter().GetResult()

        $payload = [Text.Encoding]::UTF8.GetBytes('{"id":1,"method":"Page.reload","params":{"ignoreCache":true}}')
        $segment = [System.ArraySegment[byte]]::new($payload)
        $socket.SendAsync(
            $segment,
            [System.Net.WebSockets.WebSocketMessageType]::Text,
            $true,
            $timeout.Token
        ).GetAwaiter().GetResult()
        Start-Sleep -Milliseconds 150
        $socket.Dispose()
        $timeout.Dispose()
        return $true
    }
    catch {
        return $false
    }
}

function Sync-PetState {
$now = Get-Date
$resolvedMode = $Mode.ToLowerInvariant()
if ($resolvedMode -eq "auto") {
    $resolvedMode = if ($now.Hour -ge 22 -or $now.Hour -lt 8) { "sleep" } else { "awake" }
}

$previous = $null
if (Test-Path -LiteralPath $StatePath) {
    try { $previous = Get-Content -LiteralPath $StatePath -Raw -Encoding UTF8 | ConvertFrom-Json } catch { }
}
$activityKey = 'manual'
$resolvedActivity = $Activity.ToLowerInvariant()
if ($resolvedActivity -eq 'auto') {
    $detected = Get-RecentTaskActivity -CodexRoot $CodexHome -Now $now
    $resolvedActivity = $detected.kind; $activityKey = $detected.key
    if ($activityKey -and $previous.activity_key -eq $activityKey -and $previous.last_activity -in @('coding', 'research', 'writing')) {
        try {
            if (($now.ToUniversalTime() - [datetime]::Parse($previous.activity_changed_at).ToUniversalTime()).TotalSeconds -lt 30) {
                $resolvedActivity = $previous.last_activity
            }
        } catch { }
    }
}

$changedPetIds = New-Object System.Collections.Generic.List[string]
$skippedPetIds = New-Object System.Collections.Generic.List[string]
foreach ($petId in $PetIds) {
    $source = Join-Path $Assets "$petId-$resolvedMode.webp"
    $variant = Join-Path $Assets "$petId-$resolvedActivity-$resolvedMode.webp"
    if ($resolvedActivity -ne 'coding' -and (Test-Path -LiteralPath $variant -PathType Leaf)) { $source = $variant }
    $target = Join-Path $CodexHome "pets\$petId\spritesheet.webp"
    if (-not (Test-Path -LiteralPath (Split-Path -Parent $target) -PathType Container)) {
        $skippedPetIds.Add($petId)
        continue
    }
    if (Copy-FileAtomicallyIfChanged -Source $source -Target $target) {
        $changedPetIds.Add($petId)
    }
}

$state = [ordered]@{
    last_mode = $resolvedMode
    last_activity = $resolvedActivity
    activity_key = $activityKey
    activity_changed_at = $(if ($previous.last_activity -eq $resolvedActivity -and $previous.activity_key -eq $activityKey -and $previous.activity_changed_at) { $previous.activity_changed_at } else { $now.ToString('o') })
    changed_pet_ids = @($changedPetIds)
    skipped_pet_ids = @($skippedPetIds)
    updated_at = $now.ToString("o")
}
New-Item -ItemType Directory -Path (Split-Path -Parent $StatePath) -Force | Out-Null
$state | ConvertTo-Json | Set-Content -LiteralPath $StatePath -Encoding UTF8

$label = if ($resolvedMode -eq "sleep") { "夜间睡觉待机" } else { "白天普通待机" }
$changedText = if ($changedPetIds.Count -gt 0) { $changedPetIds -join "、" } else { "无需更新" }
if ($changedPetIds.Count -gt 0) { Write-Host ("{0} / {1}：{2}" -f $label, $resolvedActivity, $changedText) }
if ($skippedPetIds.Count -gt 0) {
    Write-Host "未安装，已跳过：$($skippedPetIds -join '、')"
}
if ($changedPetIds.Count -gt 0) {
    if (Request-PetOverlayRefresh) {
        Write-Host "宠物浮窗已刷新。"
    }
    else {
        Write-Host "提示：图集已切换；如果浮窗未立即变化，重启 ChatGPT/Codex 后生效。"
    }
}
}

$watchStarted = Get-Date
do {
    Sync-PetState
    if ($WatchSeconds -gt 0 -and ((Get-Date) - $watchStarted).TotalSeconds -lt $WatchSeconds) { Start-Sleep -Seconds 5 }
} while ($WatchSeconds -gt 0 -and ((Get-Date) - $watchStarted).TotalSeconds -lt $WatchSeconds)

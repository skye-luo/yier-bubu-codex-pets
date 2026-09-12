[CmdletBinding()]
param(
    [string]$CodexHome = $(
        if ($env:CODEX_HOME) { $env:CODEX_HOME }
        else { Join-Path $HOME ".codex" }
    )
)

$ErrorActionPreference = "Stop"
$PetsRoot = Join-Path $CodexHome "pets"
$UninstallStamp = Get-Date -Format "yyyyMMdd-HHmmss"
$BackupRoot = Join-Path $CodexHome "pets-backups\yier-bubu-uninstalled-$UninstallStamp"
$Moved = $false

foreach ($petId in @("yier", "bubu", "dianzai")) {
    $targetDir = Join-Path $PetsRoot $petId
    if (Test-Path -LiteralPath $targetDir) {
        New-Item -ItemType Directory -Path $BackupRoot -Force | Out-Null
        Move-Item -LiteralPath $targetDir -Destination (Join-Path $BackupRoot $petId)
        Write-Host "已移出：$petId"
        $Moved = $true
    }
}

if ($Moved) { Write-Host "宠物已移动到：$BackupRoot" }
else { Write-Host "没有发现已安装的一二、布布或点仔。" }

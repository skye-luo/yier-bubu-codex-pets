[CmdletBinding()]
param(
    [string]$CodexHome = $(
        if ($env:CODEX_HOME) { $env:CODEX_HOME }
        else { Join-Path $HOME ".codex" }
    )
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PetsRoot = Join-Path $CodexHome "pets"
$InstallStamp = Get-Date -Format "yyyyMMdd-HHmmss"
$BackupRoot = Join-Path $CodexHome "pets-backups\yier-bubu-$InstallStamp"

function Assert-PackageChecksums {
    $checksumFile = Join-Path $RepoRoot "SHA256SUMS"
    foreach ($line in Get-Content -LiteralPath $checksumFile -Encoding UTF8) {
        if ($line -notmatch '^([0-9a-fA-F]{64})\s+\./(.+)$') { continue }
        $expected = $Matches[1].ToLowerInvariant()
        $relativePath = $Matches[2] -replace '/', [IO.Path]::DirectorySeparatorChar
        $filePath = Join-Path $RepoRoot $relativePath
        if (-not (Test-Path -LiteralPath $filePath -PathType Leaf)) {
            throw "校验失败：缺少 $relativePath"
        }
        $actual = (Get-FileHash -LiteralPath $filePath -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($actual -ne $expected) {
            throw "校验失败：$relativePath 的 SHA-256 不匹配"
        }
    }
}

Assert-PackageChecksums
New-Item -ItemType Directory -Path $PetsRoot -Force | Out-Null

foreach ($petId in @("yier", "bubu", "dianzai")) {
    $sourceDir = Join-Path $RepoRoot "pets\$petId"
    $targetDir = Join-Path $PetsRoot $petId
    $manifestPath = Join-Path $sourceDir "pet.json"
    $spritesheetPath = Join-Path $sourceDir "spritesheet.webp"

    if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf) -or
        -not (Test-Path -LiteralPath $spritesheetPath -PathType Leaf)) {
        throw "安装失败：$sourceDir 缺少 pet.json 或 spritesheet.webp。"
    }

    if (Test-Path -LiteralPath $targetDir) {
        New-Item -ItemType Directory -Path $BackupRoot -Force | Out-Null
        Move-Item -LiteralPath $targetDir -Destination (Join-Path $BackupRoot $petId)
        Write-Host "已备份原有宠物：$(Join-Path $BackupRoot $petId)"
    }

    New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    Copy-Item -LiteralPath $manifestPath -Destination (Join-Path $targetDir "pet.json")
    Copy-Item -LiteralPath $spritesheetPath -Destination (Join-Path $targetDir "spritesheet.webp")
    Write-Host "已安装：$petId"
}

foreach ($legacyPetId in @("yier-sleep", "bubu-sleep")) {
    $legacyDir = Join-Path $PetsRoot $legacyPetId
    if (Test-Path -LiteralPath $legacyDir) {
        $legacyBackup = Join-Path $BackupRoot "legacy-pets"
        New-Item -ItemType Directory -Path $legacyBackup -Force | Out-Null
        Move-Item -LiteralPath $legacyDir -Destination (Join-Path $legacyBackup $legacyPetId)
        Write-Host "已移出旧独立睡觉角色：$legacyPetId"
    }
}

Write-Host ""
Write-Host "安装完成。请重启 ChatGPT/Codex，然后前往 设置 → Pets 切换一二、布布或点仔。"
Write-Host "如需 22:00–08:00 自动睡觉，再运行：.\install-sleep-mode.ps1"

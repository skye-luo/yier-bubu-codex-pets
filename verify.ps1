[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

foreach ($line in Get-Content -LiteralPath (Join-Path $RepoRoot "SHA256SUMS") -Encoding UTF8) {
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

foreach ($petId in @("yier", "bubu", "dianzai")) {
    $petDir = Join-Path $RepoRoot "pets\$petId"
    $manifest = Get-Content -LiteralPath (Join-Path $petDir "pet.json") -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($manifest.id -ne $petId) { throw "$petId 的 pet.json id 不正确" }
    if ($manifest.spritesheetPath -ne "spritesheet.webp") { throw "$petId 的 spritesheetPath 不正确" }
    foreach ($fileName in @("spritesheet.webp", "spritesheet-night.webp")) {
        $filePath = Join-Path $petDir $fileName
        if (-not (Test-Path -LiteralPath $filePath -PathType Leaf)) { throw "缺少 $filePath" }
        if ((Get-Item -LiteralPath $filePath).Length -gt 20MB) { throw "$filePath 超过 20 MiB" }
    }
}

Write-Host "一二 × 布布 Windows 宠物包校验通过。"

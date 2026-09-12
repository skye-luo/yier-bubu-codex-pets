$ErrorActionPreference = "Stop"

$ReleaseTag = if ($env:YIER_BUBU_RELEASE_TAG) { $env:YIER_BUBU_RELEASE_TAG } else { "v2.0.0" }
$ArchiveUrl = if ($env:YIER_BUBU_ARCHIVE_URL) {
    $env:YIER_BUBU_ARCHIVE_URL
}
else { "https://github.com/skye-luo/yier-bubu-codex-pets/archive/refs/tags/$ReleaseTag.zip" }
$TempRoot = Join-Path ([IO.Path]::GetTempPath()) ("yier-bubu-codex-pets-" + [Guid]::NewGuid().ToString("N"))

try {
    New-Item -ItemType Directory -Path $TempRoot -Force | Out-Null
    $ArchivePath = Join-Path $TempRoot "pet.zip"
    $ExtractRoot = Join-Path $TempRoot "package"
    Write-Host "正在下载一二 × 布布 Codex 宠物包……"
    Invoke-WebRequest -Uri $ArchiveUrl -OutFile $ArchivePath -UseBasicParsing
    Expand-Archive -LiteralPath $ArchivePath -DestinationPath $ExtractRoot
    $RepoPath = Get-ChildItem -LiteralPath $ExtractRoot -Directory | Select-Object -First 1 -ExpandProperty FullName
    if (-not $RepoPath) { throw "下载包中没有找到项目目录。" }

    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $RepoPath "install.ps1")
    if ($LASTEXITCODE -ne 0) { throw "宠物安装失败（退出码 $LASTEXITCODE）。" }
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $RepoPath "install-sleep-mode.ps1")
    if ($LASTEXITCODE -ne 0) { throw "睡眠模式安装失败（退出码 $LASTEXITCODE）。" }
    Write-Host ""
    Write-Host "全部完成。请重启 ChatGPT/Codex，然后前往 设置 → Pets 选择一二或布布。"
}
finally {
    if (Test-Path -LiteralPath $TempRoot) {
        Remove-Item -LiteralPath $TempRoot -Recurse -Force
    }
}

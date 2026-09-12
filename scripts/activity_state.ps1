# Local-only task-kind detection. Prompt/tool text is never saved or uploaded.
function Get-TaskKind {
    param([string]$Text)
    $patterns = [ordered]@{
        coding = '写代码|编程|修复|修bug|改代码|开发|实现|测试|重构|coding|debug|refactor|pytest|npm test|apply_patch'
        research = '查资料|查找资料|搜索|调研|检索|search_query|web__run|web\.run|research|browse|look up'
        writing = '写作|写文章|写报告|写文案|写正文|写周报|写方案|写邮件|做PPT|做演示|写文档|规划|润色|改写|生成文档|docx|pptx|write (?:a |an )?(?:report|article|email)|draft'
    }
    $winner = 'coding'; $best = 0
    foreach ($entry in $patterns.GetEnumerator()) {
        $score = [regex]::Matches($Text, $entry.Value, [Text.RegularExpressions.RegexOptions]::IgnoreCase).Count
        if ($score -gt $best) { $winner = $entry.Key; $best = $score }
    }
    return @{ kind = $winner; matched = ($best -gt 0) }
}

function Get-RecentTaskActivity {
    param([string]$CodexRoot, [datetime]$Now = (Get-Date))
    $candidates = @()
    foreach ($daysBack in 0..2) {
        $folder = Join-Path (Join-Path $CodexRoot 'sessions') $Now.AddDays(-$daysBack).ToString('yyyy/MM/dd')
        if (Test-Path -LiteralPath $folder) {
            $candidates += @(Get-ChildItem -LiteralPath $folder -Filter '*.jsonl' -File -ErrorAction SilentlyContinue | Where-Object {
                $_.LastWriteTime -ge $Now.AddMinutes(-30) -and $_.LastWriteTime -le $Now
            })
        }
    }
    foreach ($file in @($candidates | Sort-Object LastWriteTime -Descending | Select-Object -First 16)) {
        $stream = $null
        try {
            $stream = [IO.File]::Open($file.FullName, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::ReadWrite)
            $count = [int][Math]::Min($stream.Length, 524288)
            $null = $stream.Seek(-$count, [IO.SeekOrigin]::End)
            $buffer = New-Object byte[] $count
            $read = $stream.Read($buffer, 0, $count)
            $text = [Text.Encoding]::UTF8.GetString($buffer, 0, $read)
        } catch { continue } finally { if ($stream) { $stream.Dispose() } }
        $active = $false; $promptText = ''; $toolText = @(); $turnId = ''
        foreach ($line in ($text -split "`n")) {
            try { $record = $line.TrimStart([char]0xFEFF) | ConvertFrom-Json -ErrorAction Stop } catch { continue }
            $payload = $record.payload
            if ($record.type -eq 'event_msg') {
                if ($payload.type -eq 'task_started') { $active = $true; $promptText = ''; $toolText = @(); $turnId = [string]$payload.turn_id }
                elseif ($payload.type -in @('task_complete', 'task_aborted', 'turn_aborted')) { $active = $false }
                elseif ($payload.type -eq 'user_message') { $promptText = [string]$payload.message }
            }
            if ($record.type -eq 'response_item') {
                if ($payload.type -eq 'message' -and $payload.role -eq 'assistant' -and $payload.phase -eq 'final_answer') { $active = $false }
                if ($payload.type -eq 'message' -and $payload.role -eq 'user') {
                    $value = (@($payload.content | ForEach-Object { [string]$_.text }) -join "`n")
                    if ($value -and $value.TrimStart() -notmatch '^(<environment_context>|# AGENTS.md|<recommended_plugins>)') {
                        $promptText = $value.Substring(0, [Math]::Min(16000, $value.Length))
                    }
                } elseif ($payload.type -in @('function_call', 'custom_tool_call')) {
                    $active = $true
                    $argsText = if ($payload.arguments) { [string]$payload.arguments } else { [string]$payload.input }
                    $toolText += ([string]$payload.name + ' ' + $argsText.Substring(0, [Math]::Min(8000, $argsText.Length)))
                    $toolText = @($toolText | Select-Object -Last 8)
                }
            }
        }
        if ($active) {
            $result = Get-TaskKind -Text $promptText
            if (-not $result.matched) { $result = Get-TaskKind -Text ($toolText -join "`n") }
            $sha = [Security.Cryptography.SHA256]::Create()
            try { $key = ([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($file.Name + ':' + $turnId)))).Replace('-', '').ToLowerInvariant().Substring(0, 16) }
            finally { $sha.Dispose() }
            return @{ kind = $result.kind; key = $key }
        }
    }
    return @{ kind = 'coding'; key = '' }
}

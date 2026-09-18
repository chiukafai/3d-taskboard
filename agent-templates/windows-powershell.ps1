# Windows PowerShell 接入（Kingsley 主力机就是 Windows，所以给一份原生的）
#
# 录一条：
#   .\windows-powershell.ps1 -Title "9 月投放复盘" -Dept cmo -Status in_progress -Priority high
#
# 批量：把一个 JSON 文件灌进去
#   .\windows-powershell.ps1 -JsonFile .\tasks.json
#
# 也可以被任意 agent 调用（它只要会起进程就能用）

param(
  [string]$Title,
  [string]$Dept,
  # 不用 ValidateSet：中文/别名都交给看板引擎归一化（写"进行中"/"doing"/"wip"都行）
  [string]$Status = 'todo',
  [string]$Priority = 'medium',
  [string]$Desc,
  [string]$Source = $env:AGENT_NAME,
  [string]$JsonFile,
  [string]$Board  = $env:BOARD_URL,
  [string]$Token  = $env:BOARD_TOKEN
)

if (-not $Board) { $Board = 'http://127.0.0.1:8787' }
$Board = $Board.TrimEnd('/')
if (-not $Source) { $Source = 'powershell' }

$headers = @{ 'Content-Type' = 'application/json; charset=utf-8' }
if ($Token) { $headers['Authorization'] = "Bearer $Token" }

if ($JsonFile) {
  $raw = Get-Content -Raw -Encoding UTF8 $JsonFile
  $body = $raw                      # 直接透传（数组或 {"tasks":[...]} 都行）
}
else {
  if (-not $Title) { Write-Error '需要 -Title 或 -JsonFile'; exit 2 }
  $obj = [ordered]@{ title = $Title; source = $Source }
  if ($Dept)     { $obj.dept = $Dept }
  if ($Status)   { $obj.status = $Status }
  if ($Priority) { $obj.priority = $Priority }
  if ($Desc)     { $obj.desc = $Desc }
  $body = ($obj | ConvertTo-Json -Compress)
}

try {
  $resp = Invoke-RestMethod -Uri "$Board/api/tasks" -Method Post -Headers $headers `
            -Body ([System.Text.Encoding]::UTF8.GetBytes($body))
  Write-Host ("已录入：新增 {0} 条 / 更新 {1} 条 / 现有 {2} 条" -f $resp.added, $resp.updated, $resp.total) -ForegroundColor Green
  if ($resp.rejected.Count -gt 0) {
    Write-Host '以下条目被拒：' -ForegroundColor Yellow
    $resp.rejected | ForEach-Object { Write-Host ("  - " + $_.error) }
  }
}
catch {
  Write-Host ("连不上看板服务 $Board —— 先跑：python -m taskboard serve") -ForegroundColor Red
  Write-Host $_.Exception.Message -ForegroundColor DarkGray
  exit 1
}

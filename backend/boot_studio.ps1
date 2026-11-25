# 开机/登录自动拉起 AI 网文写作助手的前后端服务（幂等：端口已占用则跳过）
# 自动从 cc-connect 配置复用 DeepSeek 密钥注入环境（不写入文件，不打印）
$ErrorActionPreference = 'Stop'
$PY   = "$env:USERPROFILE\Miniconda3\envs\dev\python.exe"
$CFG  = "$env:USERPROFILE\.cc-connect\config.toml"
$ROOT = Split-Path -Parent $PSScriptRoot   # 项目根 D:\CluadeCodeProjects\ai-novel-studio

# 提取 deepseek api_key 注入环境
$refs = [IO.File]::ReadAllText($CFG)
$m = [regex]::Match($refs, '\[\[providers\]\]\s*name\s*=\s*"deepseek".*?api_key\s*=\s*"([^"]+)"', [Text.RegularExpressions.RegexOptions]::Singleline)
if (-not $m.Success) { throw '未在 cc-connect 配置中找到 deepseek api_key' }
$env:NOVEL_AI_PROVIDER = 'deepseek'
$env:NOVEL_AI_API_KEY  = $m.Groups[1].Value

function Port-InUse([int]$p) { (Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue) -ne $null }

# 后端 8778
if (-not (Port-InUse 8778)) {
    Start-Process -WindowStyle Hidden $PY -ArgumentList '-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8778' -WorkingDirectory "$ROOT\backend"
    Write-Host 'backend 8778 started'
} else { Write-Host 'backend 8778 already up' }

# 前端 5173
if (-not (Port-InUse 5173)) {
    $cmd = Join-Path $env:WINDIR 'System32\cmd.exe'
    Start-Process -WindowStyle Hidden $cmd -ArgumentList '/d','/c',"cd /d `"$ROOT\frontend`" && npm run dev"
    Write-Host 'frontend 5173 started'
} else { Write-Host 'frontend 5173 already up' }

Write-Host 'novel-studio services boot done'
# 启动后端（Windows PowerShell）。
# 自动从 cc-connect 配置复用 DeepSeek 凭据注入环境（不写入任何文件，不打印密钥）。
$ErrorActionPreference = 'Stop'
$PY = "$env:USERPROFILE\Miniconda3\envs\dev\python.exe"
$CFG = "$env:USERPROFILE\.cc-connect\config.toml"
Set-Location (Join-Path $PSScriptRoot '.')

# 从配置读取 deepseek api_key（正则提取，不出现在输出里）
$refs = [IO.File]::ReadAllText($CFG)
$m = [regex]::Match($refs, '\[\[providers\]\]\s*name\s*=\s*"deepseek".*?api_key\s*=\s*"([^"]+)"', [Text.RegularExpressions.RegexOptions]::Singleline)
if (-not $m.Success) { Write-Error '未在 cc-connect 配置中找到 deepseek api_key'; exit 1 }

$env:NOVEL_AI_PROVIDER = 'deepseek'
$env:NOVEL_AI_API_KEY  = $m.Groups[1].Value
# 端口：默认 8778（避开热门端口），可用 -Port 或环境变量覆盖
$port = $env:NOVEL_BACKEND_PORT
if (-not $port) { $port = '8778' }
# 不设 NOVEL_AI_BASE_URL：client.py 默认 https://api.deepseek.com（OpenAI 兼容）

Write-Host 'NOVEL_AI_PROVIDER=deepseek  (key len:' $env:NOVEL_AI_API_KEY.Length ')'
Write-Host "启动 FastAPI 于 http://127.0.0.1:$port  (前端 /api 会被代理到这里)"
& $PY -m uvicorn app.main:app --host 127.0.0.1 --port $port --reload
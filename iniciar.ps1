<#
  Sistema de Gestão Escolar — inicialização no Windows

  Uso (na pasta do sistema, pelo PowerShell):
      .\iniciar.ps1              inicia o sistema
      .\iniciar.ps1 -Demo        cria dados de demonstração (só em banco vazio) e inicia
      .\iniciar.ps1 -Porta 8080  usa outra porta
      .\iniciar.ps1 -Testes      roda os testes automáticos

  Se o Windows bloquear o script, use o arquivo iniciar.bat (dois cliques)
  ou rode antes:  Set-ExecutionPolicy -Scope Process Bypass
#>
param(
    [switch]$Demo,
    [switch]$Testes,
    [int]$Porta = 5000,
    [string]$NomeEscola = "Gestão Escolar"
)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"

function Passo($texto) { Write-Host "`n> $texto" -ForegroundColor Cyan }
function Falha($texto) {
    Write-Host "`n[ERRO] $texto" -ForegroundColor Red
    Read-Host "`nPressione Enter para fechar"
    exit 1
}

Write-Host "=============================================" -ForegroundColor DarkCyan
Write-Host "   Sistema de Gestão Escolar" -ForegroundColor White
Write-Host "=============================================" -ForegroundColor DarkCyan

# 1. Python ------------------------------------------------------------------
Passo "Procurando o Python..."
$python = $null; $pyArgs = @()
foreach ($cand in @(@("py", "-3"), @("python"), @("python3"))) {
    $exe = $cand[0]; $extra = @($cand | Select-Object -Skip 1)
    if (-not (Get-Command $exe -ErrorAction SilentlyContinue)) { continue }
    try {
        $versao = (& $exe @extra --version 2>&1) | Out-String
        if ($LASTEXITCODE -eq 0 -and $versao -match "Python 3\.(\d+)") {
            if ([int]$Matches[1] -ge 9) { $python = $exe; $pyArgs = $extra; break }
        }
    } catch { }
}
if (-not $python) {
    Falha ("Python 3.9 ou mais novo não encontrado.`n" +
           "Instale em https://www.python.org/downloads/ marcando 'Add Python to PATH',`n" +
           "ou rode no PowerShell:  winget install Python.Python.3.12")
}
Write-Host "  $($versao.Trim())"

# 2. Ambiente virtual --------------------------------------------------------
$venvPy = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPy)) {
    Passo "Criando ambiente virtual (.venv) — só na primeira vez..."
    & $python @pyArgs -m venv .venv
    if ($LASTEXITCODE -ne 0) { Falha "Não foi possível criar o ambiente virtual." }
}

# 3. Dependências (reinstala só quando requirements.txt muda) ----------------
$marca = Join-Path $PSScriptRoot ".venv\.requirements.hash"
$hash = (Get-FileHash requirements.txt -Algorithm SHA256).Hash
if (-not (Test-Path $marca) -or (Get-Content $marca -ErrorAction SilentlyContinue) -ne $hash) {
    Passo "Instalando dependências..."
    & $venvPy -m pip install --disable-pip-version-check -q -r requirements.txt
    if ($LASTEXITCODE -ne 0) { Falha "Falha ao instalar as dependências. Verifique a internet." }
    Set-Content -Path $marca -Value $hash
}

# 4. Testes (opcional) -------------------------------------------------------
if ($Testes) {
    Passo "Rodando os testes..."
    & $venvPy -m pip install --disable-pip-version-check -q pytest
    & $venvPy -m pytest -q
    Read-Host "`nPressione Enter para fechar"
    exit $LASTEXITCODE
}

# 5. Banco de dados ----------------------------------------------------------
$dados = Join-Path $PSScriptRoot "dados"
$banco = Join-Path $dados "escola.db"
New-Item -ItemType Directory -Force -Path $dados | Out-Null

if (-not (Test-Path $banco)) {
    # Aproveita um escola.db da versão antiga, se estiver na pasta ou na pasta de cima.
    $antigo = @("escola.db", "..\escola.db") | ForEach-Object { Join-Path $PSScriptRoot $_ } |
              Where-Object { Test-Path $_ } | Select-Object -First 1
    if ($antigo) {
        $resp = Read-Host "Encontrei um banco antigo em '$antigo'. Usar esses dados? (S/n)"
        if ($resp -notmatch "^[nN]") {
            Copy-Item $antigo $banco
            Write-Host "  Banco copiado para dados\escola.db (o original não foi alterado)." -ForegroundColor Green
        }
    }
}

$env:DADOS_DIR = $dados
$env:PORT = "$Porta"
$env:NOME_ESCOLA = $NomeEscola

if ($Demo) {
    Passo "Criando dados de demonstração..."
    & $venvPy seed.py
}

# 6. Porta livre? ------------------------------------------------------------
$ocupada = Get-NetTCPConnection -LocalPort $Porta -State Listen -ErrorAction SilentlyContinue
if ($ocupada) {
    Falha "A porta $Porta já está em uso (o sistema já está aberto?). Tente: .\iniciar.ps1 -Porta 8080"
}

# 7. Inicia e abre o navegador ------------------------------------------------
$url = "http://localhost:$Porta"
Passo "Iniciando o sistema em $url"
Write-Host "  Na primeira execução, a senha do administrador aparece logo abaixo." -ForegroundColor Yellow
Write-Host "  Para encerrar, feche esta janela ou pressione Ctrl+C.`n" -ForegroundColor DarkGray

Start-Job -ScriptBlock {
    param($u)
    for ($i = 0; $i -lt 30; $i++) {
        try { Invoke-WebRequest "$u/login" -UseBasicParsing -TimeoutSec 1 | Out-Null; Start-Process $u; return }
        catch { Start-Sleep -Milliseconds 500 }
    }
} -ArgumentList $url | Out-Null

& $venvPy app.py
if ($LASTEXITCODE -ne 0) { Falha "O sistema parou com erro (código $LASTEXITCODE)." }

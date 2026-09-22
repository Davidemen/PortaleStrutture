<#
Server dell'ufficio in background (Windows): resta acceso anche chiudendo il terminale.

    powershell -ExecutionPolicy Bypass -File scripts\server.ps1 avvia|ferma|riavvia|stato

Alias `strutture` e avvio automatico all'accesso: docs/CONSEGNA.md, sezione "Server". Usa scripts/serve_live.py
(CLAUDE.md, regola 2) con il Python di .venv, cosi' il PID sulla porta e' quello del server. `ferma` agisce solo sul
processo in ascolto sulla porta, e solo se e' il Python di questo progetto: mai per nome.
Testi senza lettere accentate: PowerShell 5.1 legge i .ps1 senza BOM come ANSI.
#>
param(
    [ValidateSet('avvia', 'ferma', 'riavvia', 'stato')]
    [string]$Comando = 'stato'
)

# Solo il server dell'ufficio: branch main, porta 8000, tutte le interfacce. develop e altri branch: CLAUDE.md, regole 1-2.
$Porta = 8000
$Indirizzo = '0.0.0.0'
$Ramo = 'main'
$ErrorActionPreference = 'Stop'
$Radice = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Radice '.venv\Scripts\python.exe'
$Log = Join-Path $Radice 'var\server.log'
$LogErrori = Join-Path $Radice 'var\server-errori.log'
$SecondiAttesa = 20

function Get-ServerPid {
    $c = Get-NetTCPConnection -LocalPort $Porta -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($c) { return [int]$c.OwningProcess }
    return $null
}

# Il python.exe di .venv e' un lanciatore: il processo in ascolto e' suo figlio (Python di sistema).
function Test-NostroServer([int]$id) {
    $p = Get-CimInstance Win32_Process -Filter "ProcessId=$id" -ErrorAction SilentlyContinue
    if (-not $p -or $p.CommandLine -notlike '*serve_live.py*') { return $false }
    if ($p.ExecutablePath -eq $Python) { return $true }
    $padre = Get-CimInstance Win32_Process -Filter "ProcessId=$($p.ParentProcessId)" -ErrorAction SilentlyContinue
    return [bool]($padre -and $padre.ExecutablePath -eq $Python)
}

function Show-Indirizzi {
    Write-Host "  Da questo PC:     http://127.0.0.1:$Porta/"
    if ($Indirizzo -in @('0.0.0.0', '::')) {
        Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
            Where-Object { $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*' } |
            ForEach-Object { Write-Host "  Da altri PC:      http://$($_.IPAddress):$Porta/" }
    }
}

function Start-Server {
    $esistente = Get-ServerPid
    if ($esistente) {
        Write-Host "Il server risulta gia' acceso sulla porta $Porta (PID $esistente)."
        Show-Indirizzi
        return
    }
    if (-not (Test-Path $Python)) {
        throw "Ambiente Python assente ($Python). Eseguire una volta 'uv sync' nella cartella del progetto."
    }
    $ramoAttuale = git -C $Radice branch --show-current
    if ($ramoAttuale -ne $Ramo) {
        throw "La cartella $Radice e' sul branch '$ramoAttuale': il server dell'ufficio parte solo da '$Ramo'."
    }
    New-Item -ItemType Directory -Force (Split-Path $Log) | Out-Null
    $argomenti = @('scripts/serve_live.py', '--host', $Indirizzo, '--port', "$Porta")
    $p = Start-Process -FilePath $Python -ArgumentList $argomenti -WorkingDirectory $Radice -WindowStyle Hidden `
        -RedirectStandardOutput $Log -RedirectStandardError $LogErrori -PassThru
    for ($i = 0; $i -lt $SecondiAttesa * 2; $i++) {
        $id = Get-ServerPid
        if ($id) {
            Write-Host "Server avviato sulla porta $Porta (PID $id). Log in var\server.log e var\server-errori.log."
            Show-Indirizzi
            return
        }
        if ($p.HasExited) { break }
        Start-Sleep -Milliseconds 500
    }
    Write-Host "Il server non risponde dopo $SecondiAttesa s. Ultime righe di var\server-errori.log:"
    if (Test-Path $LogErrori) { Get-Content $LogErrori -Tail 15 | Write-Host }
    exit 1
}

function Stop-Server {
    $id = Get-ServerPid
    if (-not $id) {
        Write-Host "Nessun server in ascolto sulla porta $Porta."
        return
    }
    if (-not (Test-NostroServer $id)) {
        throw "Sulla porta $Porta ascolta un altro programma (PID $id): non lo fermo."
    }
    Stop-Process -Id $id
    Wait-Process -Id $id -Timeout 10 -ErrorAction SilentlyContinue
    Write-Host "Server fermato (PID $id)."
}

switch ($Comando) {
    'avvia' { Start-Server }
    'ferma' { Stop-Server }
    'riavvia' { Stop-Server; Start-Server }
    'stato' {
        $id = Get-ServerPid
        if ($id) {
            Write-Host "Server acceso sulla porta $Porta (PID $id)."
            Show-Indirizzi
        } else {
            Write-Host "Server spento (porta $Porta libera)."
        }
    }
}

# MMarket Installer
# Uso: irm https://raw.githubusercontent.com/MaaruAx/MMarket/main/install.ps1 | iex

$ProgressPreference = "SilentlyContinue"

$REPO_ZIP    = "https://github.com/MaaruAx/MMarket/archive/refs/heads/main.zip"
$INSTALL_DIR = "$env:LOCALAPPDATA\MMarket"
$PYTHON_MIN  = [Version]"3.8.0"
$PYTHON_MAX  = [Version]"3.13.99"

function Write-Step { param([string]$T); Write-Host "  >> $T" -ForegroundColor White }
function Write-Ok   { param([string]$T); Write-Host "  OK $T" -ForegroundColor Green }
function Write-Fail { param([string]$T); Write-Host "  FAIL $T" -ForegroundColor Red }

function Write-Header {
    Clear-Host
    Write-Host ""
    Write-Host "  MMarket - Marketplace para DaVinci Resolve" -ForegroundColor Yellow
    Write-Host "  github.com/MaaruAx/MMarket" -ForegroundColor DarkGray
    Write-Host ""
}

function Test-PythonCmd {
    param([string]$Cmd)
    try {
        $out = & $Cmd --version 2>&1
        if ($out -match "Python (\d+\.\d+\.\d+)") {
            $ver = [Version]$Matches[1]
            if ($ver -ge $PYTHON_MIN -and $ver -le $PYTHON_MAX) {
                $arch = & $Cmd -c "import struct; print(struct.calcsize('P') * 8)" 2>&1
                if ($arch -eq "64") { return $true }
            }
        }
    } catch {}
    return $false
}

function Find-Python {
    foreach ($cmd in @("python", "python3", "py")) {
        if (Test-PythonCmd $cmd) { return $cmd }
    }
    return $null
}

function Install-Python {
    Write-Step "Python compatible no encontrado. Descargando Python 3.11..."
    $url = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
    $tmp = "$env:TEMP\python_setup.exe"
    try {
        Invoke-WebRequest -Uri $url -OutFile $tmp
        Write-Step "Instalando Python 3.11..."
        Start-Process -FilePath $tmp -ArgumentList "/quiet","InstallAllUsers=0","PrependPath=1","Include_pip=1" -Wait
        Remove-Item $tmp -ErrorAction SilentlyContinue
        $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH","User") + ";" + [System.Environment]::GetEnvironmentVariable("PATH","Machine")
        Write-Ok "Python 3.11 instalado"
        return "python"
    } catch {
        Write-Fail "No se pudo instalar Python. Instala Python 3.11 manualmente desde python.org"
        exit 1
    }
}

function Get-MMarket {
    if (Test-Path $INSTALL_DIR) {
        Write-Step "Actualizando instalacion en $INSTALL_DIR..."
    } else {
        Write-Step "Instalando en $INSTALL_DIR..."
        New-Item -ItemType Directory -Path $INSTALL_DIR -Force | Out-Null
    }

    Write-Step "Descargando MMarket desde GitHub..."
    $zip = "$env:TEMP\MMarket.zip"
    try {
        Invoke-WebRequest -Uri $REPO_ZIP -OutFile $zip
    } catch {
        Write-Fail "No se pudo descargar. Verifica tu conexion a internet."
        exit 1
    }

    Write-Step "Extrayendo archivos..."
    $ext = "$env:TEMP\MMarket_ext"
    if (Test-Path $ext) { Remove-Item $ext -Recurse -Force }
    Expand-Archive -Path $zip -DestinationPath $ext -Force
    Remove-Item $zip -ErrorAction SilentlyContinue

    $src = Get-ChildItem $ext | Select-Object -First 1
    if (-not $src) { Write-Fail "Error al extraer archivos."; exit 1 }

    Get-ChildItem $INSTALL_DIR -Exclude "user_themes" |
        Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Copy-Item "$($src.FullName)\*" -Destination $INSTALL_DIR -Recurse -Force
    Remove-Item $ext -Recurse -Force -ErrorAction SilentlyContinue

    Write-Ok "Archivos copiados"
}

function Install-Deps {
    param([string]$Cmd)
    $req = "$INSTALL_DIR\requirements.txt"
    if (-not (Test-Path $req)) { Write-Fail "requirements.txt no encontrado"; exit 1 }

    Write-Step "Instalando dependencias..."

    # Actualizar pip ignorando warnings
    & $Cmd -m pip install --quiet --upgrade pip 2>&1 | Out-Null

    # Instalar dependencias - capturar output para verificar resultado real
    $out = & $Cmd -m pip install --quiet -r $req 2>&1
    $exitCode = $LASTEXITCODE

    # Verificar que pywebview quedo instalado aunque haya warnings
    $check = & $Cmd -c "import webview; print('ok')" 2>&1
    if ($check -eq "ok") {
        Write-Ok "Dependencias instaladas"
    } else {
        # Intentar instalacion directa como fallback
        & $Cmd -m pip install pywebview 2>&1 | Out-Null
        $check2 = & $Cmd -c "import webview; print('ok')" 2>&1
        if ($check2 -eq "ok") {
            Write-Ok "Dependencias instaladas"
        } else {
            Write-Fail "No se pudo instalar pywebview: $out"
            exit 1
        }
    }
}

function New-Shortcut {
    param([string]$Cmd)
    Write-Step "Creando acceso directo..."
    $pyPath = & $Cmd -c "import sys; print(sys.executable)" 2>&1
    $script = "$INSTALL_DIR\app\main.py"
    $lnk    = "$env:USERPROFILE\Desktop\MMarket.lnk"
    $icon   = "$INSTALL_DIR\app\ui\assets\icon.ico"

    $wsh      = New-Object -ComObject WScript.Shell
    $shortcut = $wsh.CreateShortcut($lnk)
    $shortcut.TargetPath       = $pyPath
    $shortcut.Arguments        = "`"$script`""
    $shortcut.WorkingDirectory = "$INSTALL_DIR\app"
    $shortcut.Description      = "MMarket - Marketplace para DaVinci Resolve"
    if (Test-Path $icon) { $shortcut.IconLocation = $icon }
    $shortcut.Save()
    Write-Ok "Acceso directo creado en el escritorio"
}

# -- Main --

Write-Header

Write-Step "Verificando Python (3.8 - 3.13, 64-bit)..."
$pyCmd = Find-Python
if (-not $pyCmd) {
    $pyCmd = Install-Python
} else {
    $ver = & $pyCmd --version 2>&1
    Write-Ok "$ver (64-bit) encontrado"
}

Get-MMarket
Install-Deps -Cmd $pyCmd
New-Shortcut -Cmd $pyCmd

Write-Host ""
Write-Ok "MMarket instalado correctamente!"
Write-Host ""
Write-Host "  Abre MMarket desde el acceso directo en tu escritorio." -ForegroundColor Cyan
Write-Host "  La app se actualiza sola al abrirla." -ForegroundColor DarkGray
Write-Host ""

$r = Read-Host "  Abrir MMarket ahora? (S/n)"
if ($r -ne "n" -and $r -ne "N") {
    $pyPath = & $pyCmd -c "import sys; print(sys.executable)" 2>&1
    Start-Process -FilePath $pyPath -ArgumentList "`"$INSTALL_DIR\app\main.py`"" -WorkingDirectory "$INSTALL_DIR\app"
}

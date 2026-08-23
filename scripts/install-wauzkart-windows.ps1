$ErrorActionPreference = "Stop"

$Repo = "Fetelker-Nils/wauzkart"
$ExeUrl = $env:WAUZKART_WINDOWS_EXE_URL
if ([string]::IsNullOrWhiteSpace($ExeUrl)) {
    $ExeUrl = "https://github.com/$Repo/releases/latest/download/wauzkart-windows.exe"
}

$InstallDir = Join-Path $env:LOCALAPPDATA "WauzKart"
$InstallFile = Join-Path $InstallDir "wauzkart.exe"
$TempFile = Join-Path ([System.IO.Path]::GetTempPath()) "wauzkart-windows.exe"
$DesktopShortcut = Join-Path ([Environment]::GetFolderPath("Desktop")) "Wauz Kart.lnk"
$StartMenuDir = Join-Path ([Environment]::GetFolderPath("Programs")) "Wauz Kart"
$StartMenuShortcut = Join-Path $StartMenuDir "Wauz Kart.lnk"

function Info($Message) {
    Write-Host ""
    Write-Host "[Wauz Kart] $Message"
}

Info "Lade die neueste Windows-Version herunter..."
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
Invoke-WebRequest -Uri $ExeUrl -OutFile $TempFile -UseBasicParsing

Info "Installiere oder aktualisiere Wauz Kart..."
$running = Get-Process -Name "wauzkart" -ErrorAction SilentlyContinue
if ($running) {
    Info "Wauz Kart laeuft noch. Beende es vor dem Update."
    throw "Wauz Kart muss vor dem Update geschlossen werden."
}

Move-Item -Force -Path $TempFile -Destination $InstallFile

Info "Erstelle Verknuepfungen..."
New-Item -ItemType Directory -Force -Path $StartMenuDir | Out-Null
$shell = New-Object -ComObject WScript.Shell
foreach ($shortcutPath in @($DesktopShortcut, $StartMenuShortcut)) {
    $shortcut = $shell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = $InstallFile
    $shortcut.WorkingDirectory = $InstallDir
    $shortcut.IconLocation = "$InstallFile,0"
    $shortcut.Save()
}

Info "Fertig. Beim naechsten Ausfuehren dieses Installers wird automatisch auf die neueste Version aktualisiert."
Info "Start: $InstallFile"

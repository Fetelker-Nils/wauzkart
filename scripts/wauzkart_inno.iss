#define MyAppName "Wauz Kart"
#define MyAppVersion "1.0.46"
#define MyAppExeName "wauzkart.exe"

[Setup]
AppId={{2E614F78-82B2-41EA-A0BB-57A32A570001}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=Wauz Kart
DefaultDirName={localappdata}\WauzKart
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\Output
OutputBaseFilename=install-wauzkart-windows
Compression=lzma2
SolidCompression=no
SetupIconFile=..\assets\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
CloseApplications=yes
RestartApplications=no
WizardStyle=modern
WizardImageFile=..\assets\installer_wizard.bmp
WizardSmallImageFile=..\assets\installer_small.bmp
WizardImageStretch=no
WizardImageBackColor=$001A100B
WizardSmallImageBackColor=$001A100B

[Languages]
Name: "german"; MessagesFile: "compiler:Languages\German.isl"

[Messages]
WelcomeLabel1=Willkommen bei Wauz Kart
WelcomeLabel2=Dieser Setup-Assistent installiert Wauz Kart auf deinem Computer.%n%nMach dich bereit fuer Rennen, Items, LAN-Modus und Highlights.
ButtonBack=< Zurueck
ButtonNext=Weiter >
ButtonInstall=Installieren
ButtonFinish=Fertig
ButtonCancel=Abbrechen
FinishedHeadingLabel=Wauz Kart ist startklar
FinishedLabel=Wauz Kart wurde installiert. Du kannst direkt losfahren.

[Tasks]
Name: "desktopicon"; Description: "Desktop-Verknuepfung erstellen"; GroupDescription: "Verknuepfungen:"; Flags: unchecked

[Files]
Source: "..\dist\wauzkart\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\src\wauzkart\*"; DestDir: "{app}\src\wauzkart"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "__pycache__\*,*.pyc,*.pyo"

[InstallDelete]
Type: filesandordirs; Name: "{app}\src"

[Icons]
Name: "{group}\Wauz Kart"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{autodesktop}\Wauz Kart"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Wauz Kart starten"; Flags: nowait postinstall skipifsilent
Filename: "{app}\{#MyAppExeName}"; Flags: nowait skipifnotsilent

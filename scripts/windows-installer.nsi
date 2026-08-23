!ifndef VERSION
  !define VERSION "1.0.0"
!endif

!define APP_NAME "Wauz Kart"
!define APP_EXE "wauzkart.exe"
!define COMPANY "Wauz Kart"
!define INSTALL_DIR "$LOCALAPPDATA\WauzKart"

Unicode true
Name "${APP_NAME}"
OutFile "install-wauzkart-windows.exe"
InstallDir "${INSTALL_DIR}"
RequestExecutionLevel user

VIProductVersion "${VERSION}.0"
VIAddVersionKey "ProductName" "${APP_NAME}"
VIAddVersionKey "CompanyName" "${COMPANY}"
VIAddVersionKey "FileDescription" "${APP_NAME} Installer"
VIAddVersionKey "FileVersion" "${VERSION}"
VIAddVersionKey "ProductVersion" "${VERSION}"
VIAddVersionKey "LegalCopyright" "${COMPANY}"

!include "MUI2.nsh"
!define MUI_ABORTWARNING
!define MUI_ICON "assets\icon.ico"
!define MUI_UNICON "assets\icon.ico"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "German"

Section "Wauz Kart" SecMain
  SetOutPath "$INSTDIR"
  File /oname=${APP_EXE} "dist\wauzkart.exe"

  WriteUninstaller "$INSTDIR\uninstall.exe"

  CreateDirectory "$SMPROGRAMS\Wauz Kart"
  CreateShortcut "$SMPROGRAMS\Wauz Kart\Wauz Kart.lnk" "$INSTDIR\${APP_EXE}" "" "$INSTDIR\${APP_EXE}" 0
  CreateShortcut "$SMPROGRAMS\Wauz Kart\Deinstallieren.lnk" "$INSTDIR\uninstall.exe"
  CreateShortcut "$DESKTOP\Wauz Kart.lnk" "$INSTDIR\${APP_EXE}" "" "$INSTDIR\${APP_EXE}" 0

  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\WauzKart" "DisplayName" "${APP_NAME}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\WauzKart" "DisplayVersion" "${VERSION}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\WauzKart" "Publisher" "${COMPANY}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\WauzKart" "InstallLocation" "$INSTDIR"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\WauzKart" "DisplayIcon" "$INSTDIR\${APP_EXE}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\WauzKart" "UninstallString" "$INSTDIR\uninstall.exe"
SectionEnd

Section "Uninstall"
  Delete "$DESKTOP\Wauz Kart.lnk"
  Delete "$SMPROGRAMS\Wauz Kart\Wauz Kart.lnk"
  Delete "$SMPROGRAMS\Wauz Kart\Deinstallieren.lnk"
  RMDir "$SMPROGRAMS\Wauz Kart"

  Delete "$INSTDIR\${APP_EXE}"
  Delete "$INSTDIR\uninstall.exe"
  RMDir "$INSTDIR"

  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\WauzKart"
SectionEnd

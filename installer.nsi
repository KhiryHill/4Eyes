; installer.nsi
; NSIS script to create a Windows installer for 4Eyes

!include "MUI2.nsh"

Name "4Eyes"
OutFile "dist\4Eyes_Setup.exe"
InstallDir "$PROGRAMFILES\4Eyes"
InstallDirRegKey HKCU "Software\4Eyes" ""
RequestExecutionLevel admin

!define MUI_ABORTWARNING
!define MUI_ICON "assets\icon.ico"
!define MUI_UNICON "assets\icon.ico"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

Section "4Eyes" SecMain
  SetOutPath "$INSTDIR"
  File /r "dist\4Eyes\*.*"

  ; Create Start Menu shortcut
  CreateDirectory "$SMPROGRAMS\4Eyes"
  CreateShortcut "$SMPROGRAMS\4Eyes\4Eyes.lnk" "$INSTDIR\4Eyes.exe"
  CreateShortcut "$DESKTOP\4Eyes.lnk" "$INSTDIR\4Eyes.exe"

  ; Add to startup
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "4Eyes" "$INSTDIR\4Eyes.exe"

  ; Write uninstaller
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  WriteRegStr HKCU "Software\4Eyes" "" "$INSTDIR"
SectionEnd

Section "Uninstall"
  Delete "$INSTDIR\Uninstall.exe"
  RMDir /r "$INSTDIR"
  Delete "$SMPROGRAMS\4Eyes\4Eyes.lnk"
  Delete "$DESKTOP\4Eyes.lnk"
  RMDir "$SMPROGRAMS\4Eyes"
  DeleteRegKey HKCU "Software\4Eyes"
  DeleteRegValue HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "4Eyes"
SectionEnd

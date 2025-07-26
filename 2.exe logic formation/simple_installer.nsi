; SignBridge Pro - Full Auto Installer
!define APP_NAME "SignBridge Pro"
!define APP_VERSION "1.0"
!define APP_EXECUTABLE "SignBridgePro.exe"

!include "MUI2.nsh"

Name "${APP_NAME} ${APP_VERSION}"
OutFile "SignBridgePro_Setup.exe"
InstallDir "$PROGRAMFILES64\${APP_NAME}"
RequestExecutionLevel admin
SetCompressor lzma

!define MUI_ABORTWARNING
!define MUI_ICON "assets\signbridge_icon.ico"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"

Section "Install"
    SetOutPath "$INSTDIR"
    
    ; Core Files
    File "dist\${APP_EXECUTABLE}"
    File /nonfatal "dist\README.txt"
    File /nonfatal "dist\settings.json"
    File /nonfatal "dist\caption_output.txt"

    ; Models
    SetOutPath "$INSTDIR\model"
    File "dist\model\sign_model.h5"
    File "dist\model\label_map.npy"

    ; Assets
    SetOutPath "$INSTDIR\assets"
    File /r "dist\assets\*"

    ; Scripts
    SetOutPath "$INSTDIR\scripts"
    File /r "dist\scripts\*"

    ; OBS Installers
    SetOutPath "$INSTDIR\obs_installers"
    File /nonfatal "installers\OBS-Studio-31.1.1-Windows-x64-Installer.exe"
    File /nonfatal "installers\OBS-VirtualCam2.0.4-Installer.exe"

    ; Visual C++ Redistributable
    SetOutPath "$TEMP"
    File "dependencies\vc_redist.x64.exe"
    DetailPrint "Installing Visual C++ Redistributable..."
    ExecWait "$TEMP\vc_redist.x64.exe /quiet /norestart"
    Delete "$TEMP\vc_redist.x64.exe"

    ; Install OBS silently (optional)
    DetailPrint "Installing OBS Studio silently..."
    ExecWait "$INSTDIR\obs_installers\OBS-Studio-31.1.1-Windows-x64-Installer.exe /S"

    DetailPrint "Installing OBS VirtualCam silently..."
    ExecWait "$INSTDIR\obs_installers\OBS-VirtualCam2.0.4-Installer.exe /S"

    ; User Config Setup
    CreateDirectory "$APPDATA\${APP_NAME}"
    IfFileExists "$APPDATA\${APP_NAME}\settings.json" settings_exist 0
    CopyFiles /SILENT "$INSTDIR\settings.json" "$APPDATA\${APP_NAME}\settings.json"
    settings_exist:

    ; Shortcuts
    CreateDirectory "$SMPROGRAMS\${APP_NAME}"
    CreateShortCut "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" "$INSTDIR\${APP_EXECUTABLE}"
    CreateShortCut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\${APP_EXECUTABLE}"

    ; Registry
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayName" "${APP_NAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "UninstallString" "$INSTDIR\uninstall.exe"
    WriteRegStr HKLM "Software\${APP_NAME}" "InstallDir" "$INSTDIR"
    WriteRegStr HKLM "Software\${APP_NAME}" "UserDataDir" "$APPDATA\${APP_NAME}"
    
    ; Uninstaller
    WriteUninstaller "$INSTDIR\uninstall.exe"

    ; Run App After Install
    Exec "$INSTDIR\${APP_EXECUTABLE}"
SectionEnd

Section "Uninstall"
    MessageBox MB_YESNO "Do you want to keep your settings and data?" IDYES keep_settings
    RMDir /r "$APPDATA\${APP_NAME}"
    Goto remove_program

    keep_settings:
    DetailPrint "Keeping user data in $APPDATA\${APP_NAME}"

    remove_program:
    Delete "$INSTDIR\${APP_EXECUTABLE}"
    Delete "$INSTDIR\README.txt"
    Delete "$INSTDIR\settings.json"
    Delete "$INSTDIR\caption_output.txt"
    Delete "$INSTDIR\uninstall.exe"
    RMDir /r "$INSTDIR\model"
    RMDir /r "$INSTDIR\assets"
    RMDir /r "$INSTDIR\scripts"
    RMDir /r "$INSTDIR\obs_installers"
    RMDir "$INSTDIR"
    
    Delete "$DESKTOP\${APP_NAME}.lnk"
    RMDir /r "$SMPROGRAMS\${APP_NAME}"

    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}"
    DeleteRegKey HKLM "Software\${APP_NAME}"
SectionEnd

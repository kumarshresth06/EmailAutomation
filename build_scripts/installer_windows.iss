; ============================================================
; installer_windows.iss — Inno Setup script
; Cold Outreach Automator Windows Installer
;
; Compile with:
;   ISCC build_scripts\installer_windows.iss
; Or via Inno Setup GUI: File → Open → this file → Build → Compile
; ============================================================

#define AppName      "Cold Outreach Automator"
#define AppVersion   "1.0.0"
#define AppPublisher "Your Name"
#define AppURL       "https://github.com/yourusername/EmailAutomation"
#define AppExeName   "ColdOutreachAutomator.exe"
#define SourceDir    "..\dist\ColdOutreachAutomator"

[Setup]
; ── Installer identity ──────────────────────────────────────────
AppId={{A3F2C1B0-9D4E-4F88-B3A2-7C8D9E0F1A2B}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
AllowNoIcons=yes
; ── Output ──────────────────────────────────────────────────────
OutputDir=..\dist
OutputBaseFilename=ColdOutreachAutomator_Setup
; ── Appearance ──────────────────────────────────────────────────
SetupIconFile=..\assets\icon.ico
WizardStyle=modern
; ── Compression (LZMA2 = best ratio) ────────────────────────────
Compression=lzma2/ultra64
SolidCompression=yes
; ── Privileges ──────────────────────────────────────────────────
PrivilegesRequired=lowest          ; install per-user, no UAC prompt
PrivilegesRequiredOverridesAllowed=dialog
; ── 64-bit target ───────────────────────────────────────────────
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
; ── Misc ────────────────────────────────────────────────────────
UninstallDisplayIcon={app}\{#AppExeName}
DisableProgramGroupPage=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Copy the entire PyInstaller one-folder output
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Start Menu shortcut
Name: "{group}\{#AppName}";          Filename: "{app}\{#AppExeName}";  IconFilename: "{app}\assets\icon.ico"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"
; Optional desktop shortcut (created only if user ticked the task)
Name: "{autodesktop}\{#AppName}";    Filename: "{app}\{#AppExeName}";  IconFilename: "{app}\assets\icon.ico"; Tasks: desktopicon

[Run]
; Offer to launch the app immediately after install
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(AppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

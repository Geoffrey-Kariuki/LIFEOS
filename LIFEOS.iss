#define MyAppName "LIFEOS"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "LIFEOS"
#define MyAppExeName "LIFEOS.exe"

[Setup]
AppId={{8F4B7A8C-3D91-4C9A-B6D4-LIFEOS2026}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}

DefaultDirName={autopf}\LIFEOS
DefaultGroupName=LIFEOS

OutputDir=installer
OutputBaseFilename=LIFEOS-Setup-1.0.0

Compression=lzma
SolidCompression=yes

WizardStyle=modern
PrivilegesRequired=lowest

UninstallDisplayIcon={app}\{#MyAppExeName}

[Files]
Source: "dist\LIFEOS\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\LIFEOS"; Filename: "{app}\LIFEOS.exe"
Name: "{autodesktop}\LIFEOS"; Filename: "{app}\LIFEOS.exe"
[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch LIFEOS"; Flags: nowait postinstall skipifsilent
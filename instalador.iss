; Script do Inno Setup para o instalador do StickyDesk.
; Compile com o Inno Setup Compiler (ISCC.exe) apontando para este arquivo.

#define MyAppName "StickyDesk"
#define MyAppVersion "1.2.0"
#define MyAppPublisher "StickyDesk"
#define MyAppExeName "StickyDesk.exe"

[Setup]
AppId={{B5C2A9F0-1234-4ABC-9E10-STICKYDESK001}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=installer_output
OutputBaseFilename=StickyDesk-Setup-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
DisableProgramGroupPage=yes

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Files]
Source: "dist\StickyDesk.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Abrir StickyDesk agora"; Flags: nowait postinstall skipifsilent

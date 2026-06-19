[Setup]
AppName=StickyDesk
AppVersion=1.1.0
DefaultDirName={autopf}\StickyDesk
DefaultGroupName=StickyDesk
UninstallDisplayIcon={app}\StickyDesk.exe
Compression=lzma2
SolidCompression=yes
OutputDir=.\installer_output
OutputBaseFilename=StickyDesk_Setup

[Files]
; Copia o executável criado pelo PyInstaller para a pasta de instalação
Source: ".\dist\StickyDesk.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Cria o atalho na Área de Trabalho com o ícone embutido no executável
Name: "{autodesktop}\StickyDesk"; Filename: "{app}\StickyDesk.exe"; IconFilename: "{app}\StickyDesk.exe"
; Cria o atalho no Menu Iniciar do Windows
Name: "{group}\StickyDesk"; Filename: "{app}\StickyDesk.exe"

[Run]
; Caixa de seleção para rodar o app assim que concluir a instalação
Filename: "{app}\StickyDesk.exe"; Description: "Lançar StickyDesk agora"; Flags: nowait postinstall skipifsilent

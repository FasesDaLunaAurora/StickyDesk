# Cria um atalho do StickyDesk na Área de Trabalho do Windows.
# Uso: clique direito neste arquivo > "Executar com PowerShell"
#      (ou rode `powershell -ExecutionPolicy Bypass -File criar_atalho.ps1`)

$projectDir = $PSScriptRoot
$batPath = Join-Path $projectDir "StickyDesk.bat"
$desktopDir = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktopDir "StickyDesk.lnk"

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $batPath
$shortcut.WorkingDirectory = $projectDir
$shortcut.WindowStyle = 7  # Minimizado
$shortcut.IconLocation = "$projectDir\app\ui\..\..\StickyDesk.bat,0"
$shortcut.Description = "Abrir notas do StickyDesk"
$shortcut.Save()

Write-Host "Atalho criado em: $shortcutPath"
Write-Host "De agora em diante, basta dar duplo clique nele para abrir o StickyDesk."

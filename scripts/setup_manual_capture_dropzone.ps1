param(
    [string]$DropDir = "",
    [string]$ShortcutName = "E2E Evidence Drop.lnk"
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($DropDir)) {
    $desktopPath = [Environment]::GetFolderPath("Desktop")
    if ([string]::IsNullOrWhiteSpace($desktopPath)) {
        $desktopPath = "$env:USERPROFILE\Desktop"
    }
    $DropDir = Join-Path $desktopPath "Evidence_Drop"
}

if (-not (Test-Path -LiteralPath $DropDir)) {
    New-Item -ItemType Directory -Path $DropDir -Force | Out-Null
}

$desktopDir = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktopDir $ShortcutName

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $DropDir
$shortcut.WorkingDirectory = $DropDir
$shortcut.Description = "Drop REAL_CAPTURE evidence files into this folder."
$shortcut.IconLocation = "$env:SystemRoot\System32\shell32.dll,3"
$shortcut.Save()

Write-Host "Drop directory ready: $DropDir"
Write-Host "Desktop shortcut created: $shortcutPath"

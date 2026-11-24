# Defaults are derived from where this script lives and from the current user's
# own shell folders, so the same script works for a different account on a
# different machine. The installed product lives inside this checkout at
# <repo>/LeoAIStudio (git-ignored). Override any of them explicitly, or set
# LEO_APP_ROOT.
param(
  [string]$AppRoot = $(if ($env:LEO_APP_ROOT) { $env:LEO_APP_ROOT }
                       else { Join-Path (Split-Path -Parent $PSScriptRoot) 'LeoAIStudio' }),
  [string]$PackageRoot = (Join-Path (Split-Path -Parent $PSScriptRoot) 'dist\LeoAIStudio'),
  [string]$ShortcutPath = (Join-Path ([Environment]::GetFolderPath('Desktop')) 'Leo AI Studio.lnk')
)

$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSHOME 'Modules\Microsoft.PowerShell.Utility\Microsoft.PowerShell.Utility.psd1') -Force

function Resolve-FullPath {
  param([Parameter(Mandatory)][string]$Path)
  return [IO.Path]::GetFullPath($Path).TrimEnd('\')
}

function Assert-NoReparsePoints {
  param([Parameter(Mandatory)][string]$Path)
  $cursor = Resolve-FullPath $Path
  while ($cursor) {
    if (Test-Path -LiteralPath $cursor) {
      $item = Get-Item -LiteralPath $cursor -Force
      if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw "Deployment paths must not contain links or junctions: $cursor"
      }
    }
    $parent = Split-Path -Parent $cursor
    if ($parent -eq $cursor) { break }
    $cursor = $parent
  }
}

function Assert-SafeTree {
  param([Parameter(Mandatory)][string]$Path)
  Assert-NoReparsePoints -Path $Path
  if (-not (Test-Path -LiteralPath $Path -PathType Container)) { return }
  $pending = New-Object 'Collections.Generic.Stack[string]'
  $pending.Push((Resolve-FullPath $Path))
  while ($pending.Count -gt 0) {
    $directory = $pending.Pop()
    foreach ($item in Get-ChildItem -LiteralPath $directory -Force) {
      if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw "Deployment trees must not contain links or junctions: $($item.FullName)"
      }
      if ($item.PSIsContainer) { $pending.Push($item.FullName) }
    }
  }
}

# The original guard compared against one literal path, which made the script
# unusable anywhere else. Deploying over the wrong directory is still
# destructive, so the guard remains -- it now asks whether the target really is
# a Leo installation rather than whether it is one particular Desktop.
function Assert-LooksLikeAppRoot {
  param([Parameter(Mandatory)][string]$Path, [Parameter(Mandatory)][string]$Label)
  $full = Resolve-FullPath $Path
  if (-not (Test-Path -LiteralPath $full -PathType Container)) {
    throw "$Label does not exist: $full"
  }
  foreach ($marker in @('theme', 'bridge')) {
    if (-not (Test-Path -LiteralPath (Join-Path $full $marker) -PathType Container)) {
      throw "$Label does not look like a Leo AI Studio installation (missing '$marker'): $full"
    }
  }
}

function Assert-LooksLikePackage {
  param([Parameter(Mandatory)][string]$Path, [Parameter(Mandatory)][string]$Label)
  $full = Resolve-FullPath $Path
  if (-not (Test-Path -LiteralPath (Join-Path $full 'LeoAIStudio.exe') -PathType Leaf)) {
    throw "$Label does not contain LeoAIStudio.exe: $full"
  }
  if (-not (Test-Path -LiteralPath (Join-Path $full '_launcher') -PathType Container)) {
    throw "$Label does not contain _launcher: $full"
  }
}

function Assert-ChildPath {
  param(
    [Parameter(Mandatory)][string]$Path,
    [Parameter(Mandatory)][string]$Parent
  )
  $full = Resolve-FullPath $Path
  $root = Resolve-FullPath $Parent
  if (-not $full.StartsWith($root + '\', [StringComparison]::OrdinalIgnoreCase)) {
    throw "Deployment path escapes the application root: $full"
  }
  Assert-NoReparsePoints -Path $full
  return $full
}

Assert-LooksLikeAppRoot -Path $AppRoot -Label 'Application root'
Assert-LooksLikePackage -Path $PackageRoot -Label 'Package root'

$AppRoot = Resolve-FullPath $AppRoot
$PackageRoot = Resolve-FullPath $PackageRoot
Assert-NoReparsePoints -Path $AppRoot
Assert-NoReparsePoints -Path $PackageRoot
if ($AppRoot -eq $PackageRoot -or
    $AppRoot.StartsWith($PackageRoot + '\', [StringComparison]::OrdinalIgnoreCase) -or
    $PackageRoot.StartsWith($AppRoot + '\', [StringComparison]::OrdinalIgnoreCase)) {
  throw 'Application and package roots must be separate directories.'
}
if (-not (Test-Path -LiteralPath $AppRoot -PathType Container)) { throw 'Application root is missing.' }
if (-not (Test-Path -LiteralPath $PackageRoot -PathType Container)) { throw 'Package root is missing.' }

$sourceExe = Join-Path $PackageRoot 'LeoAIStudio.exe'
$sourceLauncher = Join-Path $PackageRoot '_launcher'
$sourceTheme = Join-Path $PackageRoot 'theme'
$iconPath = Join-Path $AppRoot 'theme\logos\leo-lion.ico'

# The theme payload, declared once. It used to be five hand-kept copies of the
# same list, which is how theme\backgrounds -- a directory the shell reads on
# every injection -- could be added to a package and silently not deployed.
#
# themes.json is in the list because the shipped default theme now lives in it:
# a release that changes the default but does not deploy that file installs a
# stylesheet for a theme nobody is switched to.
$themeFiles = @('shell.html', 'themes.json', 'workbench.html', 'workbench.css', 'workbench.js', 'research-panel.js')
$runtimeFiles = @('bridge\leo_local_relay.py', 'bridge\leo_model_selection.py', 'bridge\leo_identity.py', 'bridge\leo_runtime_compat.py', 'bridge\leo_example_persistence.py', 'bridge\leo_runtime_features.py', 'bridge\leo_reasoning.py', 'bridge\leo_turn_binding.py', 'bridge\leo_turn_binding_runtime.py', 'bridge\leo_thought_runtime.py')
$runtimeFiles += 'build-receipt.json'
# Directories copied whole. 'logos' is required; 'backgrounds' exists only in
# packages whose theme ships artwork, so it is deployed when present rather
# than demanded.
# 'intro' holds the opening animation the start page plays on launch (2026-09-26).
$themeDirsRequired = @('logos', 'intro')
$themeDirsOptional = @('backgrounds')
# Payload an older release installed that no release ships any more. Deployment
# moves each one into this deployment's rollback directory instead of deleting it,
# so restoring that directory brings the previous release back exactly. The
# upstream-page injection layer was removed on 2026-09-26 (owner's approval).
# The web fonts and their license texts were retired the same day, also approved.
$retiredRelatives = @('theme\leo-inject.js', 'theme\leo.css', 'theme\i18n', 'theme\fonts', 'LICENSES\fonts')

foreach ($required in @($sourceExe, $sourceLauncher)) {
  if (-not (Test-Path -LiteralPath $required)) { throw "Deployment input is missing: $required" }
}
foreach ($relative in $runtimeFiles) {
  if (-not (Test-Path -LiteralPath (Join-Path $PackageRoot $relative) -PathType Leaf)) {
    throw "Deployment runtime input is missing: $relative"
  }
}
foreach ($name in $themeFiles) {
  $required = Join-Path $sourceTheme $name
  if (-not (Test-Path -LiteralPath $required -PathType Leaf)) { throw "Deployment input is missing: $required" }
}
foreach ($name in $themeDirsRequired) {
  $required = Join-Path $sourceTheme $name
  if (-not (Test-Path -LiteralPath $required -PathType Container)) { throw "Deployment input is missing: $required" }
}
$themeDirs = @($themeDirsRequired) + @($themeDirsOptional | Where-Object {
  Test-Path -LiteralPath (Join-Path $sourceTheme $_) -PathType Container
})
$releaseRelatives = @('LeoAIStudio.exe', '_launcher') + $runtimeFiles +
  (($themeFiles + $themeDirs) | ForEach-Object { Join-Path 'theme' $_ })
foreach ($relative in $releaseRelatives) {
  $source = Assert-ChildPath -Path (Join-Path $PackageRoot $relative) -Parent $PackageRoot
  $target = Assert-ChildPath -Path (Join-Path $AppRoot $relative) -Parent $AppRoot
  Assert-SafeTree -Path $source
  Assert-SafeTree -Path $target
}

# Every path this deployment is accountable for, relative to the package root.
# Both hash gates below walk this one list, so a file that is copied is always
# a file that is verified.
$verifiedRelatives = @('LeoAIStudio.exe') + $runtimeFiles + ($themeFiles | ForEach-Object { Join-Path 'theme' $_ })
foreach ($file in Get-ChildItem -LiteralPath $sourceLauncher -Recurse -File -Force) {
  $relative = $file.FullName.Substring($sourceLauncher.Length).TrimStart('\', '/')
  $verifiedRelatives += (Join-Path '_launcher' $relative)
}
foreach ($dir in $themeDirs) {
  $root = Join-Path $sourceTheme $dir
  foreach ($file in Get-ChildItem -LiteralPath $root -Recurse -File) {
    $relative = $file.FullName.Substring($root.Length).TrimStart('\', '/')
    $verifiedRelatives += (Join-Path 'theme' (Join-Path $dir $relative))
  }
}

$running = Get-CimInstance Win32_Process -Filter "Name='LeoAIStudio.exe'" -ErrorAction SilentlyContinue |
  Where-Object { $_.ExecutablePath -and (Resolve-FullPath $_.ExecutablePath) -eq (Join-Path $AppRoot 'LeoAIStudio.exe') }
if ($running) {
  throw 'Leo AI Studio is still running. Close it yourself, then retry deployment.'
}

$deploymentId = (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [Guid]::NewGuid().ToString('N').Substring(0, 8)
$staging = Assert-ChildPath -Path (Join-Path $AppRoot ".leo-deploy-$deploymentId") -Parent $AppRoot
$rollback = Assert-ChildPath -Path (Join-Path $AppRoot ".leo-rollback-$deploymentId") -Parent $AppRoot
$stagingTheme = Join-Path $staging 'theme'
$rollbackTheme = Join-Path $rollback 'theme'
[void](New-Item -ItemType Directory -Path $stagingTheme -Force)
[void](New-Item -ItemType Directory -Path $rollbackTheme -Force)

Copy-Item -LiteralPath $sourceExe -Destination (Join-Path $staging 'LeoAIStudio.exe') -Force
Copy-Item -LiteralPath $sourceLauncher -Destination (Join-Path $staging '_launcher') -Recurse -Force
foreach ($relative in $runtimeFiles) {
  $copy = Join-Path $staging $relative
  [void](New-Item -ItemType Directory -Path (Split-Path -Parent $copy) -Force)
  Copy-Item -LiteralPath (Join-Path $PackageRoot $relative) -Destination $copy
}
foreach ($name in $themeFiles) {
  Copy-Item -LiteralPath (Join-Path $sourceTheme $name) -Destination (Join-Path $stagingTheme $name) -Force
}
foreach ($dir in $themeDirs) {
  Copy-Item -LiteralPath (Join-Path $sourceTheme $dir) -Destination $stagingTheme -Recurse -Force
}

if ((Get-ChildItem -LiteralPath (Join-Path $staging '_launcher') -Recurse -File).Count -lt 250) {
  throw 'Staged _launcher is incomplete.'
}
foreach ($relative in $verifiedRelatives) {
  $source = Join-Path $PackageRoot $relative
  $copy = Join-Path $staging $relative
  if ((Get-FileHash -Algorithm SHA256 -LiteralPath $source).Hash -ne (Get-FileHash -Algorithm SHA256 -LiteralPath $copy).Hash) {
    throw "Staged deployment hash mismatch: $relative"
  }
}

$deployed = $false
$backedUp = New-Object 'Collections.Generic.List[object]'
$installedTargets = New-Object 'Collections.Generic.List[object]'
$rollbackErrors = New-Object 'Collections.Generic.List[string]'
$deploymentFailure = $null
try {
  foreach ($relative in $releaseRelatives) {
    $current = Assert-ChildPath -Path (Join-Path $AppRoot $relative) -Parent $AppRoot
    $saved = Assert-ChildPath -Path (Join-Path $rollback $relative) -Parent $rollback
    $staged = Assert-ChildPath -Path (Join-Path $staging $relative) -Parent $staging
    $operation = [pscustomobject]@{ Relative=$relative; Current=$current; Saved=$saved; Staged=$staged }
    [void](New-Item -ItemType Directory -Path (Split-Path -Parent $saved) -Force)
    # A new portable installation does not yet have e.g. bridge/.
    # Current was already resolved and checked to stay inside AppRoot.
    [void](New-Item -ItemType Directory -Path (Split-Path -Parent $current) -Force)
    if (Test-Path -LiteralPath $current) {
      Assert-SafeTree -Path $current
      Move-Item -LiteralPath $current -Destination $saved
      $backedUp.Add($operation)
    }
    Move-Item -LiteralPath $staged -Destination $current
    $installedTargets.Add($operation)
  }
  foreach ($relative in $retiredRelatives) {
    $current = Assert-ChildPath -Path (Join-Path $AppRoot $relative) -Parent $AppRoot
    if (-not (Test-Path -LiteralPath $current)) { continue }
    $saved = Assert-ChildPath -Path (Join-Path $rollback $relative) -Parent $rollback
    Assert-SafeTree -Path $current
    [void](New-Item -ItemType Directory -Path (Split-Path -Parent $saved) -Force)
    Move-Item -LiteralPath $current -Destination $saved
    # Recorded as backed up only, so a failed deployment moves it straight back.
    $backedUp.Add([pscustomobject]@{ Relative=$relative; Current=$current; Saved=$saved; Staged=$null })
  }

  foreach ($relative in $verifiedRelatives) {
    $source = Join-Path $PackageRoot $relative
    $installed = Join-Path $AppRoot $relative
    if ((Get-FileHash -Algorithm SHA256 -LiteralPath $source).Hash -ne (Get-FileHash -Algorithm SHA256 -LiteralPath $installed).Hash) {
      throw "Installed deployment hash mismatch: $relative"
    }
  }
  $deployed = $true
}
catch {
  $deploymentFailure = $_
  # Only reclaim payloads this invocation actually installed. Unvisited
  # targets may still contain the sole copy of the user's previous release.
  for ($index = $installedTargets.Count - 1; $index -ge 0; $index--) {
    $operation = $installedTargets[$index]
    try {
      [void](Assert-ChildPath -Path $operation.Current -Parent $AppRoot)
      [void](Assert-ChildPath -Path $operation.Staged -Parent $staging)
      Assert-SafeTree -Path $operation.Current
      Move-Item -LiteralPath $operation.Current -Destination $operation.Staged
    } catch {
      $rollbackErrors.Add("Could not reclaim installed payload: $($operation.Relative)")
    }
  }
  for ($index = $backedUp.Count - 1; $index -ge 0; $index--) {
    $operation = $backedUp[$index]
    try {
      [void](Assert-ChildPath -Path $operation.Saved -Parent $rollback)
      [void](Assert-ChildPath -Path $operation.Current -Parent $AppRoot)
      if (Test-Path -LiteralPath $operation.Current) { throw 'Restore destination is occupied; retained backup.' }
      Assert-SafeTree -Path $operation.Saved
      Move-Item -LiteralPath $operation.Saved -Destination $operation.Current
    } catch {
      $rollbackErrors.Add("Could not restore saved payload: $($operation.Relative)")
    }
  }
}
finally {
  if ($deployed -and (Test-Path -LiteralPath $staging)) {
    [void](Assert-ChildPath -Path $staging -Parent $AppRoot)
    Assert-SafeTree -Path $staging
    Remove-Item -LiteralPath $staging -Recurse -Force
  }
}

if (-not $deployed) {
  if ($rollbackErrors.Count -gt 0) {
    throw ("Deployment failed; rollback is incomplete. Preserved evidence at $staging and $rollback. " + ($rollbackErrors -join '; '))
  }
  throw "Deployment failed; previous targets were restored and staged evidence was retained at $staging. $($deploymentFailure.Exception.Message)"
}

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($ShortcutPath)
$shortcut.TargetPath = Join-Path $AppRoot 'LeoAIStudio.exe'
$shortcut.WorkingDirectory = $AppRoot
$shortcut.IconLocation = "$iconPath,0"
$shortcut.WindowStyle = 1
$shortcut.Save()

$manifest = [ordered]@{
  deployed_at = (Get-Date).ToString('o')
  rollback = $rollback
  exe_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $AppRoot 'LeoAIStudio.exe')).Hash
  launcher_files = (Get-ChildItem -LiteralPath (Join-Path $AppRoot '_launcher') -Recurse -File).Count
  shortcut_icon = "$iconPath,0"
}
$manifest | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $rollback 'deployment.json') -Encoding UTF8
$manifest | ConvertTo-Json

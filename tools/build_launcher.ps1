param(
  # The installed product lives inside this checkout at <repo>/LeoAIStudio
  # (git-ignored). Override with -AppRoot or LEO_APP_ROOT.
  [string]$AppRoot = $(if ($env:LEO_APP_ROOT) { $env:LEO_APP_ROOT }
                       else { Join-Path (Split-Path -Parent $PSScriptRoot) 'LeoAIStudio' }),
  [string]$BuildRoot = (Split-Path -Parent $PSScriptRoot),
  [string]$OutputRoot = '',
  # Hermetic is the default now that it is demonstrated to build and run.
  # -Legacy restores the old path that recovers inputs from a previous release;
  # it exists only as an escape hatch and should not be needed.
  [switch]$Legacy
)

$ErrorActionPreference = 'Stop'
# Python-launched Windows PowerShell can inherit PowerShell 7's PSModulePath.
# Bind hash/JSON utilities to this host instead of auto-loading another edition.
Import-Module (Join-Path $PSHOME 'Modules\Microsoft.PowerShell.Utility\Microsoft.PowerShell.Utility.psd1') -Force
if (-not $OutputRoot) { $OutputRoot = $BuildRoot }
$OutputRoot = [IO.Path]::GetFullPath($OutputRoot)
[void](New-Item -ItemType Directory -Path $OutputRoot -Force)

# -Hermetic builds only from requirements.lock and the project .venv. It performs
# none of the baseline recovery below: no ABI comparison against the old
# _launcher, no PYZ extraction from the previous LeoAIStudio.exe, no --paths into
# _launcher, and no Copy-MissingTree backfill from the old onedir.
#
# Hermetic is the default; -Legacy is an explicit recovery escape hatch.
# All theme inputs come from the checkout.
$Hermetic = -not $Legacy
if ($env:LEO_LEGACY_BUILD -eq '1') { $Hermetic = $false }
if ($Hermetic) {
  Write-Output 'HERMETIC BUILD: locked environment and source-controlled theme assets'
} else {
  Write-Output 'LEGACY BUILD: recovering inputs from the previous release (not reproducible)'
}
$pyiTools = Join-Path $BuildRoot '.venv\Lib\site-packages'
$pythonExe = Join-Path $BuildRoot '.venv\Scripts\python.exe'
$entry = Join-Path $BuildRoot 'launcher\leo_shell_entry.py'
$stage = Join-Path $BuildRoot 'stage'
$stagedShell = Join-Path $stage 'shell.html'
$stagedThemes = Join-Path $stage 'themes.json'
$stagedBackgrounds = Join-Path $stage 'backgrounds'
$researchSource = Join-Path $stage 'research-panel.js'
$stagedLogos = Join-Path $stage 'logos'
# The opening animation (owner-supplied, generated with Seedance 2.5; see leo_shell/intro.py).
$stagedIntro = Join-Path $stage 'intro'
$icon = Join-Path $stagedLogos 'leo-lion.ico'
$launcherDeps = Join-Path $AppRoot '_launcher'
$baselineExe = Join-Path $AppRoot 'LeoAIStudio.exe'
# PyInstaller hooks for pywebview. These ship inside the pywebview package, so
# in hermetic mode they come from the declared dependency set like everything
# else. They used to be taken from the previous release's _launcher, which was a
# sixth coupling to an old build and was never guarded by the hermetic switch --
# and it was self-invalidating: a hermetic build's own output does not contain
# webview\__pyinstaller, so deploying one made the *next* build impossible.
# -Legacy keeps the old source for the escape hatch.
$legacyWebviewHooks = Join-Path $launcherDeps 'webview\__pyinstaller'
if ($Hermetic) {
  $webviewHooks = (& $pythonExe -c 'import os, webview; print(os.path.join(os.path.dirname(webview.__file__), ''__pyinstaller''))').Trim()
  if ($LASTEXITCODE -ne 0 -or -not $webviewHooks) {
    throw 'Unable to locate pywebview''s PyInstaller hooks in the build environment.'
  }
} else {
  $webviewHooks = $legacyWebviewHooks
}
$packageContract = Join-Path $BuildRoot 'tools\package_contract.py'
$dependencyCache = Join-Path ([IO.Path]::GetTempPath()) ('leo-launcher-deps-' + [guid]::NewGuid().ToString('N'))
$previousPythonPath = $env:PYTHONPATH
$hadDontWriteBytecode = Test-Path Env:PYTHONDONTWRITEBYTECODE
$previousDontWriteBytecode = $env:PYTHONDONTWRITEBYTECODE
$env:PYTHONDONTWRITEBYTECODE = '1'

function Invoke-PythonChecked {
  param([Parameter(Mandatory)][string[]]$Arguments)
  # Builds run on the isolated project .venv (PyInstaller and the pinned
  # cryptography live there); never fall back to the system Python.
  #
  # The preference is relaxed only across the native call. Windows PowerShell
  # 5.1 -- the default host on Windows -- wraps every stderr line from a native
  # executable in an ErrorRecord, and under 'Stop' that terminates the build on
  # PyInstaller's ordinary WARNING output before the exit code is ever read.
  # PowerShell 7 does not, which is why this only ever failed on 5.1. The exit
  # code below is the real gate and is unchanged; nothing here suppresses a
  # genuine failure.
  $previousPreference = $ErrorActionPreference
  $ErrorActionPreference = 'Continue'
  try {
    & $pythonExe @Arguments
  } finally {
    $ErrorActionPreference = $previousPreference
  }
  if ($LASTEXITCODE -ne 0) {
    throw "Python failed with exit code $LASTEXITCODE."
  }
}

function Assert-SafeBaselineTree {
  param([Parameter(Mandatory)][string]$Root)
  $unsafe = Get-ChildItem -LiteralPath $Root -Force -Recurse | Where-Object {
    $relative = $_.FullName.Substring($Root.Length).TrimStart('\', '/')
    $relative -match '(?i)(^|[\\/])user([\\/]|$)|(^|[\\/])\.env($|[.\\/])|\.dpapi$|(^|[\\/])(?:credentials?|secrets?)(?:[.\\/]|$)|\.(?:key|pem|p12|pfx)$'
  }
  if ($unsafe) {
    $names = ($unsafe | ForEach-Object { $_.FullName.Substring($Root.Length).TrimStart('\', '/') }) -join ', '
    throw "Dependency baseline contains forbidden user/credential material: $names"
  }
}

function Copy-MissingTree {
  param(
    [Parameter(Mandatory)][string]$Source,
    [Parameter(Mandatory)][string]$Destination,
    [switch]$Overwrite
  )
  foreach ($sourceFile in Get-ChildItem -LiteralPath $Source -File -Recurse) {
    $relative = $sourceFile.FullName.Substring($Source.Length).TrimStart('\', '/')
    if ($relative -match '(?i)(^|[\\/])__pycache__([\\/]|$)|\.pyc$') {
      continue
    }
    $destinationFile = Join-Path $Destination $relative
    if ($Overwrite -or -not (Test-Path -LiteralPath $destinationFile)) {
      $destinationDirectory = Split-Path -Parent $destinationFile
      [void](New-Item -ItemType Directory -Path $destinationDirectory -Force)
      Copy-Item -LiteralPath $sourceFile.FullName -Destination $destinationFile -Force
    }
  }
}

# Inputs every build needs, whichever mode it runs in.
$requiredInputs = @(
  $pyiTools,
  $pythonExe,
  $entry,
  $stage,
  $stagedShell,
  $stagedThemes,
  $stagedBackgrounds,
  $stagedIntro,
  $researchSource,
  (Join-Path $stage 'workbench.html'),
  (Join-Path $stage 'workbench.css'),
  (Join-Path $stage 'workbench.js'),
  $icon,
  $webviewHooks,
  $packageContract,
  (Join-Path $BuildRoot 'leo_shell\app.py')
  (Join-Path $BuildRoot 'bridge\leo_local_relay.py')
  (Join-Path $BuildRoot 'bridge\leo_model_selection.py')
  (Join-Path $BuildRoot 'bridge\leo_identity.py')
  (Join-Path $BuildRoot 'bridge\leo_runtime_compat.py')
  (Join-Path $BuildRoot 'bridge\leo_example_persistence.py')
  (Join-Path $BuildRoot 'bridge\leo_runtime_features.py')
  (Join-Path $BuildRoot 'bridge\leo_reasoning.py')
  (Join-Path $BuildRoot 'bridge\leo_turn_binding.py')
  (Join-Path $BuildRoot 'bridge\leo_turn_binding_runtime.py')
  (Join-Path $BuildRoot 'bridge\leo_thought_runtime.py')
)

# The previous release's onedir and EXE. A hermetic build reads neither -- every
# use of them below is behind `if (-not $Hermetic)` -- so requiring them here was
# the last thing making a build impossible on a machine that has never installed
# Leo AI Studio. That is historical F1 in CHANGELOG.md, and a
# precondition that fails before PyInstaller starts is not a hermetic build.
if (-not $Hermetic) {
  $requiredInputs += $launcherDeps
  $requiredInputs += $baselineExe
}

foreach ($required in $requiredInputs) {
  if (-not (Test-Path -LiteralPath $required)) {
    throw "Required build input is missing: $required"
  }
}

if (-not $Hermetic) {
  Assert-SafeBaselineTree -Root $launcherDeps
}
Assert-SafeBaselineTree -Root $stage
if ($Hermetic) {
  Invoke-PythonChecked -Arguments @((Join-Path $BuildRoot 'tools\build_receipt.py'), 'begin', '--repo', $BuildRoot, '--dist', (Join-Path $OutputRoot 'dist\LeoAIStudio'), '--snapshot', (Join-Path $OutputRoot 'build-inputs.json'))
}

# The upstream-page injection bundle (leo-inject.js, leo.css and their layers)
# was removed on 2026-09-26 with the owner's approval: every document the shell
# shows is Leo's own, so there is nothing to bundle.

# Keep this probe free of double quotes: Windows PowerShell 5.1 strips them
# when passing arguments to native commands, which would corrupt the code.
$pythonInfoJson = & $pythonExe -c 'import json, platform, sys; print(json.dumps(dict(major=sys.version_info.major, minor=sys.version_info.minor, bits=platform.architecture()[0])))'
if ($LASTEXITCODE -ne 0) {
  throw 'Unable to inspect the build Python runtime.'
}
$pythonInfo = $pythonInfoJson | ConvertFrom-Json
if ($pythonInfo.major -ne 3 -or $pythonInfo.minor -ne 12 -or $pythonInfo.bits -ne '64bit') {
  throw "The dependency baseline requires 64-bit Python 3.12; found $($pythonInfo.major).$($pythonInfo.minor) $($pythonInfo.bits)."
}

if (-not $Hermetic) {
  $baselinePython = Join-Path $launcherDeps 'python312.dll'
  # The .venv interpreter is a venv launcher; the ABI-relevant DLL lives in its
  # base prefix (the mamba CPython 3.12 installation), so resolve it there
  # rather than next to whatever 'python' happens to be on PATH.
  $runtimePython = (& $pythonExe -c 'import os, sys; print(os.path.join(sys.base_prefix, ''python312.dll''))').Trim()
  foreach ($pythonDll in @($baselinePython, $runtimePython)) {
    if (-not (Test-Path -LiteralPath $pythonDll)) {
      throw "Python ABI validation input is missing: $pythonDll"
    }
  }
  if ((Get-FileHash -Algorithm SHA256 -LiteralPath $baselinePython).Hash -ne (Get-FileHash -Algorithm SHA256 -LiteralPath $runtimePython).Hash) {
    throw 'The old _launcher Python DLL does not match the Python used for this build.'
  }

  $baselineCryptography = Get-ChildItem -LiteralPath $launcherDeps -Directory -Filter 'cryptography-*.dist-info' | Select-Object -First 1
  if (-not $baselineCryptography -or $baselineCryptography.Name -notmatch '^cryptography-(?<version>.+)\.dist-info$') {
    throw 'The old _launcher does not identify its cryptography version.'
  }
  $baselineCryptographyVersion = $Matches.version
  $installedCryptography = & $pythonExe -c 'import cryptography; print(cryptography.__version__)'
  if ($LASTEXITCODE -ne 0 -or $installedCryptography.Trim() -ne $baselineCryptographyVersion) {
    throw "cryptography version mismatch: baseline=$baselineCryptographyVersion, build=$($installedCryptography.Trim())."
  }
}
else {
  # Hermetic: the ABI contract is the declared Python, not the old build.
  $lockFile = Join-Path $BuildRoot 'requirements.lock'
  if (-not (Test-Path -LiteralPath $lockFile)) { throw 'requirements.lock is missing.' }
  $runtimePython = (& $pythonExe -c 'import os, sys; print(os.path.join(sys.base_prefix, ''python312.dll''))').Trim()
  if (-not (Test-Path -LiteralPath $runtimePython)) { throw "Python DLL missing: $runtimePython" }
  Write-Output "HERMETIC: python312.dll from $runtimePython"

  # "Built from requirements.lock" was, until now, a claim about intent: the
  # build used whatever .venv happened to contain. This checks it. Every pin
  # must be installed at its pinned version and nothing undeclared may be there,
  # or the build stops -- a package that is in the environment but not in the
  # lock is a dependency nobody reviewed and that no wheelhouse would carry.
  $wheelhouseTool = Join-Path $BuildRoot 'tools\build_wheelhouse.py'
  Write-Output 'HERMETIC: auditing the build environment against requirements.lock'
  & $pythonExe $wheelhouseTool audit-env --python $pythonExe
  if ($LASTEXITCODE -ne 0) {
    throw 'Build environment does not match requirements.lock (see above). Reprovision with tools/provision_venv.ps1.'
  }

  # The wheelhouse is what makes provisioning offline. It is not required to run
  # PyInstaller, so its absence is reported rather than fatal -- but the build log
  # must say which of the two situations produced this binary.
  $wheelhouseManifest = Join-Path $BuildRoot 'manifests\wheelhouse.json'
  if (Test-Path -LiteralPath $wheelhouseManifest) {
    & $pythonExe $wheelhouseTool verify | Out-Null
    if ($LASTEXITCODE -eq 0) {
      Write-Output 'HERMETIC: wheelhouse verified; dependencies are installable with --no-index'
    } else {
      Write-Output 'HERMETIC: WARNING wheelhouse manifest present but does NOT verify; offline install is not available'
    }
  } else {
    Write-Output 'HERMETIC: no wheelhouse on this machine; dependencies would resolve from an index. Run tools/build_wheelhouse.py build'
  }
}

try {
  [void](New-Item -ItemType Directory -Path $dependencyCache -Force)
  $env:LEO_BASELINE_EXE = $baselineExe
  $env:LEO_DEPENDENCY_CACHE = $dependencyCache
  # PyInstaller itself comes from the project .venv; $pyiTools is only kept as
  # the offline archive reader for the package contract test below.
  $env:PYTHONPATH = $dependencyCache

  # These pure modules live in the old launcher's PYZ rather than as loose
  # files in _launcher. Recover only dependency modules into an ephemeral cache.
  # Keeping cffi paired with the baseline _cffi_backend also prevents an ABI
  # mismatch with an unrelated cffi installation in the build environment.
  $extractDependencies = @'
import importlib.util
import marshal
import os
from pathlib import Path

from PyInstaller.archive.readers import CArchiveReader

source = CArchiveReader(os.environ["LEO_BASELINE_EXE"])
pyz = source.open_embedded_archive("PYZ.pyz")
output = Path(os.environ["LEO_DEPENDENCY_CACHE"])
allowed = ("bottle", "cffi", "clr", "proxy_tools", "pythonnet", "clr_loader")

for name in sorted(pyz.toc):
    if not any(name == prefix or name.startswith(prefix + ".") for prefix in allowed):
        continue
    code = pyz.extract(name)
    if code is None:
        continue
    parts = name.split(".")
    is_package = pyz.toc[name][0] == 1
    target = output.joinpath(*parts, "__init__.pyc") if is_package else output.joinpath(*parts).with_suffix(".pyc")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(importlib.util.MAGIC_NUMBER + b"\0" * 12 + marshal.dumps(code))

required = (
    output / "bottle.pyc",
    output / "cffi" / "__init__.pyc",
    output / "clr.pyc",
    output / "proxy_tools" / "__init__.pyc",
    output / "pythonnet" / "__init__.pyc",
    output / "clr_loader" / "__init__.pyc",
)
missing = [str(path) for path in required if not path.is_file()]
if missing:
    raise SystemExit("Missing recovered dependency modules: " + ", ".join(missing))
'@
  # Run the extractor as a real file: Windows PowerShell 5.1 mangles embedded
  # double quotes when forwarding -c payloads to native commands.
  $extractScript = Join-Path $dependencyCache 'extract_dependencies.py'
  Set-Content -LiteralPath $extractScript -Value $extractDependencies -Encoding ASCII
  if (-not $Hermetic) {
    Invoke-PythonChecked -Arguments @($extractScript)
  }
  else {
    Write-Output 'HERMETIC: skipping PYZ recovery; dependencies come from requirements.lock'
  }

  if ($Hermetic) {
    $env:PYTHONPATH = $BuildRoot
    # PyInstaller resolves a binary's dependencies through PATH on Windows. This
    # Python is a conda distribution, which keeps ffi-8.dll, sqlite3.dll,
    # libbz2.dll, liblzma.dll and libexpat.dll under <base_prefix>\Libraryin
    # rather than beside python.exe, so PyInstaller misses them and the frozen
    # app dies on `import _ctypes` before it reaches main().
    #
    # The legacy build papered over this by copying the DLLs out of the previous
    # release's _launcher. They are part of the declared Python toolchain, so
    # hermetic mode takes them from there instead.
    $libraryBin = (& $pythonExe -c 'import os, sys; print(os.path.join(sys.base_prefix, ''Library'', ''bin''))').Trim()
    if (Test-Path -LiteralPath $libraryBin) {
      Write-Output "HERMETIC: adding $libraryBin to PATH for dependency analysis"
      $env:PATH = $libraryBin + ';' + $env:PATH
    }
  }
  else {
    $env:PYTHONPATH = @($dependencyCache, $BuildRoot, $launcherDeps) -join ';'
  }
  $versionInfo = Join-Path $OutputRoot 'version-info.txt'
  Invoke-PythonChecked -Arguments @((Join-Path $BuildRoot 'tools\release_identity.py'), '--output', $versionInfo)
  $pyInstallerArguments = @(
    '-m', 'PyInstaller',
    '--noconfirm',
    '--clean',
    '--windowed',
    '--onedir',
    '--contents-directory', '_launcher',
    '--name', 'LeoAIStudio',
    '--version-file', $versionInfo,
    '--icon', $icon,
    '--paths', $dependencyCache,
    '--paths', $BuildRoot,
    '--paths', $(if ($Hermetic) { $BuildRoot } else { $launcherDeps }),
    '--additional-hooks-dir', $webviewHooks,
    '--hidden-import', 'webview',
    '--hidden-import', 'webview.platforms.edgechromium',
    '--hidden-import', 'webview.platforms.winforms',
    '--hidden-import', 'bottle',
    '--hidden-import', 'leo_shell.research',
    '--hidden-import', 'leo_shell.research_draft',
    '--add-data', ((Join-Path $BuildRoot 'pinn\governance\schemas') + ';pinn/governance/schemas'),
    '--exclude-module', 'torch',
    '--exclude-module', 'numpy',
    '--exclude-module', 'matplotlib',
    '--hidden-import', 'cffi',
    '--hidden-import', 'clr',
    '--hidden-import', 'proxy_tools',
    '--hidden-import', 'pythonnet',
    '--collect-submodules', 'webview',
    '--collect-submodules', 'cffi',
    '--collect-submodules', 'clr_loader',
    '--collect-submodules', 'pythonnet',
    '--collect-submodules', 'leo_shell',
    '--collect-all', 'cryptography',
    '--distpath', (Join-Path $OutputRoot 'dist'),
    '--workpath', (Join-Path $OutputRoot 'pyi-work'),
    '--specpath', (Join-Path $OutputRoot 'pyi-spec'),
    $entry
  )
  Invoke-PythonChecked -Arguments $pyInstallerArguments

  $packageRoot = Join-Path $OutputRoot 'dist\LeoAIStudio'
  $distLauncher = Join-Path $packageRoot '_launcher'
  $exe = Join-Path $packageRoot 'LeoAIStudio.exe'
  $newBaseLibrary = Join-Path $distLauncher 'base_library.zip'
  foreach ($buildOutput in @($exe, $distLauncher, $newBaseLibrary)) {
    if (-not (Test-Path -LiteralPath $buildOutput)) {
      throw "PyInstaller did not produce required output: $buildOutput"
    }
  }

  # Fill gaps from the validated old onedir baseline. Existing files, including
  # the new EXE's base_library.zip and bootloader DLLs, always win.
  $newBaseLibraryHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $newBaseLibrary).Hash
  if (-not $Hermetic) {
    Copy-MissingTree -Source $launcherDeps -Destination $distLauncher
  }
  else {
    Write-Output 'HERMETIC: no backfill from the previous _launcher'
  }
  if ((Get-FileHash -Algorithm SHA256 -LiteralPath $newBaseLibrary).Hash -ne $newBaseLibraryHash) {
    throw 'Dependency merge unexpectedly replaced the new base_library.zip.'
  }

  # Theme assets are approved application inputs and are copied authoritatively.
  #
  # No installation is consulted: the declared files/directories below are
  # the entire theme payload. (The web fonts and their licenses were retired on
  # 2026-09-26 with the owner's approval; no Leo document used them.)
  #
  # themes.json and backgrounds/ joined that set because the runtime reads both
  # on every render: themes.json decides which theme a new user opens on, and
  # backgrounds/ is inlined into the stylesheet. Taking either from the local
  # installation would leave a product asset outside version control.
  $packageTheme = Join-Path $packageRoot 'theme'
  [void](New-Item -ItemType Directory -Path $packageTheme -Force)
  $themeOverlays = @{
    'shell.html' = $stagedShell
    'themes.json' = $stagedThemes
    'workbench.html' = (Join-Path $stage 'workbench.html')
    'workbench.css' = (Join-Path $stage 'workbench.css')
    'workbench.js' = (Join-Path $stage 'workbench.js')
    'research-panel.js' = $researchSource
  }
  # Directory overlays: every file under the staged directory replaces the
  # package's copy, and the package keeps nothing the repository does not have.
  $themeDirOverlays = @{ 'backgrounds' = $stagedBackgrounds; 'logos' = $stagedLogos; 'intro' = $stagedIntro }
  foreach ($relative in $themeDirOverlays.Keys) {
    $source = $themeDirOverlays[$relative]
    if (-not (Test-Path -LiteralPath $source -PathType Container)) {
      throw "Staged theme directory is missing: $source"
    }
    $destination = Join-Path $packageTheme $relative
    if (Test-Path -LiteralPath $destination) {
      $resolvedDestination = (Resolve-Path -LiteralPath $destination).ProviderPath
      $resolvedPackageTheme = (Resolve-Path -LiteralPath $packageTheme).ProviderPath.TrimEnd('\') + '\'
      if (-not $resolvedDestination.StartsWith($resolvedPackageTheme, [StringComparison]::OrdinalIgnoreCase) -or
          ((Get-Item -LiteralPath $destination).Attributes -band [IO.FileAttributes]::ReparsePoint)) {
        throw "Unsafe package overlay destination: $resolvedDestination"
      }
      Remove-Item -LiteralPath $resolvedDestination -Recurse -Force
    }
    Copy-Item -LiteralPath $source -Destination $packageTheme -Recurse -Force
    foreach ($file in Get-ChildItem -LiteralPath $source -Recurse -File) {
      $suffix = $file.FullName.Substring($source.Length).TrimStart('\', '/')
      $copy = Join-Path $destination $suffix
      if ((Get-FileHash -Algorithm SHA256 -LiteralPath $file.FullName).Hash -ne (Get-FileHash -Algorithm SHA256 -LiteralPath $copy).Hash) {
        throw "Staged theme overlay verification failed: $relative\$suffix"
      }
    }
  }
  foreach ($relative in $themeOverlays.Keys) {
    $source = $themeOverlays[$relative]
    $destination = Join-Path $packageTheme $relative
    Copy-Item -LiteralPath $source -Destination $destination -Force
    if ((Get-FileHash -Algorithm SHA256 -LiteralPath $source).Hash -ne (Get-FileHash -Algorithm SHA256 -LiteralPath $destination).Hash) {
      throw "Staged theme overlay verification failed: $relative"
    }
  }

  # Only this bridge resource belongs to this feature; retain the installed
  # upstream bridge independently instead of copying/replacing its directory.
  $packageBridge = Join-Path $packageRoot 'bridge'
  [void](New-Item -ItemType Directory -Path $packageBridge -Force)
  foreach ($resource in @('leo_local_relay.py', 'leo_model_selection.py', 'leo_identity.py', 'leo_runtime_compat.py', 'leo_example_persistence.py', 'leo_runtime_features.py', 'leo_reasoning.py', 'leo_turn_binding.py', 'leo_turn_binding_runtime.py', 'leo_thought_runtime.py')) {
    $resourceSource = Join-Path (Join-Path $BuildRoot 'bridge') $resource
    $resourceTarget = Join-Path $packageBridge $resource
    Copy-Item -LiteralPath $resourceSource -Destination $resourceTarget -Force
    if ((Get-FileHash -LiteralPath $resourceSource).Hash -ne (Get-FileHash -LiteralPath $resourceTarget).Hash) {
      throw "Local model runtime package hash mismatch: $resource"
    }
  }

  Invoke-PythonChecked -Arguments @(
    $packageContract,
    '--dist', $packageRoot,
    '--pyinstaller-tools', $pyiTools,
    '--forbidden-build-root', $BuildRoot
  )

  Get-Item -LiteralPath $exe | Select-Object FullName, Length, LastWriteTime
  if ($Hermetic) {
    Invoke-PythonChecked -Arguments @((Join-Path $BuildRoot 'tools\build_receipt.py'), 'finish', '--repo', $BuildRoot, '--dist', $packageRoot, '--snapshot', (Join-Path $OutputRoot 'build-inputs.json'))
  }
  Write-Host "Package contract passed for $packageRoot"
}
finally {
  $env:PYTHONPATH = $previousPythonPath
  if ($hadDontWriteBytecode) { $env:PYTHONDONTWRITEBYTECODE = $previousDontWriteBytecode }
  else { Remove-Item Env:PYTHONDONTWRITEBYTECODE -ErrorAction SilentlyContinue }
  Remove-Item Env:LEO_BASELINE_EXE -ErrorAction SilentlyContinue
  Remove-Item Env:LEO_DEPENDENCY_CACHE -ErrorAction SilentlyContinue
  if (Test-Path -LiteralPath $dependencyCache) {
    $resolvedCache = (Resolve-Path -LiteralPath $dependencyCache).ProviderPath
    $resolvedTemp = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\') + '\'
    if (-not $resolvedCache.StartsWith($resolvedTemp, [StringComparison]::OrdinalIgnoreCase) -or
        (Split-Path -Leaf $resolvedCache) -notlike 'leo-launcher-deps-*') {
      throw "Unsafe dependency-cache cleanup path: $resolvedCache"
    }
    Remove-Item -LiteralPath $dependencyCache -Recurse -Force
  }
}

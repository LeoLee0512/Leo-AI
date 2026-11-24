# Create the build environment from the declared inputs, offline where possible.
#
# The build runs on .venv. Until now nothing said where .venv came from, which
# meant "built from requirements.lock" described an intention rather than a fact.
# This script is the other end of that: it creates .venv and installs exactly the
# locked set, from the local wheelhouse with --no-index when one is present.
#
#   tools\provision_venv.ps1                 # offline from wheelhouse/, if it verifies
#   tools\provision_venv.ps1 -AllowIndex     # permit resolving from an index
#   tools\provision_venv.ps1 -Recreate       # delete and rebuild .venv first
#
# Without -AllowIndex and without a verified wheelhouse this fails rather than
# quietly reaching for PyPI. A build that silently changes where its dependencies
# came from is the problem this exists to prevent.

param(
  [string]$BuildRoot = (Split-Path -Parent $PSScriptRoot),
  [string]$BasePython = 'python',
  [switch]$AllowIndex,
  [switch]$Recreate
)

$ErrorActionPreference = 'Stop'

$venv = Join-Path $BuildRoot '.venv'
$venvPython = Join-Path $venv 'Scripts\python.exe'
$lockFile = Join-Path $BuildRoot 'requirements.lock'
$wheelhouse = Join-Path $BuildRoot 'wheelhouse'
$wheelhouseTool = Join-Path $BuildRoot 'tools\build_wheelhouse.py'

if (-not (Test-Path -LiteralPath $lockFile)) { throw "requirements.lock is missing at $lockFile." }

if ($Recreate -and (Test-Path -LiteralPath $venv)) {
  Write-Output "Removing $venv"
  Remove-Item -LiteralPath $venv -Recurse -Force
}

if (-not (Test-Path -LiteralPath $venvPython)) {
  Write-Output "Creating $venv from $BasePython"
  & $BasePython -m venv $venv
  if ($LASTEXITCODE -ne 0) { throw "Could not create a virtual environment with $BasePython." }
}

# Decide the install mode before installing anything, and say which one is in
# use. A log that does not record whether the wheels came from disk or from a
# network index cannot support a reproducibility claim afterwards.
$offline = $false
if (Test-Path -LiteralPath $wheelhouse) {
  & $venvPython $wheelhouseTool verify | Out-Null
  if ($LASTEXITCODE -eq 0) {
    $offline = $true
  } else {
    Write-Output 'Wheelhouse present but does not verify:'
    & $venvPython $wheelhouseTool verify
  }
}

if ($offline) {
  Write-Output "OFFLINE: installing from $wheelhouse with --no-index"
  & $venvPython -m pip install --no-index --find-links $wheelhouse --requirement $lockFile
  if ($LASTEXITCODE -ne 0) { throw 'Offline install failed.' }
}
elseif ($AllowIndex) {
  Write-Output 'INDEX: no verified wheelhouse; resolving from the configured index because -AllowIndex was passed'
  & $venvPython -m pip install --requirement $lockFile
  if ($LASTEXITCODE -ne 0) { throw 'Install from index failed.' }
}
else {
  throw @'
No verified wheelhouse, and -AllowIndex was not passed.

Either build one:
    python tools\build_wheelhouse.py build
or accept an index explicitly:
    tools\provision_venv.ps1 -AllowIndex

Falling back to an index without being asked would make the build silently
depend on what that index serves today, which is the failure this refuses.
'@
}

Write-Output 'Auditing the result against requirements.lock'
& $venvPython $wheelhouseTool audit-env --python $venvPython
if ($LASTEXITCODE -ne 0) { throw 'The provisioned environment does not match requirements.lock.' }

Write-Output ''
Write-Output "PROVISIONED: $venvPython"
Write-Output ("  source: " + $(if ($offline) { "wheelhouse (offline)" } else { "index" }))
Write-Output '  NOTE: this provisions a build environment. Whether a clean machine can'
Write-Output '        build the product from a fresh clone is F1/F2 in'
Write-Output '        the historical manual checklist in CHANGELOG.md and stays NOT TESTED.'

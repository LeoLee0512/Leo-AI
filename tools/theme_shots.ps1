# Capture theme-preview screenshots with headless Edge.
#
# Edge is deliberate rather than convenient: the app renders in WebView2, which
# is the same Chromium build, so what this captures is what the shell paints.
#
# A throwaway --user-data-dir keeps the operator's real Edge profile untouched.
#
#   pwsh tools/theme_shots.ps1 -BaseUrl http://127.0.0.1:8801/preview-light `
#        -OutDir shots/light -Tag light
param(
  [Parameter(Mandatory)][string]$BaseUrl,
  [Parameter(Mandatory)][string]$OutDir,
  [string]$Tag = 'light',
  [string[]]$Scenes = @('home', 'chat', 'workspace-empty', 'settings'),
  [string]$Edge = 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
)

$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $Edge)) { throw "Edge not found: $Edge" }
[void](New-Item -ItemType Directory -Path $OutDir -Force)

$profileDir = Join-Path ([IO.Path]::GetTempPath()) ("leo-shots-" + [Guid]::NewGuid().ToString('N'))
[void](New-Item -ItemType Directory -Path $profileDir -Force)

# 1440x900 is the desktop acceptance width; 390x844 is the phone one.
$viewports = @(
  @{ name = 'desktop'; size = '1440,900' },
  @{ name = 'mobile';  size = '390,844'  }
)

try {
  foreach ($vp in $viewports) {
    foreach ($scene in $Scenes) {
      $out = Join-Path $OutDir "$Tag-$($vp.name)-$scene.png"
      $url = "$BaseUrl/$scene.html"
      # Routed through cmd so Edge's stderr chatter ("N bytes written to file")
      # stays out of PowerShell 5.1's pipeline, where it would surface as a
      # NativeCommandError on an otherwise successful capture.
      $args = @(
        '--headless=new', '--disable-gpu', '--hide-scrollbars',
        '--force-device-scale-factor=1', "--user-data-dir=`"$profileDir`"",
        '--no-first-run', '--no-default-browser-check',
        '--virtual-time-budget=6000', "--window-size=$($vp.size)",
        "--screenshot=`"$out`"", "`"$url`""
      ) -join ' '
      cmd /c "`"$Edge`" $args >nul 2>nul"
      if (Test-Path -LiteralPath $out) {
        $kb = [math]::Round((Get-Item -LiteralPath $out).Length / 1KB, 1)
        Write-Output "$out  ($kb KB)"
      } else {
        Write-Output "FAILED: $out"
      }
    }
  }
} finally {
  Remove-Item -LiteralPath $profileDir -Recurse -Force -ErrorAction SilentlyContinue
}

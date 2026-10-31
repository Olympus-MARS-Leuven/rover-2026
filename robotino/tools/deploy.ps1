<#
Deploy the committed robotino/ folder to the Pi as a new release.

Run in PowerShell on the PC, from anywhere inside the repository:
    .\robotino\tools\deploy.ps1
Stop the robot app on the Pi first (Ctrl+C). Nothing on the Pi is deleted:
each release gets its own folder in ~/robotino-releases and ~/robotino is
switched to point at it. Calibration in ~/.config/robotino is not touched.
#>
param(
    [string]$PiHost = "robotino@robotino-pi.local",
    [switch]$AllowUncommitted
)
$ErrorActionPreference = "Stop"

$repo = (git rev-parse --show-toplevel).Trim()
Set-Location $repo
$changes = git status --porcelain -- robotino
if ($changes -and -not $AllowUncommitted) {
    Write-Host "robotino/ has uncommitted changes; only committed code is deployed:" -ForegroundColor Yellow
    $changes
    Write-Host "Commit first, or run again with -AllowUncommitted to deploy the last commit anyway."
    exit 1
}
$commit = (git rev-parse --short=10 HEAD).Trim()
$branch = (git rev-parse --abbrev-ref HEAD).Trim()
$tar = Join-Path $env:TEMP "robotino-$commit.tar"

# core.autocrlf=false keeps Linux line endings (LF), whatever this PC uses.
git -c core.autocrlf=false archive --format=tar -o $tar "HEAD:robotino"
if ($LASTEXITCODE -ne 0) { throw "git archive failed" }
Write-Host "Release $commit from $branch ($([math]::Round((Get-Item $tar).Length / 1KB)) KB)"

Write-Host "1/3 Checking the Pi (password prompt possible)"
ssh $PiHost "mkdir -p ~/robotino-releases && if pgrep -f '[r]obotino_app.py' >/dev/null; then echo 'The robot app is running on the Pi: stop it with Ctrl+C first.'; exit 3; fi"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "2/3 Copying"
scp $tar "${PiHost}:robotino-releases/$commit.tar"
if ($LASTEXITCODE -ne 0) { throw "Copy to the Pi failed" }

Write-Host "3/3 Installing"
ssh $PiHost "cd ~/robotino-releases && mkdir -p $commit && tar -xf $commit.tar -C $commit && rm $commit.tar && sh $commit/tools/install_release.sh $commit '$branch'"
if ($LASTEXITCODE -ne 0) { throw "Install on the Pi failed" }
Remove-Item $tar

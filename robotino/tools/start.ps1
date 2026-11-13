<#
Start Robotino from the PC in one step: opens the SSH tunnel, starts the robot
app on the Pi and opens the control page in the browser.

Double-click "Start Robotino.cmd" in the robotino folder, or run:
    .\robotino\tools\start.ps1               real tracks and servos
    .\robotino\tools\start.ps1 -Simulation   nothing moves
    .\robotino\tools\start.ps1 -Shutdown     switch the Pi off safely
#>
param(
    [string]$PiHost = "robotino@robotino-pi.local",
    [switch]$Simulation,
    [switch]$Shutdown
)

if ($Shutdown) {
    Write-Host "Shutting down the robot's Pi. Type the Pi password if asked (twice is normal)."
    ssh -t $PiHost "sudo shutdown -h now"
    Write-Host ""
    Write-Host "Wait about 20 seconds until the green light on the Pi stops flashing, then switch the robot off."
    Read-Host "Press Enter to close this window"
    exit
}

$flags = if ($Simulation) { "" } else { "--hardware --servos" }
$url = "http://127.0.0.1:8765"

# A hidden helper opens the browser as soon as the page answers. It waits up to
# 3 minutes, which leaves time to type the password.
$opener = @"
`$deadline = (Get-Date).AddMinutes(3)
while ((Get-Date) -lt `$deadline) {
    try { Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 '$url/' | Out-Null; Start-Process '$url'; break }
    catch { Start-Sleep -Seconds 1 }
}
"@
$encoded = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($opener))
Start-Process powershell -WindowStyle Hidden -ArgumentList "-NoProfile", "-EncodedCommand", $encoded

Write-Host "Connecting to the robot. Type the Pi password when asked (nothing shows while typing)."
Write-Host "KEEP THIS WINDOW OPEN while you drive. Ctrl+C here stops the robot app." -ForegroundColor Yellow
Write-Host ""
ssh -t -L 8765:127.0.0.1:8765 -o ExitOnForwardFailure=yes $PiHost "cd ~/robotino && python3 robotino_app.py $flags"
$code = $LASTEXITCODE
Write-Host ""
if ($code -eq 0 -or $code -eq 130) {
    Write-Host "The robot app has stopped."
} else {
    Write-Host "Could not start the robot (code $code). Common causes:" -ForegroundColor Red
    Write-Host " - 'Could not resolve hostname': the robot is off, still starting (wait 1 minute), or this PC is on another Wi-Fi."
    Write-Host " - 'Address already in use': another Robotino window or the simulation is already open. Close it and try again."
    Write-Host " - 'Another Robotino hardware process': the app is already running on the Pi in another window."
    Write-Host " - 'Permission denied': wrong password."
}
Read-Host "Press Enter to close this window"

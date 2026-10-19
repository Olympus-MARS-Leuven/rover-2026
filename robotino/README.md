# Robotino: keyboard driving and arm control

Target: original green Adeept Motor Shield V2, Raspberry Pi 3 Model B,
Raspberry Pi OS Bookworm Lite 64-bit, Python 3.11. Login used for this robot:
`robotino@robotino-pi.local`. The browser controls the tracks and all five arm/camera
joints. Read [ARM_CONTROL.md](ARM_CONTROL.md) for joint sliders, keyboard jogging,
movement speed, initial software limits and servo-only testing. Camera streaming
and PS4 input are not implemented yet.

This is a bench-test version, not yet the finished public-event application.
The hardware-free tests cannot establish physical track direction, stopping
distance, available torque, power stability, or performance on this Pi.

## Where everything happens

| Place | Purpose |
| --- | --- |
| PC: local VS Code window | Edit the source code and use Codex |
| PC: GitHub Desktop | Review changes, commit, and publish your feature branch |
| GitHub | Shared history of the project; it does not run the robot |
| Pi: SSH terminal | Run Python, which controls the shield |
| PC: browser | Read keyboard events and send commands through an SSH tunnel |

Editing on the PC does not automatically update the Pi. Repeat the copy command
after edits, with the running robot app stopped. A commit saves a local snapshot;
a push/publish uploads commits to GitHub. Follow the repository's feature-branch
and pull-request rules; do not merge directly into `main`.

## Files

| File | Responsibility |
| --- | --- |
| `robotino_app.py` | Local HTTP server, hardware selection, watchdog, shutdown |
| `drive.py` | Motor pins, selected motor duty, expiring control sessions |
| `arm.py` | Five joint limits, smooth ramps, holding/release and servo drivers |
| `hardware.py` | Shared Pi checks and exclusive hardware ownership |
| `servo_test.py` | Finite one-channel servo ramp based on the original web app; simulation by default |
| `servo_probe.py` | Explicit one-channel servo identification; simulation by default |
| `web/index.html` | English control page |
| `web/controls.js` | Keyboard handling, speed slider and command heartbeats |
| `tests/` | Hardware-free checks for timeout, stale commands, wiring and HTTP |
| `move.py` | Existing vendor example; not imported or run by this application |

## 1. Prepare the Pi

In the Pi terminal:

```bash
uname -m
getconf LONG_BIT
sudo apt update
sudo apt install -y python3-rpi.gpio python3-smbus
python3 -c "import RPi.GPIO as GPIO; print(GPIO.VERSION)"
id -nG
```

Expected architecture: `aarch64` and `64`. Your groups should include `gpio`
and, for servo operation, `i2c`. If missing, run
`sudo usermod -aG gpio,i2c robotino` and log out/in.
Run the app as the normal `robotino` user, without `sudo`.

In `sudo raspi-config`, keep I2C enabled, serial login **disabled**, serial port
hardware **disabled**, and 1-Wire **disabled**. GPIO14/15 are motor direction
pins and GPIO4 is a motor enable, so serial and 1-Wire must not use them.

Set the two motor enables LOW early during future boots. Open:

```bash
sudo nano /boot/firmware/config.txt
```

At the end, add these lines if this exact setting is not already present:

```ini
[all]
gpio=4,17=op,dl
```

Save with Ctrl+O, Enter, then exit with Ctrl+X. Reboot with `sudo reboot`.
This boot setting complements the software stop; it is not a physical emergency
stop and cannot cover the interval before firmware configures the pins.

## 2. Copy from PC to Pi

Stop any running Robotino app with Ctrl+C before replacing its files.
From a **local Windows PowerShell terminal** in the repository root:

```powershell
scp -r .\robotino robotino@robotino-pi.local:~/
```

This initial transfer copies this small project folder into `/home/robotino/robotino`.
Do not put backups, credentials, or a virtual environment inside this folder.
Driving uses standard Python modules plus the OS-provided RPi.GPIO package.
The browser arm controls and servo tools also need the OS package `python3-smbus`.
Neither requires pip or a virtual environment. Start with
`python3 robotino_app.py --servos` for real joints and disabled tracks, then use
`python3 robotino_app.py --hardware --servos` for combined real operation after
joint checks. Without `--servos`, the arm remains simulated.

## 3. Test without moving anything

In a **local Windows PowerShell terminal**, open SSH with a port forward:

```powershell
ssh -L 8765:127.0.0.1:8765 -o ExitOnForwardFailure=yes robotino@robotino-pi.local
```

Inside that resulting **Pi terminal**:

```bash
cd ~/robotino
python3 -m unittest discover -s tests -v
python3 robotino_app.py
```

On the PC, open <http://127.0.0.1:8765>. Keep the SSH terminal open.
The page must say **SIMULATION — motors disabled**. This mode never imports
RPi.GPIO or accesses motor pins. Click **Connect controls**, then hold Shift and
one direction. The page should show signed motor percentages, while the robot
stays still. STOP/Esc/Space disconnect; reconnect manually afterward.

The **Speed / motor duty** slider starts at **50%** whenever the page is loaded.
It covers **0–100%** in 5-point steps and applies on the next command, including
while driving. At 0%, both tracks stop. It changes the power sent to both motors;
it does not measure speed or automatically balance a weaker track.

Focusing the slider clears held driving keys. When it has focus, arrow keys
adjust its value. Click elsewhere on the page before driving with arrows again.
ZQSD still works with Shift. Changing the slider by itself never starts motion.

To check the browser logic on a **PC with Node.js installed**, from the
repository root:

```powershell
node --test .\robotino\tests\test_keyboard.cjs
```

## 4. First physical test

Support the rover so both tracks can spin clear of the surface. Keep its arm
clear and the power switch accessible. Use charged batteries. Stop simulation
with Ctrl+C, then in the same Pi terminal:

```bash
python3 robotino_app.py --hardware
```

Refresh the browser with Ctrl+F5. It must now say **MOTORS ENABLED** and show
the speed slider at **50%**. Connect controls.

1. Briefly hold Shift+Up (or Shift+Z). Both tracks should drive forward.
2. Release the direction key. Both tracks must stop being powered.
3. Test backward, left and right briefly. Left/right pivot on the spot.
4. While holding a direction, release Shift: power must stop.
5. Test STOP, then reconnect and test switching to another browser tab.
6. With tracks still raised, test loss of the SSH link. The Pi watchdog must
   stop motor power after about **2 seconds**. Reconnecting the network must not
   restart motion by itself.

Both tracks' motor polarity is set for your latest report that **all four
directions** were reversed. Check forward, backward, left and right again:
left/right pivot direction also depends on the track polarities. Stop the app
before copying an update, then restart it so Python loads the new mapping.

The previous fixed **25%** limit has been replaced by the slider. Start at **50%**
with the tracks raised, then increase in 5- or 10-point steps if needed. Full duty
is available at 100%; use the lowest setting that moves both tracks reliably.
If a track buzzes or stays stuck, release immediately. Check for a tight track,
obstruction, poor connection or weak batteries before repeatedly increasing duty.
Higher duty cannot establish that the underlying problem is only a low setting.
If direction or stopping is wrong, switch off and report which track did what.
Test on a clear, level floor only after the raised-track checks pass; save ramps
and blocks until both tracks move reliably under the robot's weight.

If timeouts continue, note the exact red message, whether the page was idle or
driving, and any errors in the Pi terminal. The new timing allows short delays;
it does not fix a dropped Wi-Fi or SSH connection.

Before disconnecting power normally: Ctrl+C to stop the app, then
`sudo shutdown -h now`, wait for shutdown, and switch off.

## How stopping works, and its limits

- A fresh command is sent about every 80 ms plus network/processing time.
- The browser allows **1.5 seconds** for each request (previously 0.3 seconds).
  On failure it requests a stop and requires a manual reconnect.
- The Pi expires a session after **2 seconds** without a fresh accepted command
  (previously 0.4 seconds). This tolerates more network and Pi scheduling delays,
  but a lost link or lost release message can leave motors powered for up to
  about **2 seconds after the last accepted command**.
  The watchdog checks every 20 ms. Linux scheduling adds jitter; this is not a
  guaranteed real-time deadline. Measure the real stopping response on the Pi.
- Commands carry a one-use server challenge. Old or duplicated movement
  requests cannot renew an expired session. Only one page controls a session.
- The browser holds at most one drive request in flight and clears its keys on
  blur, tab hiding, STOP and connection faults. It never reconnects automatically.
- Releasing a direction or Shift is sent at the next heartbeat. A lost release
  message is covered by the Pi timeout. Conflicting direction keys request stop.
- Both PWM enables drop to zero before changing direction. Reversals include
  a 50 ms coast interval. Normal exit leaves enable pins driven LOW.
- With real servos enabled, STOP, disconnect, timeout and normal shutdown also
  remove servo signals. The arm can sag; support it during tests. The arm panel's
  **Hold position** pauses joint travel while keeping servo support.
- This is a **software stop**, not a safety-rated emergency stop. A Pi freeze,
  forced process termination, GPIO failure or power fault can defeat software
  protections. Keep physical power cutoff available. The tracks may coast.

## Hardware references

BCM GPIO numbers from the user's working backup dated 2026-10-18. Forward
polarity is corrected using the subsequent physical-test feedback:

| Track | Enable/PWM | IN1 | IN2 | Forward IN1/IN2 |
| --- | --- | --- | --- | --- |
| Left (B) | 17 | 27 | 18 | HIGH / LOW |
| Right (A) | 4 | 14 | 15 | LOW / HIGH |

PWM is 1 kHz. The old source's startup pulses at 100% duty are not reproduced.
The servo controller responds at I2C `0x40`; `0x70` is normally its all-call
address. The app uses real servos only with `--servos`; all outputs start OFF and
each joint starts on first use in the page. Servo preparation disables all-call,
so `0x70` may disappear from later scans. Only `0x40` is used for servo commands.
The separate terminal tools require their own `--hardware` flag for movement.
Joint channels and initial limits come from the user's original backup; see
[ARM_CONTROL.md](ARM_CONTROL.md) for provenance and the tighter gripper limit.

Sources: [vendor repository](https://github.com/adeept/Adeept_RaspTank),
[RPi.GPIO basics](https://sourceforge.net/p/raspberry-gpio-python/wiki/BasicUsage/),
[RPi.GPIO PWM](https://sourceforge.net/p/raspberry-gpio-python/wiki/PWM/),
[PCA9685 datasheet](https://www.nxp.com/docs/en/data-sheet/PCA9685.pdf),
[Raspberry Pi config.txt GPIO settings](https://www.raspberrypi.com/documentation/computers/config_txt.html#gpio).

Next milestones: physical checks and any required tightening of the joint limits,
PS4 input, event network, optional camera streaming, then supervised usability and
endurance tests.

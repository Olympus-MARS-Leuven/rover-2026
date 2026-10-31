# Robotino: browser and PS4 control, video and guided setup

Target: original green Adeept Motor Shield V2, Raspberry Pi 3 Model B,
Raspberry Pi OS Bookworm Lite 64-bit, Python 3.11. Login used for this robot:
`robotino@robotino-pi.local`.

One local web page (reached through an SSH tunnel) controls everything:

- **Tracks** with the keyboard (Shift + arrows/ZQSD) or the **PS4 controller**
  (left stick, proportional).
- **Arm and camera tilt** with sliders, Shift + keys, or the controller in ARM
  mode (△ switches DRIVE ↔ ARM). See [ARM_CONTROL.md](ARM_CONTROL.md).
- **Video** from the ribbon camera, started on demand.
- **Pi health**: under-voltage (weak batteries), throttling, temperature, CPU.
- **Setup & tests**: a guided tab that moves one thing at a time, asks what you
  saw, saves the measured calibration on the Pi and produces a report.

First session with real hardware: follow [FIRST_RUN.md](FIRST_RUN.md).

This is still a bench-test version. The hardware-free tests cannot establish
physical directions, stopping distance, torque, power stability or Pi
performance; the Setup & tests tab exists to measure those.

## Where everything happens

| Place | Purpose |
| --- | --- |
| PC: local VS Code window | Edit the source code |
| PC: GitHub Desktop or Git | Review changes, commit, and publish your feature branch |
| GitHub | Shared history of the project; it does not run the robot |
| PC: PowerShell | `tools/deploy.ps1` installs the committed code on the Pi |
| Pi: SSH terminal | Run Python, which controls the shield |
| PC: browser | Page with keyboard, PS4 controller, video and setup tests |

Editing on the PC does not update the Pi, and a commit or push does not either.
Deploy after committing. Follow the repository's feature-branch and pull-request
rules; do not merge directly into `main`.

## Files

| File | Responsibility |
| --- | --- |
| `robotino_app.py` | Local HTTP server, hardware selection, watchdog, status, video endpoint |
| `drive.py` | Motor pins, duty, analog (stick) driving, expiring control sessions |
| `arm.py` | Joint limits, ramps, freeze/release, start-position estimates, servo drivers |
| `calibration.py` | Measured settings in `~/.config/robotino/calibration.json` |
| `camera.py` | On-demand MJPEG video from `rpicam-vid` (test card on a PC) |
| `health.py` | Under-voltage, throttling, temperature and CPU readings and logs |
| `hardware.py` | Shared Pi checks and exclusive hardware ownership |
| `servo_test.py`, `servo_probe.py` | Finite one-channel servo tools from the arm investigation |
| `web/index.html`, `web/controls.js` | Page, keyboard, controller, video, health |
| `web/gamepad.js` | PS4 button and stick mapping (pure functions) |
| `web/setup.js`, `web/setup_logic.js` | Setup & tests tab and its calculations/report |
| `tools/deploy.ps1`, `tools/install_release.sh` | Release-based installation on the Pi |
| `tests/` | Hardware-free checks (Python and Node.js) |
| `move.py` | Vendor example; not imported or run by this application |

## 1. Prepare the Pi

In the Pi terminal:

```bash
uname -m
getconf LONG_BIT
sudo apt update
sudo apt install -y python3-rpi.gpio python3-smbus
python3 -c "import RPi.GPIO as GPIO; print(GPIO.VERSION)"
id -nG
rpicam-hello --list-cameras
```

Expected architecture: `aarch64` and `64` (confirmed on 25 October 2026).
Your groups should include `gpio`, `i2c` and `video`. If missing, run
`sudo usermod -aG gpio,i2c,video robotino` and log out/in.
Run the app as the normal `robotino` user, without `sudo`.
Video needs the camera tools, normally included in Raspberry Pi OS Lite; if
`rpicam-hello` is not found, install them with `sudo apt install -y rpicam-apps-lite`.

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

## 2. Deploy from PC to Pi

Stop any running Robotino app with Ctrl+C before deploying. Commit your changes,
then from a **local Windows PowerShell terminal** in the repository:

```powershell
powershell -ExecutionPolicy Bypass -File .\robotino\tools\deploy.ps1
```

The script packs the committed `robotino/` folder with `git archive` (Linux line
endings, `docs/` left out), copies it to `~/robotino-releases/<commit>` on the
Pi and points `~/robotino` at it. Nothing is deleted: the first deployment keeps
the old hand-copied folder as `~/robotino-before-releases`, and any previous
release can be restored with `ln -sfn ~/robotino-releases/<commit> ~/robotino`.
The page header and `~/robotino/VERSION` show which commit is running.

The old `scp -r .\robotino robotino@robotino-pi.local:~/` method also works but
does not remove deleted files and copies Windows line endings.

Measured calibration, remembered servo positions, test reports and health logs
are kept in `~/.config/robotino/`, outside the code, so deployments keep them.

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
one direction, or use the controller. The page shows signed motor percentages
while the robot stays still. STOP/Esc/Space/○ disconnect; reconnect manually
(or with Options on the controller).

The same simulation runs on the PC itself: `python robotino_app.py` in the
`robotino` folder, then the same address. To check the browser logic on a
**PC with Node.js installed**, from the `robotino` folder:

```powershell
node --test tests/test_keyboard.cjs tests/test_gamepad.cjs tests/test_setup_logic.cjs
```

The **Speed / motor duty** slider starts at **50%** whenever the page is loaded.
It is the maximum for both the keyboard and the stick, covers **0–100%** in
5-point steps (10 with the D-pad) and applies on the next command. At 0%, both
tracks stop. It changes the power sent to both motors; it does not measure
speed. Focusing the slider clears held driving keys; when it has focus, arrow
keys adjust its value.

## 4. Run modes

| Command (Pi) | Real hardware |
| --- | --- |
| `python3 robotino_app.py` | None; tracks and servos simulated |
| `python3 robotino_app.py --servos` | Servos; real track enables held LOW |
| `python3 robotino_app.py --hardware` | Tracks; servos simulated |
| `python3 robotino_app.py --hardware --servos` | Tracks and servos |

Add `--no-camera` to switch the video off. Video starts only when the page shows
it, in a separate `rpicam-vid` process, and stops 3 s after the last viewer.
Presets: low 424×240 at 10 fps, normal 640×480 at 15 fps, smooth 640×480 at 25 fps.

## 5. First physical tests

Use the **Setup & tests** tab ([FIRST_RUN.md](FIRST_RUN.md) explains each step).
It checks servo channels and directions, joint limits, rest positions, the arm
after STOP, track directions, minimum track power, driving straight, the
lost-link stop, stopping distance, the controller and video, and saves what it
measures. Track directions are never changed by calibration: the GPIO map and
polarity below were accepted after two physical corrections.

## PS4 controller

The controller is read by the browser (Gamepad API), so nothing is installed on
the Pi and its commands use the same session, challenge and timeout as the
keyboard. Plug it into the PC with the USB cable and press any button after the
page has loaded.

| Control | Action |
| --- | --- |
| △ | DRIVE ↔ ARM (1 / 2 vibrations in Chrome; Firefox cannot vibrate). ARM also enables the arm |
| Left stick (DRIVE) | Drive and turn, proportional; let go to stop |
| Left stick ↕ (ARM) | Lower arm |
| Right stick ↕ / ↔ (ARM) | Upper arm / wrist |
| R2 / L2 (ARM) | Close / open the gripper |
| D-pad ↑ / ↓ | Camera tilt (arm enabled) |
| D-pad ← / → | Lower / raise the maximum drive duty, or arm speed in ARM |
| Hold L1 or R1 | Precision: 40% of the movement |
| ○ / Options | STOP and disconnect / connect |
| □ / Share | Park the arm at its measured rest pose / release the servos |

No shoulder button has to be held: a stick springs back to its centre, which is
stop. The keyboard keeps its Shift deadman and has priority while it is used.
Unplugging the controller or leaving the window stops controller movement at
once; a Bluetooth dropout can take a few seconds to be noticed, so use the USB
cable at events.

## How stopping works, and its limits

- A fresh command is sent about every 80 ms plus network/processing time.
- The browser allows **1.5 seconds** for each request. On failure it requests
  a stop and requires a manual reconnect.
- The Pi expires a session after **2 seconds** without a fresh accepted command
  and logs how long it waited. A lost link or lost release message can leave
  motors powered for up to about **2 seconds after the last accepted command**.
  The watchdog checks every 20 ms; this is not a guaranteed real-time deadline.
  The Setup & tests tab measures it.
- Commands carry a one-use server challenge. Old or duplicated movement
  requests cannot renew an expired session. Only one page controls a session.
- The browser holds at most one drive request in flight and clears its keys on
  blur, tab hiding, STOP and connection faults. It never reconnects automatically.
- Both PWM enables drop to zero before changing direction. Reversals include
  a 50 ms coast interval. Normal exit leaves enable pins driven LOW.
- STOP, disconnect and timeout **freeze the arm**: it keeps holding for
  **10 seconds** (so a block is not dropped), then releases. Enabling the arm
  again within that time continues from where it is. **Release servos** (or
  Share) removes holding force at once; normal shutdown also releases.
- This is a **software stop**, not a safety-rated emergency stop. A Pi freeze,
  forced process termination, GPIO failure or power fault can defeat software
  protections. The servo controller keeps its last signals if the Pi crashes.
  Keep physical power cutoff available. The tracks may coast.

## Hardware references

BCM GPIO numbers from the user's working backup dated 2026-10-18. Forward
polarity is corrected using the subsequent physical-test feedback:

| Track | Enable/PWM | IN1 | IN2 | Forward IN1/IN2 |
| --- | --- | --- | --- | --- |
| Left (B) | 17 | 27 | 18 | HIGH / LOW |
| Right (A) | 4 | 14 | 15 | LOW / HIGH |

PWM is 1 kHz. The old source's startup pulses at 100% duty are not reproduced.
Measured track calibration only adds a minimum moving duty and a straight-line
trim; it never changes these directions.

The servo controller responds at I2C `0x40`; `0x70` is normally its all-call
address. The app uses real servos only with `--servos`; all outputs start OFF.
Joints whose position is known (measured rest pose, or remembered after the
last release) are powered one by one when the arm is enabled; the others start
on first use. Joint channels and initial limits come from the original backup
until the Setup & tests tab saves measured values; see
[ARM_CONTROL.md](ARM_CONTROL.md).

Sources: [vendor repository](https://github.com/adeept/Adeept_RaspTank),
[RPi.GPIO basics](https://sourceforge.net/p/raspberry-gpio-python/wiki/BasicUsage/),
[RPi.GPIO PWM](https://sourceforge.net/p/raspberry-gpio-python/wiki/PWM/),
[PCA9685 datasheet](https://www.nxp.com/docs/en/data-sheet/PCA9685.pdf),
[Raspberry Pi config.txt GPIO settings](https://www.raspberrypi.com/documentation/computers/config_txt.html#gpio),
[Raspberry Pi camera software](https://www.raspberrypi.com/documentation/computers/camera_software.html),
[`vcgencmd get_throttled`](https://www.raspberrypi.com/documentation/computers/os.html#get_throttled),
[Gamepad API standard mapping](https://w3c.github.io/gamepad/#remapping).

Next milestones: run the Setup & tests tab on the robot, event network and
startup routine, all-day power (the health log in `~/.config/robotino/logs/`
records under-voltage and temperature), then supervised usability tests.

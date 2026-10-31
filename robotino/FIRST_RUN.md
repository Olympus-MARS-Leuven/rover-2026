# First run after the battery fix

A checklist for the first session with the new software. It installs the code
on the Pi, starts it, and walks through the **Setup & tests** tab, which
moves one thing at a time and asks you what you saw. At the end you download
a report; send it so the results can be recorded in the repository.

Every command says where it runs: **PC** (PowerShell on your Windows PC) or
**Pi** (the SSH terminal on the robot).

## 0. Today, without the robot (optional, recommended)

You can learn the whole page now. In simulation nothing is sent to motors or
servos, and nothing is saved as calibration.

**PC**, in the repository folder:

```powershell
cd robotino
python -m unittest discover -s tests
node --test tests/test_keyboard.cjs tests/test_gamepad.cjs tests/test_setup_logic.cjs
python robotino_app.py
```

Open <http://127.0.0.1:8765> in Firefox or Chrome. The camera panel shows a
test card. Plug the PS4 controller into the PC with the USB cable and press any
button: the controller panel shows it. Open **Setup & tests** and try the
steps; each one is marked *practice*. Step 2 (PS4 controller) is a real test
even now. Stop the app with Ctrl+C.

## 1. Batteries and robot

- Charge the batteries fully.
- Put the robot on a stand so both tracks turn freely in the air.
- Clear the arm area. Keep the power switch within reach.

## 2. Install the new code on the Pi

Stop any running robot app on the Pi first (Ctrl+C in its terminal).

**PC**, from the repository folder:

```powershell
powershell -ExecutionPolicy Bypass -File .\robotino\tools\deploy.ps1
```

It may ask for the Pi password up to three times. What it does:

- packs exactly the **committed** code of your current branch, with Linux line
  endings (this fixes the mixed line endings found on 25 October);
- copies it to `~/robotino-releases/<commit>` on the Pi;
- points `~/robotino` at that folder. The first time, your old `~/robotino`
  folder is kept as `~/robotino-before-releases`. Nothing is deleted.

Calibration and reports live in `~/.config/robotino` on the Pi, so they
survive every update.

## 3. Check the Pi once

**PC**, open the SSH terminal with the tunnel:

```powershell
ssh -L 8765:127.0.0.1:8765 -o ExitOnForwardFailure=yes robotino@robotino-pi.local
```

**Pi**:

```bash
cd ~/robotino
cat VERSION
python3 -m unittest discover -s tests
rpicam-hello --list-cameras
```

- `VERSION` shows the commit you deployed.
- All tests should pass (107 at the time of writing).
- If `rpicam-hello` is missing: `sudo apt install -y rpicam-apps-lite`. If no
  camera is listed, power off and check the ribbon cable. Video is optional:
  the robot works without it.

## 4. Start with real hardware

**Pi**:

```bash
python3 robotino_app.py --hardware --servos
```

**PC**: open <http://127.0.0.1:8765> and press Ctrl+F5. Check the top bar:

- **MOTORS ENABLED** and **REAL SERVOS**;
- the version matches `VERSION`;
- the health box says **Supply OK**. If it says **UNDER-VOLTAGE**, the
  batteries are too weak for reliable tests: stop and charge or replace them.

## 5. Setup & tests

Click **Connect controls**, then the **Setup & tests** tab, and go through the
steps in order. Red **STOP** (or Esc, or ○ on the controller) stops
everything at any moment.

| Step | Robot position | What happens |
| --- | --- | --- |
| 1-2 | — | Checklist; controller buttons and vibration |
| 3 Servo channels & directions | On the stand, hand near the arm | Each servo moves 20 ticks and back; you say what moved and which way. Saving fixes the directions and, if needed, the channels |
| 4 Joint limits | On the stand, support the arm | You hold a button to move a joint slowly and mark both safe ends. It pauses at the old archived limit and asks before going further |
| 5 Arm rest positions | On the stand | Finds where the arm rests when unpowered, so later it can be powered without a jump. Then save |
| 6 Arm after STOP | On the stand | Checks that STOP freezes the arm, then releases it after 10 s |
| 7 Track directions | Tracks in the air | Each track runs forward for 1 s; you confirm the direction |
| 8 Minimum track power | In the air (then optionally the floor) | Power rises in steps; you press when the track starts turning |
| 9 Driving straight | Floor, 1.5 m free | Short drive; the trim is adjusted until it goes straight |
| 10 Lost-link stop | Tracks in the air | The page goes silent on purpose; the Pi must stop the motors by itself in about 2 s |
| 11 Stopping distance | Floor, optional | Measures how far it rolls after you let go |
| 12 Save track calibration | — | Saves minimum power and trim |
| 13 Controller on the robot | In the air first | Normal controller driving and ARM mode, as a checklist |
| 14 Video | — | Camera model, upright picture, delay, frame rate while driving |
| 15 Report | — | Download the report (.md) and send it |

Your answers are kept in this browser if the page reloads. You can repeat a
step at any time by clicking it on the left.

## 6. Driving at events

Use the **Drive** tab. Controller summary:

- **DRIVE**: left stick drives; let go to stop. D-pad ←/→ changes the
  maximum speed. Hold L1 or R1 for precise, slow movement.
- **△** switches to **ARM** (two vibrations in Chrome; Firefox cannot vibrate).
  Left stick ↕ lower arm, right stick ↕ upper arm, right stick ↔ wrist,
  R2/L2 close/open the gripper, D-pad ↑/↓ camera tilt.
- **○** is STOP. **Options** connects again. **□** parks the arm at its rest
  pose, **Share** releases the servos.

Use the USB cable at events: unplugging stops the robot at once, while a
Bluetooth dropout can take a few seconds to be noticed.

## 7. Shut down

**Pi**: Ctrl+C to stop the app, then `sudo shutdown -h now`. Wait about 20
seconds, then switch off the power.

## If something goes wrong

| Symptom | What to do |
| --- | --- |
| UNDER-VOLTAGE in the top bar | Charge or replace the batteries before testing further. Each episode is in the report and in `~/.config/robotino/logs/` |
| "Another Robotino hardware process is already running" | An old app is still running: `ps -ef \| grep '[r]obotino_app.py'`, then stop it |
| Controller not shown | Press any button on it after the page has loaded; try the other USB port |
| Camera: "Camera stopped" | Run `rpicam-hello --list-cameras` on the Pi and send the output |
| Want the previous code back | **Pi**: `ls ~/robotino-releases`, then `ln -sfn ~/robotino-releases/<commit> ~/robotino` |
| Track turned the wrong way in step 7 | Do not change wiring or code yourself; finish and send the report |

Optional, saves typing the password: create an SSH key once on the **PC** with
`ssh-keygen -t ed25519` (press Enter at each question), then
`type $env:USERPROFILE\.ssh\id_ed25519.pub | ssh robotino@robotino-pi.local "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"`.

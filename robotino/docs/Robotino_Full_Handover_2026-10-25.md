# Robotino — complete project handover

**Prepared: 25 October 2026.** This document is intended for the next AI and the Olympus MARS team. Read it before editing or deploying anything. It combines the project conversation, relevant local VS Code/Codex feedback, inspected Git revisions, the original software backup, supplied hardware PDFs, and software tests rerun for this handover.

## 1. Read this first

Robotino is the small **tracked Adeept RaspTank with the original green Adeept Motor Shield V2 and a Raspberry Pi 3 Model B**. It is a supervised public-event robot for driving around a small course and moving lightweight blocks with its arm.

**The project has progressed beyond initial keyboard control.** Corrected track control was reported working by the user. Finite camera-tilt and gripper tests were also reported working. An integrated five-joint browser controller now exists on `robotino/feature/arm-control`. That branch is **not merged into the inspected `main`**. Do not restart the project from an old keyboard-only patch.

The next AI should:

1. Read the revision table below and inspect the chosen branch before changing files.
2. Preserve the working track controls and the successful servo-test approach.
3. Ask for the user's current feedback; the last request before this handover was to continue making changes directly in VS Code.
4. Establish what is actually running on the Pi. The current Windows checkout is not proof of Pi deployment.
5. Continue with arm validation and the requested feedback, then PS4 input, event operation, and optional video.
6. Explain useful batches of steps to a beginner, label PC versus Pi commands, and make authorized code changes directly where access permits.

### Evidence labels used throughout

- **User observed:** reported physical behavior or terminal output; not independently measured by the AI.
- **Inspected:** found in source, Git metadata, backup files, PDFs, or relevant session records.
- **Software tested:** tests executed on the Windows computer with simulated/mocked hardware.
- **Proposed / unverified:** a plan, recommendation, or a point still requiring confirmation.

There was **no live SSH inspection or physical robot operation during preparation of this handover**. Passing desktop tests does not establish stopping distance, electrical reliability, mechanical limits, or five-hour endurance.

## 2. User goals and working preferences

The user is learning larger software projects and wants an AI collaborator that can implement code, explain it clearly, and teach the Git/VS Code/Pi workflow without repetitive elementary questions.

Requirements recorded directly in the conversation:

- Rewrite the original RaspTank software to make it simpler, more reliable, and lighter on the Pi 3.
- Use Raspberry Pi OS Lite, with development in local VS Code and source history in the existing Olympus MARS GitHub repository.
- Implement keyboard driving first, arm control next, then an original Sony PS4/DualShock 4 controller. A USB data cable is available.
- Add ribbon-camera video to the PC only if the Pi handles robot control reliably and video latency is acceptable. Video is optional.
- Use English for the interface. The PC keyboard is AZERTY; arrows and ZQSD are appropriate.
- Operate at schools and public events, with the team supervising users of all ages, including children.
- Typical course: around 2 × 2 m or larger, small ramps and tunnels, picking up small lightweight blocks and dropping them into boxes. Cardboard blocks around 3 × 3 cm or smaller are acceptable.
- Operating distance is only a few metres. Venues change, so dependable local networking matters more than internet access.
- Target event duration is approximately 12:00–17:00 with nearly continuous use.
- Keep costs low and reuse available equipment where practical.
- The user accepts a more involved initial setup if everyday operation becomes straightforward.
- A PC is not intrinsically required for eventual controller-only operation; it is useful for a video display.
- The user prefers several meaningful steps at a time, accurate instructions, and preservation of prior progress.

Do not treat this as the team's larger ERC rover. The repository also contains unrelated STM32 and other rover work. Four-wheel steering, STM32 F446RE, DRV8833 motor drivers, SG90 steering, and that rover's power architecture must not be substituted for Robotino's hardware.

Anti-collision features and deliberately introduced control latency appeared in broader remembered context, but were not established as implemented or confirmed requirements in the evidence used here. Reconfirm before expanding scope.

## 3. Repository, branches, and the current state

Repository: https://github.com/Olympus-MARS-Leuven/rover-2026

Original Windows checkout:

```text
C:\Users\adrie\Documents\GitHub\rover-2026
```

Project scope is its `robotino/` directory. The repository's root README describes feature branches and pull requests. Use that workflow rather than merging directly into `main`.

### Revisions inspected on 25 October

| Revision | Commit | Meaning |
|---|---|---|
| Current local `main` | `73fae8a85349892345fa67e29f67713b244c3ea3` | Contains the merged keyboard-control work. Its latest commit adds an unrelated STM32 Motor_test project. |
| `robotino/feature/keyboard-control` | `b303d8e8fc7cb0ec5a1c1f23dba05c635f7a922c` | Adjustable motor duty, corrected directions, longer timeouts. Commit dated 18 October, 23:31:58 local time. |
| Keyboard merge into main | `f0b9be6` | PR #5 merge in the inspected history. |
| `robotino/feature/arm-control` | `d5b0eb2cb8d4e059ed1b61d5110a6f30339ee465` | Finite servo tests plus integrated arm/camera-tilt controls. Commit dated 20 October, 00:37:39 local time; message “test of arm's joint”. |

The arm commit is **not an ancestor of the inspected main**. Local cached origin references matched the feature-branch commits. No fresh fetch from GitHub was performed for this handover; remote changes made elsewhere could therefore be missing.

The original checkout had a clean Git status when inspected. Ignored Python caches were present, including arm-related caches left behind on main. **A cached `.pyc` file does not establish that its source exists on the active branch.**

Direct Git access to the original checkout was restricted in the handover environment, so inspection used a separate local copy. The original repository was not modified. Git also reported a broken internal Codex checkpoint reference under `refs/codex/turn-diffs/…`; ordinary branch history and the source snapshots remained readable. This is not evidence of a Robotino runtime failure.

### Included source snapshots

The accompanying ZIP contains exact tracked-file exports of:

- `01_main/` — root README and Robotino files at main's commit above.
- `02_arm_control/` — root README and Robotino files at the arm branch commit above.
- `03_validation/` — complete Python and JavaScript test logs from this handover.
- `04_hardware_documents/` — supplied assembly tutorial and Motor Shield V2 schematic.
- A copy of this handover, a read-first note, and a SHA-256 manifest.

The snapshots contain neither Git history nor a connection to GitHub. To contribute changes, use the real repository and the appropriate branch. Do not replace the whole shared repository with a snapshot.

**Unknown:** the exact files and revision currently installed under `/home/robotino/robotino` on the Pi.

## 4. Hardware inventory and wiring

### Confirmed or source-supported hardware

| Item | Evidence and qualification |
|---|---|
| Raspberry Pi | User output: `Raspberry Pi 3 Model B Rev 1.2`. This model has 1 GB RAM and supports a 64-bit operating system. |
| Shield | User identifies Adeept Motor Shield V2; the supplied documentation and software correspond to the original green board. |
| Tracks | Original DC motors and stock mechanical assembly. No encoder feedback has been established. |
| Servos | Camera tilt, lower arm, upper arm, wrist rotation, and gripper in the current control mapping. |
| Camera | Raspberry Pi ribbon/CSI camera. Exact sensor and camera-board model remain unknown. |
| Power | Stock holder with two 18650 lithium-ion cells powering the Pi and shield. Actual cell health/capacity and current demand are unmeasured. |
| Original functionality | Before the reset, the user reported that tracks, arm, and camera all worked with the original software. |

The supplied schematic identifies **PCA9685** servo PWM control, an **L298P** dual motor bridge, and a **GS2678** step-down supply. Its motor supply is connected to the input-voltage rail, while a regulated 5 V rail serves other circuitry. This is a schematic interpretation, not a live voltage measurement or a complete input-rating approval.

### Motor GPIO mapping — BCM numbering

Current source in both snapshots:

```python
TRACKS = (
    (17, 27, 18, (1, 0)),  # left / motor B
    (4, 14, 15, (0, 1)),  # right / motor A
)
```

| Track | PWM enable BCM / physical pin | Direction 1 BCM / physical pin | Direction 2 BCM / physical pin | Forward levels |
|---|---|---|---|---|
| Left, motor B | 17 / 11 | 27 / 13 | 18 / 12 | HIGH, LOW |
| Right, motor A | 4 / 7 | 14 / 8 | 15 / 10 | LOW, HIGH |

Use BCM values in the program, not physical connector numbers. PWM is 1 kHz through RPi.GPIO. Direction reversal first drops power and includes a 50 ms coast interval.

The user reported reversed directions during intermediate versions, then confirmed the corrected controls were satisfactory. **Do not reverse the current mapping again solely because an older message said the robot was reversed.**

GPIO14 and GPIO15 overlap serial UART functions; GPIO4 overlaps the usual 1-Wire assignment. The documented setup disables serial login, serial hardware, and 1-Wire, while enabling I2C.

Recommended boot setting in `/boot/firmware/config.txt`:

```ini
[all]
gpio=4,17=op,dl
```

This sets the two enable pins LOW when firmware applies the configuration. It does not cover every instant of startup or replace a physical cutoff. The actual current Pi configuration was not reread for this handover.

### I2C findings

User command `sudo i2cdetect -y 1` showed devices at:

```text
0x40
0x70
```

`0x40` is the expected PCA9685 controller address. **`0x70` does not prove a TCA9548A multiplexer is present.** The PCA9685 normally supports an all-call address at `0x70`; this explains the second response without requiring another chip. A prior remembered identification of a TCA9548A was unsupported and must not be carried forward.

I2C bus 1 uses the Pi's SDA/SCL pins, BCM2/BCM3, physical pins 3/5.

### Servo channels and current software limits

Mapping is from the actual original backup's `webServer.py`, supported by the assembly diagram. Initial values and 50 Hz operation come from `RPIservo.py`. Narrower reference limits come from backup `config.txt`.

| Joint | PCA9685 channel | Current minimum | Current maximum | Initial commanded value | Finite test cycle |
|---|---:|---:|---:|---:|---|
| Camera tilt | 11 | 201 | 300 | 300 | 300 → 270 → 300 |
| Lower arm | 12 | 300 | 430 | 300 | 300 → 330 → 300 |
| Upper arm | 13 | 139 | 443 | 300 | 300 → 270 → 300 |
| Wrist rotation | 14 | 300 | 500 | 300 | 300 → 330 → 300 |
| Gripper | 15 | 300 | **330** | 300 | 300 → 330 → 300 |

Values are **PWM ticks**, not degrees. At nominal 50 Hz, 300 ticks is approximately 1.465 ms and 330 ticks approximately 1.611 ms. Actual joint angles depend on the servo and installation.

The backup's global driver bounds were 100–520. Its per-channel config listed a gripper maximum of 500. The new gripper maximum is deliberately **330**, because the user reported full pinching during the small 300–330 test.

The archived web server did not load `config.txt`. Its values therefore are useful reference limits, **not measured mechanical endpoints**. Some archived presets also need separate interpretation rather than blanket reuse.

The supplied assembly tutorial's printed pages 72–73 identify the five channels. These correspond approximately to PDF pages 63–64 because document page labels differ from PDF indices.

**Critical distinction:** `server/servo.py` in the same backup uses a different, older channel path around 0–3. It is not the mapping used by the working web app. Follow `webServer.py` → `RPIservo.py` for this robot.

## 5. OS, SSH, VS Code, and Codex history

### Original system

User-provided terminal output established:

```text
User: viola
Hostname: viola-pi
Model: Raspberry Pi 3 Model B Rev 1.2
OS: Raspbian GNU/Linux 12 (bookworm)
uname -m: armv7l
getconf LONG_BIT: 32
```

Original source files were found at:

```text
/home/viola/adeept_rasptank/server/webServer.py
/home/viola/adeept_rasptank/server/move.py
/home/viola/adeept_rasptank/server/servo.py
/home/viola/adeept_rasptank/server/RPIservo.py
```

### Why terminal SSH worked while VS Code Remote SSH failed

PuTTY and normal SSH in the VS Code terminal worked. Remote SSH repeatedly asked for the platform/password and failed to install its server.

Recovered diagnosis: `Error installing server: platform not currently supported: Linux ARM32`. The inspected versions were VS Code 1.142.0 and Remote SSH 0.128.0. Official VS Code documentation states that 1.122 was the last release with prebuilt Linux ARM32 servers; 1.123 and later require x64 or ARM64 for that server.

An earlier `useExecServer=false` attempt did not resolve the problem. A portable 1.122.1 workaround was considered, but the project direction became a clean 64-bit Lite installation.

This was a VS Code server/architecture issue, not proof of a bad SSH password.

### Reinstalled system and remaining verification

The chosen target was **Raspberry Pi OS Legacy Lite, 64-bit, Bookworm**. Subsequent user output established:

```text
User: robotino
Hostname: robotino-pi
Python: 3.11.2
I2C bus 1: 0x40 and 0x70
```

The normal connection used in project documentation is:

```text
robotino@robotino-pi.local
```

A fresh `uname -m` / `getconf LONG_BIT` transcript from the reinstalled Pi is not in the evidence available here. Treat 64-bit Bookworm as the intended/documented target; confirm the live machine when diagnosing architecture-dependent behavior.

### Codex installation

A separate extension-installation problem involved marketplace/network `ERR_CONNECTION_RESET`. A phone-hotspot retry was suggested, but the evidence does not establish which action fixed it.

A later local extension installation, `openai.chatgpt-26.1007.21434-win32-x64`, and a subsequent VS Code Codex session were found. The user was already giving feedback and requesting changes through that session by the evening of 18 October. Therefore it is inaccurate to hand over “Codex is still not installed” as the current state.

Use the local repository in VS Code, open the Codex sidebar, and give the next AI this document and access to the correct files. Signing into an account should not be treated as automatic transfer of the entire prior conversation.

### Where work happens

| Place | Role |
|---|---|
| Windows PC, local VS Code | Edit code and use Codex against the local repository. |
| GitHub Desktop | Inspect changes, commit locally, publish/push, and follow the PR workflow. |
| GitHub | Shared source history and review; it does not run the robot. |
| Pi SSH terminal | Run the Python application against actual GPIO/I2C. |
| PC browser | Keyboard/slider interface, connected through SSH forwarding. |

Editing the PC file, committing, pushing, and deploying to the Pi are four different operations. The current workflow does not automatically synchronize the PC and Pi.

## 6. Backups and recovery evidence

### Original source archive — verified hash

Windows path:

```text
C:\Users\adrie\Robotino-backup\robotino-original-2026-10-18.tar.gz
```

Original Pi path:

```text
/home/viola/robotino-original-2026-10-18.tar.gz
```

Size: **15,788,821 bytes**.

SHA-256:

```text
4cd73698aee3ab4e6b8230a9b96773fc8858d2b1a34fbcf68aaedddbf0821efa
```

The PC and Pi hashes supplied by the user matched exactly, ignoring letter case. Rehashing the local archive on 25 October produced the same value.

This is a source/application backup, **not a complete SD-card image**. It is an important reference because it represents the actual previously working installation rather than an assumed matching public GitHub version.

Archived code was inspected as data. Do not import or run old `webServer.py`/`RPIservo.py` casually: their initialization can configure hardware and command servos.

### Full original SD-card image

```text
C:\Users\adrie\Robotino-backup\robotino-full-original.img
```

Current inspected size: **62,226,694,144 bytes**, approximately 62.23 GB decimal.

During the original backup, the file was initially still growing and locked, despite an early “done” message. The guidance was corrected to wait until reading finished before reflashing the card. Win32 Disk Imager's full-card Read procedure was used/instructed; Verify Only was suggested afterward.

The evidence does **not** establish a completed restore test or a recorded whole-image SHA-256.

Additional read-only inspection on 25 October found:

- An MBR signature of `55 aa`.
- First partition: start sector 16,384; length 1,048,576 sectors.
- Second partition: start sector 1,064,960; length 120,471,552 sectors.
- Using 512-byte sectors, the second partition ends exactly at byte 62,226,694,144, matching the file size.

This supports that the image is not simply the early truncated copy. It does not validate all filesystem contents or guarantee restorability.

Keep this image privately available for recovery. A full OS image can contain Wi-Fi credentials, account data, and keys. It is not a useful default attachment to an AI, and it is not included in the handover ZIP.

## 7. Timeline of attempts, failures, corrections, and physical feedback

Dates below use Belgian local time where a precise session timestamp was available. October 18–20 was UTC+02. These are selected project-relevant records, not a full private chat export.

| Stage / date | What happened | What it establishes |
|---|---|---|
| Before reset | User reported original tracks, arm, and camera working. | The stock hardware had previously operated. This does not identify every cable or prove present battery condition. |
| Initial connection setup | Normal SSH worked; VS Code Remote SSH looped and ARM32 server installation failed. | Architecture compatibility issue identified; 64-bit Lite reinstall selected. |
| Backup stage | Original source archive copied; PC and Pi SHA-256 matched. Full SD image made after noticing it was still growing. | Source copy integrity verified. Full restore remains untested. |
| New Pi setup | Hostname robotino-pi, Python 3.11.2, I2C 0x40/0x70 reported. | New login and I2C access established. |
| Initial keyboard implementation, 18 Oct | Browser UI, GPIO driver, local HTTP server, deadman controls, session expiry, tests and docs created. Fixed 25% duty, 0.4 s server expiry, 0.3 s browser timeout. | Initial baseline; now superseded. |
| Initial desktop verification | 17 Python tests and 5 JavaScript tests passed; initial simulated browser connect/STOP was checked. | Hardware-free behavior only. |
| 18 Oct, 23:09 | User: web page constantly timed out; 25% was too weak, one track struggled, rover could not move its weight; forward/reverse were switched; requested on-page speed changes. | Actual physical and usability problems; not evidence that wiring alone was faulty. |
| First feedback correction | Added duty slider, raised default to 50%, permitted 0–100%, increased request timeout to 1.5 s and server expiry to 2 s; adjusted direction mapping. | Addressed reported torque/usability issues, with a longer possible stop delay on link loss. |
| 18 Oct, 23:20 | User: “works very good,” but forward/backward and left/right were still reversed. | First direction correction was incomplete. |
| Second direction correction | Track polarity handling updated again. | Current map is the result to preserve. |
| 18 Oct, 23:28 | User: “ok its all perfect,” then requested Git explanations. | User accepted the corrected driving behavior. No measured endurance or stopping-distance result was supplied. |
| 19 Oct, 22:37 | User reported that everything integrated so far worked. | Reinforces acceptance of the driving milestone. |
| 19 Oct, 22:59 | User said the PR had been accepted and a new arm branch created from main. | Start of separate arm work. |
| 19 Oct, 23:44–23:45 | Initial very short servo pulses produced a small buzz on the first test, no visible movement in the others. User confirmed buzz during the pulse, battery supply on, main switch on. | Tiny pulse approach was inconclusive, not proof of a dead servo or failed board. |
| 19 Oct, 23:50 | PCA9685 register inspection showed awake/internal clock, prescale 121, non-inverted output, and channel fully off after cleanup. | Digital controller state was readable; cleanup state observed. |
| 20 Oct, 00:01 | User reported no obstruction and asked to base meaningful finite tests on the original archive. | Investigation shifted to actual original configuration and a visible finite motion cycle. |
| Finite-test implementation | Added a slow 300 → nearby target → 300 cycle on one channel, with readback and release. | Replaced ineffective 0.2 s / 5-tick identification pulses. |
| 20 Oct, 00:16 | User: “it all worked,” camera tilt very slow, gripper fully pinched; requested full per-joint sliders/keyboard and faster movement. | Successful finite camera-tilt and gripper tests. Do not interpret as measured validation of every joint endpoint. |
| Following arm implementation | Integrated five joints, speed control, hold/release behavior, backend limits, narrowed gripper maximum, tests/docs. | Code exists on the arm branch. No subsequent explicit physical acceptance of the full browser arm UI was found. |
| 25 Oct handover | Inspected local revisions, recovered relevant feedback, reran both suites, copied hardware PDFs, checked backup integrity evidence. | Current evidence package; no robot movement performed. |

### Register output preserved from the unsuccessful-probe investigation

```text
mode2 0x04
prescale 121
asleep false
external_clock false
auto_increment true
inverted_output false
nominal_hz_if_internal_25mhz 50.03
on_ticks 0
off_ticks 44
full_on false
full_off true
```

With `full_off true`, the channel is off; the stored `off_ticks 44` does not mean a 44-tick pulse was actively driving the servo at that moment. Register readback establishes programmed digital state, not actual servo angle, supply voltage, or waveform quality.

## 8. Current track-control implementation

### Main files

| File | Responsibility |
|---|---|
| `robotino_app.py` | HTTP server, hardware selection, session endpoints, watchdog, shutdown. |
| `drive.py` | GPIO mapping, PWM, duty selection, controller/session logic. |
| `web/index.html` | English control interface. |
| `web/controls.js` | Keyboard state, duty slider, heartbeats, connection handling. |
| `tests/test_drive.py` | Controller and mocked motor checks. |
| `tests/test_http.py` | HTTP/session/input validation checks. |
| `tests/test_keyboard.cjs` | Browser-control logic under Node.js. |
| `move.py` | Retained vendor example; not the new app's motor implementation. |
| `README.md` | Setup, usage, physical-check procedure, and limitations. |

The current main README describes the keyboard milestone. Its statement that arm and camera are not implemented is true for that revision; it must not be generalized to the arm branch.

### Current settings versus the obsolete first version

| Setting | First version | Current inspected code |
|---|---:|---:|
| Default duty | Fixed 25% | 50% |
| Adjustable duty | None | 0–100%, 5-point UI steps |
| Server session expiry | 0.4 s | 2.0 s |
| Browser request timeout | 0.3 s | 1.5 s |
| Heartbeat scheduling | Around 80 ms plus round trip | Around 80 ms plus round trip |
| Watchdog check period | 20 ms | 20 ms |
| Reversal coast | 50 ms | 50 ms |

Duty is a PWM power command, **not a measured vehicle speed**. There is no encoder-based left/right speed balancing. Zero duty stops powered drive; increasing duty cannot rule out track friction, poor contacts, weak batteries, or a mechanical fault.

### Input and session behavior

- Hold Shift plus one direction: arrows or AZERTY ZQSD.
- Conflicting direction keys request stop.
- Release Shift or the direction key to send a stop state on the next heartbeat.
- STOP, Escape, Space, window focus loss, hidden tab, or connection failure clears controls and requires explicit reconnection.
- A focused range slider uses arrow keys for normal slider adjustment; click elsewhere before driving with arrows.
- Changing the duty slider alone does not initiate movement.
- Only one active control session is accepted.
- Each command carries a one-use server challenge, preventing duplicate/stale movement requests from renewing a session.
- The browser keeps at most one drive request in flight and does not automatically reconnect after a fault.

### Server and hardware behavior

- HTTP is bound to `127.0.0.1:8765` on the Pi.
- Access is through an SSH local port forward, not an unauthenticated public LAN listener.
- POST endpoints include `/api/connect`, `/api/drive`, and `/api/stop`.
- A per-process random token, local host/origin checks, and bounded/validated requests protect the browser control interface.
- Hardware mode checks the expected Pi model and serial-console conflict, and uses a cooperative process lock.
- The server port is bound before opening motor hardware, reducing accidental competing controller starts.
- Both PWM enables start at zero. The old vendor example's initial 100% duty pulse is not reproduced.
- Normal exit drives enables LOW rather than relying on GPIO cleanup that returns pins to inputs.
- The hardware-free mode avoids opening GPIO/I2C.

### Material limitations to retain in the handover

The two-second timeout resolved reported nuisance expiry, but a lost release message or link can leave motor power applied for roughly two seconds after the last accepted command, plus scheduling effects. This needs actual measurement on the small event course, especially at higher duty.

The watchdog is software in the same Linux/Python system. Process freezes, blocking hardware calls, electrical faults, or forced termination can defeat software cleanup. The cooperative lock does not stop arbitrary old programs from accessing GPIO.

These are review priorities, not evidence that every failure has occurred. Do not blindly restore the old 0.4 s setting and reintroduce known usability failures; measure the actual communication and stopping behavior.

## 9. Arm branch implementation and semantics

Additional files include:

- `arm.py` — joint definitions, bounds, ramping, hold/release and jogging.
- `hardware.py` — shared hardware-access checks.
- `servo_probe.py` — PCA9685 register operations and diagnostic probing.
- `servo_test.py` — bounded finite single-channel motion test.
- `ARM_CONTROL.md` and `SERVO_PROBING.md`.
- Additional arm, servo-motion, and probe tests.
- Integrated changes to the HTTP/controller and browser files.

### Hardware selection

| Command, run on Pi | Effect |
|---|---|
| `python3 robotino_app.py` | Simulated tracks and servos; no GPIO/I2C access. |
| `python3 robotino_app.py --hardware` | Real tracks, simulated servos. |
| `python3 robotino_app.py --servos` | Real servos, actual track-enable pins held LOW. |
| `python3 robotino_app.py --hardware --servos` | Real tracks and real servos. |

The arm branch needs the OS package `python3-smbus` in addition to `python3-rpi.gpio`, and the normal user needs the `i2c` and `gpio` groups.

Starting the real servo controller switches old PWM signals off. Starting the application, connecting, or clicking **Enable arm + camera** does not command all joints to a position. The first slider/key action for a joint starts from its last commanded value in the process, initially 300.

**Actual position is not sensed.** The initial command can therefore cause an abrupt move from the physical starting position. A software ramp cannot correct unknown initial position by itself.

### Browser arm controls

Sliders select 0–100% of the configured joint range. The percentage is neither an angle nor measured position. Slider movement does not require Shift.

Keyboard jogging requires Shift plus one joint key:

| Joint | Keys |
|---|---|
| Camera tilt | I up / K down |
| Lower arm | R up / F down |
| Upper arm | T up / G down |
| Wrist | J left / L right |
| Gripper | O open / P close |

Directions follow the original app; lower arm, upper arm, and wrist directions still need clear physical confirmation.

Movement speed is adjustable from 25–200% of the normal command rate. Normal is 100 PWM ticks/second, so the range is 25–200 ticks/second. Software updates are approximately every 20 ms. This is a rate of position-command change, not torque control.

- Releasing a jog key freezes the commanded position while maintaining holding torque.
- **Hold position** cancels target travel/jogging but keeps current servo signals.
- **Release servos** removes servo signals and disables arm control.
- STOP, Escape, Space, focus loss, hidden tab, and expired session stop tracks **and release servo support**.
- Reconnection and re-enabling are explicit; old targets do not resume automatically.

The release policy can let a raised arm or held object sag/drop. Review it against the actual mechanism and public-event task. Do not assume “remove PWM” and “hold safely in place” are equivalent.

### Why the finite servo test succeeded where tiny probes did not

The original short probe used approximately 0.2-second, five-tick changes. The user heard buzzing but saw no useful movement. Subsequent investigation used the original archive's known 300-tick reference and a longer visible cycle.

`servo_test.py`:

1. Holds track enables LOW and releases previous servo signals.
2. Commands only the chosen channel to 300.
3. Ramps in one-tick steps, 40 ms apart, to a nearby target.
4. Returns to 300.
5. Reads back controller registers at landmarks.
6. Releases signals and exits; the default cycle is approximately 3.5 seconds.

Its narrow test window is 260–340 ticks intersected with the channel's reference bounds. Supported travel choices include 10, 20, 30, and 40 ticks; invalid directions/ranges are rejected before opening hardware. Tests are individual, not an automatic all-joint sweep.

Examples, for reference only:

```bash
# Simulation; no movement.
python3 servo_test.py --channel 11

# Physical actions: only when deliberately ready to move that joint.
python3 servo_test.py --channel 11 --hardware
python3 servo_test.py --channel 15 --hardware
```

The read-only diagnostic:

```bash
python3 servo_probe.py --channel 11 --inspect
```

reads the existing controller state without changing outputs. **It is not a stop command.**

## 10. Validation ledger

### Software checks rerun on 25 October

Tests ran against the exported tracked code on the Windows PC, using Python and Node.js. Real GPIO/I2C was not accessed.

| Snapshot | Python unittest | Node.js browser logic | Result |
|---|---:|---:|---|
| Main, `73fae8a…` | 25 passed | 10 passed | 35 passing tests |
| Arm branch, `d5b0eb2…` | 60 passed | 16 passed | 76 passing tests |

The branches share many tests. Do not describe their sum as 111 independent tests of the robot.

Log files:

```text
03_validation/01_main_python.txt
03_validation/01_main_javascript.txt
03_validation/02_arm_control_python.txt
03_validation/02_arm_control_javascript.txt
```

Coverage includes deadman logic, stale/duplicate sessions, timeouts, invalid inputs, duty changes, HTTP protections, motor initialization/reversal/shutdown behavior, browser keyboard/slider behavior, and—in the arm branch—joint bounds, ramping, hold/release, servo register operations, cleanup, and simulated versus real hardware selection.

The historical initial baseline had 17 Python and 5 JavaScript tests. That older count does not describe the current snapshots.

A real browser connect/STOP exercise was recorded for the original simulated interface. The latest arm page was not visually/browser-tested during this handover.

### Physical validation status

| Capability | Recorded evidence | Remaining uncertainty |
|---|---|---|
| Original tracks/arm/camera | User said all worked before reset. | Present condition after changes and battery state. |
| Current corrected track directions and duty control | User accepted driving after two direction corrections. | Instrumented speeds, minimum reliable duty, left/right balance. |
| Communication usability | User accepted changes after initial timeout complaints. | Measured latency distribution and behavior at event venues. |
| Camera tilt servo | Successful finite test, reported slow. | Full travel and final browser control behavior. |
| Gripper servo | Successful finite cycle, reported fully pinched. | Safe grip force, payload behavior, full operating range. |
| Lower arm / upper arm / wrist | Mapping and code exist. | Explicit joint-by-joint movement, direction and limits not recorded. |
| Full integrated arm browser UI | Implemented; software tests pass. | No explicit physical acceptance recorded after implementation. |
| Software stops | Desktop logic tests; physical procedure documented. | Timed real link-loss/focus-loss/STOP tests not recorded individually. |
| PS4 input | Desired; controller/cable available. | Not implemented or tested in inspected code. |
| Camera video | Original software worked historically. | New streaming implementation, resolution/FPS/latency/CPU load not established. |
| Five-hour event use | Requirement only. | Runtime, temperatures, brownouts, fatigue, recovery, and operator workflow. |

## 11. Power and all-day operation: findings and open decisions

The user specifically asked about slow battery charging, spare/smaller batteries, larger capacity, and a thin tether to a lab supply.

No all-day power solution has been built or validated in this project evidence. No trustworthy average current, peak current, duty cycle, usable battery capacity, or endurance measurement is available.

Two stock lithium-ion cells in series are nominally about 7.4 V together and up to 8.4 V fully charged when they are ordinary 4.2 V cells. Series connection adds voltage; it does not double the amp-hour capacity. A claimed label capacity must not be used as a measured runtime.

Additional equipment mentioned in prior project context includes a blue 7.2 V / 3000 mAh NiMH pack, a green 8.4 V / 2000 mAh NiMH pack, an older 7.4 V LiPo, and a Graupner Ultramat 14 charger. Their labels/condition, connector polarity, charging suitability, and compatibility with this exact robot have **not** been established here. Do not turn these mentions into a purchase or wiring approval.

The nominal energy calculation alone gives 21.6 Wh for 7.2 V × 3 Ah and 16.8 Wh for 8.4 V × 2 Ah. That does not predict usable robot runtime or make either pack a safe substitute. Fully charged voltage and motor/servo/regulator limits matter.

Options discussed:

- Matched, properly charged spare stock-type packs swapped between runs.
- Measuring actual operating demand before deciding whether larger capacity is worthwhile.
- A regulated tether at a supply appropriate to the original battery input, with batteries disconnected and polarity, current capacity, wiring, and mechanical routing verified.
- A tether proposal around the stock nominal 7.4 V was a discussion direction, not a tested setting or complete design.

For a 2 × 2 m course with ramps/tunnels, tether drag and snagging need practical testing. No validated cable gauge, fuse, connector, supply current limit, or fast-charge procedure has been selected. Do not treat the shield's USB connector as an established charging input.

A useful next measurement plan is to record idle, driving, turning, and arm-operation demand, observe Pi undervoltage/temperature, and perform progressively longer supervised runs. Avoid deliberately stalling motors/servos merely to collect a number.

## 12. Event networking, PS4, and video

### Current networking

The implemented path is PC browser → SSH tunnel → Pi-local HTTP server → controller → GPIO/I2C. The current control page does not need an external internet service.

Venue Wi-Fi is not yet an established event solution. The Pi 3 Model B uses 2.4 GHz Wi-Fi. A dedicated small router or a tested local hotspot was a reasonable future direction for changing venues and short range, but neither is documented as purchased, configured, or endurance-tested.

Keep control-server exposure intentional. Do not change the bind address to all interfaces merely to make access easier without reviewing the session/authentication model.

### PS4 controller

Original Sony controller and USB data cable are available. No input library, browser Gamepad mapping, direct-Pi HID implementation, Bluetooth pairing, or disconnect behavior has been implemented in the inspected branches.

Two architectural choices remain: controller on the PC feeding the existing control session, or controller on the Pi for PC-independent driving. Select with the user, considering desired standalone operation and video. Reuse the established drive/arm command layer and explicitly handle controller disconnect/deadman behavior.

Do not invent tested button mappings or claim Bluetooth works on this robot.

### Video

The ribbon camera worked with the old software, but the exact camera model remains unknown. Servo tilt control is implemented on the arm branch; **video streaming is not**.

Official Raspberry Pi camera guidance uses the modern libcamera/rpicam stack, with Picamera2 for Python use. Legacy raspistill/raspivid and the original Picamera stack should not be assumed to work unchanged on the selected OS.

No modern camera package install, sensor detection, stream, or benchmark is recorded as completed in the new application. Evaluate camera detection and a modest stream only after control is stable, measuring responsiveness with tracks and arm active. If latency or CPU/memory contention is unacceptable, the user explicitly prefers omitting video.

## 13. Practical continuation instructions

### Start by confirming the local branch

On the PC, in the real repository:

```powershell
git status --short --branch
git log -1 --oneline
git branch -avv
```

Do not automatically switch branches over uncommitted work. The included snapshots are for review; the real repository is where development history belongs.

For further arm work, inspect `robotino/feature/arm-control` first. Review its changes relative to main and follow the team's PR process.

### Check the Pi without moving the robot

Commands to run in a normal SSH session when needed:

```bash
hostname
cat /proc/device-tree/model
cat /etc/os-release
uname -m
getconf LONG_BIT
python3 --version
id -nG
ps -ef | grep '[r]obotino_app.py'
ls -l ~/robotino
```

Determine whether an application is already running before starting another one. Inspect deployed source/configuration and compare relevant files or hashes to the intended revision. Do not assume a directory copied weeks ago matches today's PC branch.

A normal SSH connection is:

```powershell
ssh robotino@robotino-pi.local
```

The host name depends on the local network resolving it. No fixed current IP address or password should be invented.

### Existing dependency/setup instructions

On the Pi, if the packages are not already present:

```bash
sudo apt update
sudo apt install -y python3-rpi.gpio python3-smbus
```

The arm branch uses both packages. The keyboard branch needs RPi.GPIO. The core application otherwise uses the Python standard library; a new pip environment is not required for this baseline.

Use the normal `robotino` account, with `gpio` and `i2c` access. The documented raspi-config and boot-GPIO settings must be checked against the live configuration rather than repeatedly appended.

### Existing deployment method and a limitation

Stop the old app with Ctrl+C in its Pi terminal before replacing its files. From PC PowerShell at repository root, the documented copy is:

```powershell
scp -r .\robotino robotino@robotino-pi.local:~/
```

**SCP copies and overwrites files but does not remove files deleted on another branch.** Switching from the arm branch back to main this way can leave obsolete arm files on the Pi. The next AI should inspect the deployment and adopt a deliberate clean/versioned deployment method when needed, preserving local settings. Do not blindly delete the remote folder to resolve uncertainty.

Git commits/pushes alone do not deploy anything.

### Run a simulation through the tunnel

From PC PowerShell:

```powershell
ssh -L 8765:127.0.0.1:8765 -o ExitOnForwardFailure=yes robotino@robotino-pi.local
```

In the resulting Pi shell:

```bash
cd ~/robotino
python3 -m unittest discover -s tests -v
python3 robotino_app.py
```

In the PC browser, open http://127.0.0.1:8765 and hard-refresh after front-end changes. Confirm the simulation label. Keep the SSH session open.

On a PC with Python and Node.js, the code's tests can also be run from the chosen Robotino directory:

```text
python -m unittest discover -s tests -v
node --test tests/test_keyboard.cjs
```

The handover validation used the installed Codex runtime's Python/Node binaries; the user's shell may have different executable names.

Physical modes and finite test commands are documented earlier. They are not part of an automatic setup sequence. Keep the physical cutoff accessible, support the robot/arm appropriately for the intended check, and change one unverified mechanical behavior at a time.

Normal shutdown sequence: stop the application, run `sudo shutdown -h now`, wait for shutdown, then switch off power.

## 14. Priorities for the next AI

1. **Receive the user's current feedback and identify the active code/deployment.** Avoid recreating solved setup work.
2. **Preserve the accepted track controls.** Regressions to old directions, 25% fixed duty, or overly aggressive timeouts would discard actual progress.
3. **Complete physical arm validation.** Confirm lower/upper/wrist channels and directions, tighten endpoints from observations, and test the integrated controls. Camera and gripper have already moved successfully.
4. **Review position initialization and stop/release behavior.** First-command movement and arm sag are unresolved practical behaviors.
5. **Measure communication and stopping behavior on the actual Pi/course.** The current 2 s timeout and available 100% duty need event-specific evaluation.
6. **Make operation repeatable.** Decide event network, startup/shutdown and recovery workflow, deployment method, and operator controls before public use.
7. **Implement PS4 input through the existing control layer.**
8. **Evaluate optional video under realistic load.**
9. **Choose and validate power for the five-hour use case.** Measure before promising runtime or selecting a charger/pack.
10. **Record real test results in the repository.** Include revision, settings, observed behavior, and what remains untested.

These are priorities, not permission to silently expand scope or activate the robot remotely. Routine code investigation and authorized edits should proceed without repeatedly asking questions whose answers are already here.

## 15. What to give the next AI

### Minimum useful package

1. **This handover document.**
2. **The accompanying ZIP**, or access to the repository including the arm branch—not just main.
3. **The user's new feedback**, screenshots, and exact error output when relevant.

The ZIP already includes both source versions, their project instructions, arm/probing guides, test logs, and these two hardware documents:

- `Assembly_tutorial.pdf` — the supplied “2 Assembly tutorial.pdf”.
- `Adeept_Motor_Shield_V2_Schematic.pdf` — the supplied “Circuit-Schematic-AdeeptMotorShield-V2.0.pdf”.

```

The assembly tutorial was under `4. Assembly tutorial\2 Assembly tutorial.pdf`. The schematic was at the documentation root. Copies in the ZIP retain the source PDF contents, with simpler filenames.

### Add when the AI needs original-software details

`robotino-original-2026-10-18.tar.gz`, from the backup path in section 6. The most relevant archived files are:

```text
adeept_rasptank/server/move.py
adeept_rasptank/server/webServer.py
adeept_rasptank/server/RPIservo.py
adeept_rasptank/server/servo.py
adeept_rasptank/server/config.txt
```

The archive is not bundled here. Share it privately when needed after reviewing it for credentials. It is more relevant than unrelated STM32/large-rover documents.

Useful additional evidence, only if the next task needs it: clear shield/servo-connector photos, camera label, short joint-motion videos, current Pi architecture and deployment output, and actual battery labels.

### Keep for recovery, not routine AI upload

The 62.23 GB full SD image. Keep the original archive and SD image unchanged. The older `robotino-keyboard.patch` and preview image are historical artifacts, not the authoritative current implementation.

Do not provide a full private Codex session dump just to preserve these facts. Relevant feedback is already summarized and quoted in this document.

## 16. Documentation and research register

The following sources explain the decisions above. They are primary/vendor references where available. Hardware PDFs and the actual original archive take precedence over guessed compatibility from a similarly named product. Pages may change after this handover.

### Hardware and original software

**[S1] Adeept original RaspTank repository**  
https://github.com/adeept/Adeept_RaspTank  
Used to identify the original green-board software family. The repository distinguishes this discontinued model from the purple-board upgrade, which uses a different repository. Do not substitute the newer board's pinout.

**[S2] Original web application**  
https://github.com/adeept/Adeept_RaspTank/blob/master/server/webServer.py  
Reference for original control commands and channel roles. The local dated backup was the main robot-specific evidence for mapping.

**[S3] Original servo implementation**  
https://github.com/adeept/Adeept_RaspTank/blob/master/server/RPIservo.py  
Reference for the original PCA9685 approach, starting positions, and general bounds. Inspect as text rather than importing initialization code.

**[S4] Original motor implementation**  
https://github.com/adeept/Adeept_RaspTank/blob/master/server/move.py  
Reference for GPIO assignments and vendor behavior; new code avoids the old startup PWM pulse. Public source was not assumed to be byte-identical to the dated backup.

**[S5] Supplied assembly tutorial and shield schematic**  
Included in `04_hardware_documents/`. Assembly pages support the five servo connections. The schematic supports identifying PCA9685, L298P, GS2678, and relevant supply/pin relationships. No public URL is needed to use these supplied originals.

**[S6] NXP PCA9685 datasheet**  
https://www.nxp.com/docs/en/data-sheet/PCA9685.pdf  
Used for 12-bit PWM registers, prescale/frequency interpretation, all-call addressing, and full-off behavior. At the nominal 25 MHz internal clock, prescale 121 corresponds to about 50.03 Hz. Digital settings and nominal calculations do not establish actual shaft position or waveform quality.

### Raspberry Pi and GPIO

**[S7] Raspberry Pi 3 Model B specifications**  
https://www.raspberrypi.com/products/raspberry-pi-3-model-b/  
Reference for the board family, RAM, 64-bit CPU capability, and wireless capabilities.

**[S8] Raspberry Pi OS images**  
https://www.raspberrypi.com/software/operating-systems/  
Used when choosing a Lite/64-bit image suitable for this board. The documented project target is Bookworm; do not silently change distribution release merely because the download page now promotes another version.

**[S9] Raspberry Pi getting started / Imager**  
https://www.raspberrypi.com/documentation/computers/getting-started.html  
Reference for writing the image and configuring hostname, account, wireless access, and SSH.

**[S10] Raspberry Pi configuration**  
https://www.raspberrypi.com/documentation/computers/configuration.html  
Reference for interface settings, including I2C and serial configuration.

**[S11] config.txt GPIO settings**  
https://www.raspberrypi.com/documentation/computers/config_txt.html#gpio  
Basis for driving enable pins LOW through firmware configuration. This acts after firmware reaches the setting, and later software can reconfigure pins.

**[S12] RPi.GPIO basic usage**  
https://sourceforge.net/p/raspberry-gpio-python/wiki/BasicUsage/  
Reference for BCM mode, initial output state, and cleanup semantics. The new application intentionally leaves motor-enable outputs LOW on ordinary shutdown.

**[S13] RPi.GPIO PWM**  
https://sourceforge.net/p/raspberry-gpio-python/wiki/PWM/  
Reference for PWM initialization and duty changes. PWM commands here are open-loop motor duty, not measured speed.

### Development tools and backups

**[S14] VS Code Remote Development FAQ**  
https://code.visualstudio.com/docs/remote/faq  
Reference for the Linux ARM32 server-support change: 1.122 was the final prebuilt ARM32-server release; newer servers require a supported architecture. Explains why normal SSH could succeed while Remote SSH installation failed.

**[S15] VS Code 1.122 remote release notes**  
https://github.com/microsoft/vscode-docs/blob/main/remote-release-notes/v1_122.md  
Additional reference considered during the architecture investigation. The portable older-version workaround was discussed, not the final selected deployment plan.

**[S16] VS Code Remote SSH documentation**  
https://code.visualstudio.com/docs/remote/ssh  
Reference for SSH hosts, server setup, diagnostics, and forwarding. A terminal SSH connection and a VS Code remote server installation are separate operations.

**[S17] OpenAI Codex IDE documentation**  
https://developers.openai.com/codex/ide/  
Reference for the VS Code extension and local coding workflow; the local installed extension was also inspected. This documentation may redirect to OpenAI's current learning site. No claim is made that a new IDE chat automatically inherits this conversation.

**[S18] Win32 Disk Imager**  
https://sourceforge.net/projects/win32diskimager/  
Tool used/discussed for reading the SD card into a full image and verifying it. Its availability is not evidence that the user's image passed a restore test.

### Future camera work

**[S19] Raspberry Pi camera software**  
https://www.raspberrypi.com/documentation/computers/camera_software.html  
Reference for the modern rpicam/libcamera stack and migration away from legacy camera commands. Relevant research for the next milestone, not a completed streaming implementation.

**[S20] Picamera2 project**  
https://github.com/raspberrypi/picamera2  
Official Python camera-library reference for a possible later implementation. No Picamera2 application or measured streaming result is included in the current code.

**[S21] Team repository**  
https://github.com/Olympus-MARS-Leuven/rover-2026  
Source of project branches and team workflow. The exact commits exported in this handover are recorded in section 3; current remote state should be checked before contributing.

## 17. Corrections and uncertainties that must survive the handover

- `0x70` is not evidence of an installed I2C multiplexer.
- The relevant camera servo is **tilt**, not a proven pan axis.
- Camera-servo control does not mean video streaming exists.
- `main` does not include the inspected arm implementation.
- The initial fixed 25% duty and 0.4 s timeout are obsolete.
- The user already confirmed corrected driving and successful finite camera/gripper movement.
- The tiny-pulse buzzing attempt was inconclusive; do not restart that investigation without a concrete reason.
- Archive/config limits are not verified mechanical endpoints.
- The gripper's current 330-tick cap deliberately replaces the archive's 500.
- `full_off true` overrides the stored pulse-width count.
- The Pi's new 64-bit architecture is the documented target but lacks a fresh recorded architecture check here.
- Successful source-archive hashing is not verification of the full SD image.
- Desktop tests are not physical safety, endurance, or performance certification.
- No recorded five-hour battery test, PS4 implementation, camera stream benchmark, or final arm-UI physical sign-off exists.
- No fresh GitHub fetch or live Pi inspection was performed for this handover.
- Proposed power/network choices are not purchased or validated equipment.
- Do not mix hardware assumptions from the larger ERC rover into Robotino.

## 18. Suggested first message to the next AI

> Continue the Robotino project using this handover and the attached source/document package. First inspect the repository and confirm the active branch and Pi deployment. The corrected keyboard controls have been accepted by the user. Camera-tilt and gripper finite tests worked. Integrated five-joint control exists on robotino/feature/arm-control at d5b0eb2cb8d4e059ed1b61d5110a6f30339ee465 and is not in the inspected main. Preserve that progress, read ARM_CONTROL.md and SERVO_PROBING.md, and distinguish software tests from physical observations. I am a beginner: explain useful batches of steps and label PC versus Pi commands. My new feedback is: [add feedback here]. Do not move hardware merely to inspect or load the project.

---

**Scope of this handover:** comprehensive reconstruction of the relevant available evidence, not a claim to possess every past message or an unstated test result. When a new observation conflicts with this document, record the observation and the exact deployed revision before changing conclusions.

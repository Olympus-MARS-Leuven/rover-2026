# Servo testing with the original Robotino code as a reference

All five joints now also have browser sliders and keyboard jogging. Start with
[ARM_CONTROL.md](ARM_CONTROL.md) for normal control; this guide covers the
standalone finite test and diagnostics.

Work on `robotino/feature/arm-control`. The driving code has been physically
checked. Servo wiring and joint limits still require observations on this robot.

## What the backup establishes

The user supplied `robotino-original-2026-10-18.tar.gz`. Its
`adeept_rasptank/server/webServer.py` uses `RPIservo.ServoCtrl.singleServo()`
with these channels:

| Channel | Original web-app command | Physical role from the assembly diagram | Default test |
| --- | --- | --- | --- |
| 11 | up / down | Camera tilt | 300 -> 270 -> 300 |
| 12 | armup / armdown | Lower arm joint | 300 -> 330 -> 300 |
| 13 | handup / handdown | Upper arm joint | 300 -> 270 -> 300 |
| 14 | lookleft / lookright | Wrist rotation | 300 -> 330 -> 300 |
| 15 | grab / loose | Gripper | 300 -> 330 -> 300 |

The backup's `RPIservo.py` uses I2C address `0x40`, bus 1, 50 Hz and initial
positions of 300 ticks. Its software-wide bounds are 100-520 ticks. Its
`config.txt` also contains per-channel ranges: 11=201-300, 12=300-430,
13=139-443, 14=300-500 and 15=300-500. The web server does not load that file,
so these values are additional reference bounds, not measured mechanical limits.
The new test intersects them with a narrow 260-340 window around 300.

The older `server/servo.py` in the same backup uses channels 0-3 and belongs to
a different control path. Use the web-app mapping above for the current tests.
The supplied assembly tutorial, printed pages 72-73, agrees on channels 11-15.
The archive was inspected as data; no archived program or setup script was run.

The public [webServer.py](https://github.com/adeept/Adeept_RaspTank/blob/master/server/webServer.py)
and [RPIservo.py](https://github.com/adeept/Adeept_RaspTank/blob/master/server/RPIservo.py)
provide the same channel commands and general servo-control approach. Our tool
uses the existing OS-provided SMBus package and does not import the vendor app,
which initialises every channel when imported.

## How the new test works

`servo_test.py` runs one finite cycle on one channel:

1. Disable old servo signals and keep both track enables LOW.
2. Command only the selected channel to the original 300-tick starting position.
3. Move in 1-tick increments to a nearby target, then return to 300.
4. Check the controller's position-register readback at the start, target and return.
5. Release all servo signals and exit after about 3.5 seconds by default.

It waits 40 ms between ramp steps and briefly holds each landmark. This makes
movement more visible than the earlier 0.2-second, 5-tick identification pulses.
The actual servo position is not measured. Readback confirms digital settings,
not actual motion, voltage at a servo, or signal quality.

Simulation is the default. `--hardware` explicitly enables the real test. The
initial movement to 300 is from an unknown position; support the arm, clear the
gripper and keep physical power cutoff accessible. Signal release removes
holding torque. Stop with Ctrl+C if movement strains or reaches an obstruction.
Normal exit, interrupts and errors attempt release; a forced kill or an I2C/
hardware fault can defeat software cleanup.

## PC: copy the updated files

First stop the driving app with Ctrl+C in its Pi terminal. In **PC PowerShell**,
from the repository root:

```powershell
scp -r .\robotino robotino@robotino-pi.local:~/
```

Use your existing SSH session or open one from **PC PowerShell**:

```powershell
ssh robotino@robotino-pi.local
```

The servo tests use the terminal; no browser or port forward is required.

## Pi: check simulation, then run one real test

In the **Pi terminal**:

```bash
cd ~/robotino
python3 -m unittest discover -s tests -v
python3 servo_test.py --channel 11
```

The simulation command should print `300 -> 270 -> 300` without moving anything.
The existing `python3-smbus` and `python3-rpi.gpio` packages are used. If SMBus has
not been installed, run `sudo apt install -y python3-smbus`. Run the test without
sudo; the Robotino user needs the `gpio` and `i2c` groups.

When ready for real movement, start with the camera candidate:

```bash
python3 servo_test.py --channel 11 --hardware
```

Observe the entire cycle and share which part moved. If it completes normally,
try the gripper separately, with nothing held in it:

```bash
python3 servo_test.py --channel 15 --hardware
```

The remaining channels can then be tested individually with `--channel 12`,
`--channel 13` or `--channel 14`. Do not put the tests in an automatic loop.

`--travel 10`, `20`, `30` (default), or `40` changes the distance from 300 ticks.
For example, a smaller first test is:

```bash
python3 servo_test.py --channel 11 --travel 10 --hardware
```

`--direction negative` or `--direction positive` overrides the default only when
that direction fits the channel's test window. Channel 13 permits both; channel
11 permits negative only, and 12/14/15 permit positive only with these reference
bounds. Invalid requests are rejected before hardware is opened. These tests
establish movement and channel roles; they do not calibrate full travel limits.

## Diagnostics and observations so far

The earlier channel-11 pulse buzzed without visible movement. Follow-up small
pulses also produced no reported movement. Battery power and the main switch
were on. Subsequent register inspection showed the controller awake, internal
clock, non-inverted output, prescale 121 (nominal 50.03 Hz), and channel 11 fully
OFF after cleanup. The user reports no mechanical obstruction.

The user subsequently confirmed that the finite camera and gripper tests worked:
camera tilt was slow and the gripper fully pinched during the 300-330 cycle.
The browser controller therefore provides adjustable movement speed and caps the
gripper at 330 ticks. The remaining joints and all full endpoints still require
physical checks. Record the actual part moved, direction, sound and terminal
output for each channel.

The original short probe and read-only inspection remain available:

```bash
python3 servo_probe.py --channel 11 --inspect
```

Inspection reads I2C registers only and leaves existing outputs as found. It is
not a stop command. The controller-register implementation follows the
[NXP PCA9685 datasheet](https://www.nxp.com/docs/en/data-sheet/PCA9685.pdf).

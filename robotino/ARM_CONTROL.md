# Arm and camera-tilt control

The five joints share the page and the control session with the tracks. They
can be moved with sliders, with Shift + keys, or with the PS4 controller in ARM
mode. The earlier finite test moved the camera and fully pinched the gripper;
the other joints are checked and measured in the **Setup & tests** tab (see
[FIRST_RUN.md](FIRST_RUN.md)).

## Select the real hardware explicitly

| Command (Pi terminal) | Real hardware enabled |
| --- | --- |
| `python3 robotino_app.py` | None; tracks and servos simulated |
| `python3 robotino_app.py --servos` | Servos; real track enables held LOW |
| `python3 robotino_app.py --hardware` | Tracks; servos simulated |
| `python3 robotino_app.py --hardware --servos` | Tracks and servos |

With `--servos` the page says **REAL SERVOS**. The Pi needs the
`python3-rpi.gpio` and `python3-smbus` OS packages and the user's `gpio`/`i2c`
groups. Run as `robotino`, without sudo.

## Where a joint starts

Servos report no position, so the first command to an unpowered joint makes it
jump to whatever value is sent. The software therefore estimates where each
joint is:

| Source | Used for | Shown as |
| --- | --- | --- |
| Measured rest pose | Lower and upper arm: gravity always pulls them to the same rest | `rest` |
| Remembered position | Camera, wrist, gripper: they stay where they were released | `remembered` |
| Archive value 300 | Anything not yet known | `unknown` |

Rest poses are measured in Setup & tests step 5. Remembered positions are saved
in `~/.config/robotino/arm-state.json` whenever real servos are released.

Starting the app switches old servo signals off. Enabling the arm (button, or
△ on the controller) powers the joints with a known position one by one,
0.3 s apart, so the arm does not flop and the batteries see no single large
current peak. Joints with an unknown position start only when first used.

## Moving the joints

- **Sliders** choose a target within the limits; the joint ramps to it. The
  output shows the percentage and the commanded PWM ticks.
- **Keyboard**: hold Shift plus one joint key. Releasing either freezes the joint.

  | Joint | Keys while holding Shift |
  | --- | --- |
  | Camera tilt | I = up, K = down |
  | Lower arm | R = up, F = down |
  | Upper arm | T = up, G = down |
  | Wrist rotation | J = left, L = right |
  | Gripper | O = open, P = close |

- **Controller, ARM mode**: left stick ↕ lower arm, right stick ↕ upper arm,
  right stick ↔ wrist, R2/L2 close/open the gripper, D-pad ↑/↓ camera tilt.
  The speed follows how far the stick or trigger is pushed, several joints can
  move together, and L1/R1 give 40% precision movement.

Keys and sticks name a physical direction (up, left, close…). Which tick
direction that is comes from the measured calibration (Setup & tests step 3),
so the controls stay correct even if a servo is mounted the other way round.

**Movement speed** covers 25–200% of the normal rate of 100 PWM ticks per
second (D-pad ←/→ in ARM mode). It is the rate of position commands, not servo
torque. Updates run about every 20 ms.

## Hold, park, freeze and release

- **Hold position**: cancel travel and jogging; keep holding.
- **Park at rest pose** (□ on the controller): ramp the lower and upper arm to
  their measured rest poses. Shown only after rest poses are saved.
- **STOP / Esc / Space / ○ / lost link / hidden tab**: the tracks stop at once;
  the arm **freezes and keeps holding for 10 seconds**, then releases. The page
  shows the countdown. Enabling the arm again within those 10 seconds continues
  from where it is, without a jump.
- **Release servos** (Share): remove all servo signals at once. Lower and upper
  arm sag to their rest pose.

A frozen arm still uses battery and still pushes against whatever it holds.
Release it if something is trapped.

## Limits and calibration

Initial limits come from `server/config.txt` in
`robotino-original-2026-10-18.tar.gz` (channels from `webServer.py`, the 300
start value from `RPIservo.py`). They are not measured endpoints:

| Joint | Channel | Archived minimum | Archived maximum |
| --- | --- | --- | --- |
| Camera tilt | 11 | 201 | 300 |
| Lower arm | 12 | 300 | 430 |
| Upper arm | 13 | 139 | 443 |
| Wrist rotation | 14 | 300 | 500 |
| Gripper | 15 | 300 | 330 (tested 300–330 cycle was already fully pinched) |

Setup & tests replaces them with measured values, stored in
`~/.config/robotino/calibration.json`:

- **channel** and **direction** of each joint, from watching a 20-tick wiggle;
- **minimum** and **maximum**, from the two safe ends you mark while moving the
  joint slowly (30 ticks per second), 3 ticks inside each mark. The search
  pauses at the archived limit and asks before going further, never beyond the
  driver's absolute 100–520;
- **rest** pose of the lower and upper arm.

The backend enforces the limits for every slider, key and stick command. A
changed servo channel is only accepted while the arm is released. A missing or
invalid calibration file means the archived values are used.

The [finite test guide](SERVO_PROBING.md) and read-only
`python3 servo_probe.py --channel 11 --inspect` remain available for diagnostics.
Keep the physical power switch accessible: I2C failures, forced process
termination or a Pi failure can defeat software stops.

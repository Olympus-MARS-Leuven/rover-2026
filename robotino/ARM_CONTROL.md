# Browser arm and camera controls

The five joints are integrated into the same browser page and control session as
the tracks. Use `robotino/feature/arm-control` and the normal pull-request workflow.
The earlier finite test successfully moved the camera and fully pinched the
gripper according to user feedback. Full joint endpoints remain unmeasured.

## PC and Pi setup

Stop the old app with **Ctrl+C in its Pi terminal**. In **PC PowerShell**, from
the repository root, copy the current files:

```powershell
scp -r .\robotino robotino@robotino-pi.local:~/
```

Reuse your existing tunneled SSH session. If none is open, start one from
**PC PowerShell**:

```powershell
ssh -L 8765:127.0.0.1:8765 -o ExitOnForwardFailure=yes robotino@robotino-pi.local
```

In the resulting **Pi terminal**, run the tests and simulation:

```bash
cd ~/robotino
python3 -m unittest discover -s tests -v
python3 robotino_app.py
```

On the **PC browser**, open <http://127.0.0.1:8765> and refresh with **Ctrl+F5**.
Click **Connect controls**, then **Enable arm + camera**. Use sliders to preview
the behaviour. Simulation opens neither GPIO nor I2C.

## Select the real hardware explicitly

Stop simulation with Ctrl+C, then choose the mode in the **Pi terminal**:

| Command | Real hardware enabled |
| --- | --- |
| `python3 robotino_app.py` | None; tracks and servos simulated |
| `python3 robotino_app.py --servos` | Servos; real track enables held LOW |
| `python3 robotino_app.py --hardware` | Tracks; servos simulated |
| `python3 robotino_app.py --hardware --servos` | Tracks and servos |

Start physical arm checks with **`--servos`**, then refresh the browser. It should
say **TRACK MOTORS DISABLED** and **REAL SERVOS**. The Pi needs the existing
`python3-rpi.gpio` and `python3-smbus` OS packages and the user's `gpio`/`i2c`
groups. Run as `robotino`, without sudo.

Starting the app turns old servo signals off, but sends no joint positions.
Connecting and enabling arm control also send no joint positions. Each joint
starts only when its slider or key is used. Its first position is the last
commanded position in this process, initially the archive's 300 ticks. Actual
position is not measured; the first movement can be abrupt. Support the arm
and keep the tracks raised while checking each joint.

## Sliders, keys and speed

Joint sliders select a target without needing Shift. Movement ramps smoothly
toward that target. The percentage is travel within the configured range, not
degrees or measured position. The output beside each slider shows the current
commanded position; the slider represents the target.

For keyboard jogging, hold **Shift plus one joint key**. Releasing either freezes
that joint's command and keeps holding torque. Two joint keys together request
no jogging. Tracks continue to use Shift + arrows or ZQSD.

| Joint | Keys while holding Shift |
| --- | --- |
| Camera tilt | I = up, K = down |
| Lower arm | R = up, F = down |
| Upper arm | T = up, G = down |
| Wrist rotation | J = left, L = right |
| Gripper | O = open, P = close |

Key directions follow the original web app; confirm lower arm, upper arm and
wrist physically. The original app calls wrist movement lookleft/lookright.
When a range input has focus, arrows adjust it normally; click elsewhere to
drive with arrows. Focusing a slider or changing a joint slider clears held
keyboard commands.

**Movement speed** covers 25-200% of the normal rate. Normal is 100 PWM
ticks/second, four times the finite test's ramp rate. This controls the rate of
position commands, not servo torque or track duty. Actual movement depends on
the servo and load. Software ramp updates run about every 20 ms.

- **Hold position:** cancel target travel and jogging while maintaining the
  current commanded positions and holding torque.
- **Release servos:** disable arm control and remove all servo signals. A joint
  can sag after release; enabling again does not restart old target travel.
- **STOP / Esc / Space:** disconnect, stop track power and release servo signals.
  Focus loss, hiding the tab, or expiry after about 2 seconds also releases support.
  Reconnect and enable explicitly to control the arm again.

## Initial software limits and provenance

Channel assignments come from `server/webServer.py`, starting positions and
50 Hz operation from `server/RPIservo.py`, and the narrower per-channel ranges
from `server/config.txt` inside `robotino-original-2026-10-18.tar.gz`.

| Joint | Channel | Minimum ticks | Maximum ticks | Basis |
| --- | --- | --- | --- | --- |
| Camera tilt | 11 | 201 | 300 | Backup config |
| Lower arm | 12 | 300 | 430 | Backup config |
| Upper arm | 13 | 139 | 443 | Backup config |
| Wrist rotation | 14 | 300 | 500 | Backup config |
| Gripper | 15 | 300 | 330 | Tested 300-330 cycle already fully pinched |

The archived RPIservo driver permits 100-520 globally, while the archived web
server does not load `config.txt`. Therefore these narrower values are useful
initial software limits, **not confirmed mechanical endpoints**. The gripper
cap intentionally replaces the backup's 500 with 330 based on the physical test.
Limits are defined once in `arm.py`; every slider and keyboard request is
constrained by the backend. The UI cannot request beyond these limits.

Check small movements on each joint before using full slider travel. If a joint
reaches its physical stop early or keeps straining, press Hold position, move it
back slightly or release it with support, and report the joint and direction so
its software limit can be tightened. Keep the physical power switch accessible;
I2C failures, forced process termination or Pi failure can defeat software stops.

The [finite test guide](SERVO_PROBING.md) and read-only
`python3 servo_probe.py --channel 11 --inspect` remain available for diagnostics.

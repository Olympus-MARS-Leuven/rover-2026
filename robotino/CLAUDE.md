# Robotino

Small tracked Adeept RaspTank (original green Motor Shield V2, Raspberry Pi 3
Model B) used at schools and public events, supervised by the team. It drives
a ~2x2 m course with ramps and tunnels and moves light blocks (~3 cm) with
its arm. This is NOT the big ERC rover: never apply STM32, DRV8833,
four-wheel steering or the ERC power design here.

Full history and evidence: `docs/HANDOVER.md` (long; read section 1, 14 and
19 first, then only the sections you need). First hardware session:
`FIRST_RUN.md`.

## How to work with me
- I am a beginner at larger software projects and Git. Explain useful batches
  of steps, and why. Label every command PC or Pi.
- English for the interface. My PC keyboard is AZERTY (arrows and ZQSD).
- Do not ask questions already answered in docs/HANDOVER.md.
- Make code changes directly in small steps. Run the tests before each commit.

## Hard rules
- Never run anything that moves motors or servos (no --hardware, --servos,
  servo_test.py --hardware). Give me the exact command; I run it on the Pi
  with the robot supported and the power cutoff reachable. Simulation on the
  PC (`python robotino_app.py`, no flags) is fine.
- Never SSH to the Pi or deploy unless I ask.
- Do not change the track GPIO map or direction polarity in drive.py. I
  accepted it physically after two corrections. Track calibration may only add
  minimum duty and trim.
- Do not bring back the old fixed 25% duty or 0.4 s timeout. Measure instead.
- Never import or run the old Adeept webServer.py or RPIservo.py (their
  initialization moves hardware). Read the backup as text only.
- Keep the server bound to 127.0.0.1:8765 (reached through an SSH tunnel).
- Use BCM pin numbers. I2C 0x70 is the PCA9685 all-call address, not a
  multiplexer.
- Servo values are PWM ticks, not degrees. Archive limits are not measured
  endpoints; measured values come from Setup & tests and live in
  ~/.config/robotino/calibration.json on the Pi. Absolute bounds 100-520.
- The camera servo is tilt only.
- Decisions made with me (2026-10-31): PS4 controller via the PC browser
  (Gamepad API), no shoulder-button deadman for the controller; STOP and lost
  links freeze the arm and release it after 10 s; the limit search may pass
  archived limits slowly, with a pause and confirmation.

## Git
- Use feature branches named robotino/feature/<name> and pull requests.
- Run `git status --short --branch` first. Never switch branches over
  uncommitted work.
- robotino/feature/ps4-video-setup is built on robotino/feature/arm-control;
  neither is in main yet.

## Tests (PC, no hardware), run from robotino/
- python -m unittest discover -s tests -v
- node --test tests/test_keyboard.cjs tests/test_gamepad.cjs tests/test_setup_logic.cjs
- Expected on ps4-video-setup: 107 Python and 36 JS pass. arm-control: 60 and
  16; main: 25 and 10.
- Passing tests do not prove the robot is safe or reliable.

## Pi and deployment
- Pi: robotino@robotino-pi.local, Raspberry Pi OS Bookworm Lite 64-bit
  (confirmed aarch64 on 2026-10-25), Python 3.11.2. Keep code 3.11-compatible.
- Deploy with tools/deploy.ps1 (PC): git archive of the committed folder into
  ~/robotino-releases/<commit>, ~/robotino is a symlink to it. Nothing deleted.
- Until the first deploy.ps1 run, the Pi has the arm-branch code (d5b0eb2)
  copied by scp with mixed CRLF/LF line endings.
- Packages: python3-rpi.gpio, python3-smbus; rpicam-apps-lite for video.
  User needs the gpio, i2c and video groups.
- Pushing to GitHub deploys nothing. Never delete the Pi's folders to fix
  uncertainty.
- Run modes: robotino_app.py (all simulated), --hardware (real tracks),
  --servos (real servos), both flags (everything real); --no-camera.

## Priorities (update this list after each session)
1. User fixes the batteries, deploys and runs FIRST_RUN.md; get the report.
2. Record the report's physical results in docs/HANDOVER.md (validation ledger).
3. Fix whatever the report shows (channels, directions, limits, video, power).
4. Event workflow: network, startup/shutdown routine, operator checklist.
5. All-day power: use the health logs (~/.config/robotino/logs) to decide.

# Robotino

Small tracked Adeept RaspTank (original green Motor Shield V2, Raspberry Pi 3
Model B) used at schools and public events, supervised by the team. It drives
a ~2x2 m course with ramps and tunnels and moves light blocks (~3 cm) with
its arm. This is NOT the big ERC rover: never apply STM32, DRV8833,
four-wheel steering or the ERC power design here.

Full history and evidence: `docs/HANDOVER.md` (long; read section 1 and 14
first, then only the sections you need).

## How to work with me
- I am a beginner at larger software projects and Git. Explain useful batches
  of steps, and why. Label every command PC or Pi.
- English for the interface. My PC keyboard is AZERTY (arrows and ZQSD).
- Do not ask questions already answered in docs/HANDOVER.md.
- Make code changes directly in small steps. Run the tests before each commit.

## Hard rules
- Never run anything that moves motors or servos (no --hardware, --servos,
  servo_test.py --hardware). Give me the exact command; I run it on the Pi
  with the robot supported and the power cutoff reachable.
- Never SSH to the Pi or deploy unless I ask.
- Do not change the track GPIO map or direction polarity in drive.py. I
  accepted it physically after two corrections.
- Do not bring back the old fixed 25% duty or 0.4 s timeout. Measure instead.
- Never import or run the old Adeept webServer.py or RPIservo.py (their
  initialization moves hardware). Read the backup as text only.
- Keep the server bound to 127.0.0.1:8765 (reached through an SSH tunnel).
- Use BCM pin numbers. I2C 0x70 is the PCA9685 all-call address, not a
  multiplexer.
- Servo values are PWM ticks, not degrees. Limits from the old archive are not
  measured endpoints. The gripper maximum 330 is deliberate.
- The camera servo is tilt only. Video streaming does not exist yet.
- Arm code exists only on branch robotino/feature/arm-control, not in main.
  Check the branch before editing.

## Git
- Use feature branches named robotino/feature/<name> and pull requests.
- Run `git status --short --branch` first. Never switch branches over
  uncommitted work.

## Tests (PC, no hardware), run from robotino/
- python -m unittest discover -s tests -v
- node --test tests/test_keyboard.cjs
- Expected: arm branch 60 Python and 16 JS pass; main 25 and 10.
- Passing tests do not prove the robot is safe or reliable.

## Pi and deployment
- Pi: robotino@robotino-pi.local, Raspberry Pi OS Bookworm Lite 64-bit
  (intended target; confirm with uname -m), Python 3.11.2.
- Packages: python3-rpi.gpio, python3-smbus. User needs the gpio and i2c groups.
- Pushing to GitHub deploys nothing. scp copies files but does not remove
  deleted ones. Never delete the Pi's folder to fix uncertainty.
- Run modes: robotino_app.py (all simulated), --hardware (real tracks),
  --servos (real servos), both flags (everything real).

## Priorities (update this list after each session)
1. Confirm what is installed and running on the Pi.
2. Physically validate lower arm, upper arm and wrist (channels 12, 13, 14).
3. Review first-move and release behaviour (arm can sag, position unsensed).
4. Measure real stopping time on link loss (2 s timeout).
5. Choose a clean deployment method.
6. PS4 input, then optional video, then all-day power.
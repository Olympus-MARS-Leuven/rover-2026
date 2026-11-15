# Robotino quick start

Drive Robotino with a PS4 controller in about five minutes. This guide covers
only the normal run. The robot is already set up and calibrated; leave the
**Setup & tests** tab alone unless the team asks you to use it.

## What you need

- Robotino with **charged batteries**
- A Windows PC or Mac on the **same Wi-Fi as the robot** (ask the team which network)
- This repository on the computer (the `rover-2026` folder)
- The PS4 controller and its **USB cable**
- The robot's password (ask the team)

## 1. Switch on the robot

1. Put the robot on the floor of the course, or on a stand if this is your first time.
2. Switch it on with the power switch.
3. **Wait one minute** while the Raspberry Pi starts.

## 2. Start the control page

1. On Windows, open the `rover-2026\robotino` folder in File Explorer and
   double-click **`Start Robotino.cmd`**.
   On Mac, open the `robotino` folder in Finder and double-click
   **`Start Robotino.command`**. If macOS asks you to confirm opening it, choose
   **Open**.
2. A terminal window opens. Type the robot's password and press Enter.
   Nothing appears while you type; that is normal.
3. Wait a few seconds: the **control page opens in your browser** by itself.

**This starts real tracks and servos on the Pi. Keep the terminal window open**
while you drive; closing it stops the robot app.

The first SSH connection may ask whether to trust the robot's identity. Check
with the team if you are unsure; otherwise type `yes` if asked.

## 3. Check the page

At the top of the page you should see:

| You see | Meaning |
| --- | --- |
| **MOTORS ENABLED** and **REAL SERVOS** | The robot is ready to move |
| **Supply OK** (green) | Batteries are fine |
| **UNDER-VOLTAGE** (red) | Batteries are too weak: stop and charge them |

## 4. Connect the controller

1. Plug the PS4 controller into the computer with the USB cable.
2. Press any button on it. The controller box on the page shows **Connected:**
   followed by the controller's name.
3. Press **Options** on the controller (or click **Connect controls**).
   The top of the page says **Connected**.

## 5. Drive

The page starts in **DRIVE** mode.

| Controller | What it does |
| --- | --- |
| Left stick | Drive and turn. Let go to stop |
| D-pad ← / → | Slower / faster |
| Hold L1 or R1 | Fine, slow movement |
| **○ Circle** | **STOP** (press Options to connect again) |

Start slowly: press ← on the D-pad a few times before your first drive.

## 6. Use the arm

Press **△ Triangle** to switch to **ARM** mode (the page shows ARM in yellow).
The tracks do not move in ARM mode. Press △ again to drive.

| Controller | What it does |
| --- | --- |
| Left stick ↑ / ↓ | Lower arm up / down |
| Right stick ↑ / ↓ | Upper arm up / down |
| Right stick ← / → | Turn the wrist |
| R2 / L2 | Close / open the gripper |
| D-pad ↑ / ↓ | Tilt the camera |
| □ Square | Fold the arm to its rest position |

Pick up light blocks (about 3 cm cardboard). Heavy objects are too much for
the small servos, and the lower arm struggles most when stretched far out.

**Camera:** click **Start video** on the page to see what the robot sees.

## 7. Stop and switch off

1. Press **○** on the controller.
2. Click in the terminal window and press **Ctrl+C**. Then press Enter to close it.
3. On Windows, double-click **`Shut down Robotino.cmd`**. On Mac, double-click
   **`Shut down Robotino.command`**. Type the password (sometimes twice). This
   switches the Raspberry Pi off safely.
4. Wait **20 seconds**, then switch the robot off with the power switch.

Never switch the power off while the Pi is still running, unless it is an
emergency.

## In an emergency

Press **○** on the controller or the red **STOP** on the page. If the robot
still moves, **switch the power off**. STOP stops the tracks at once; the arm
keeps holding for 10 seconds, then goes limp.

## If something goes wrong

| Problem | What to do |
| --- | --- |
| Terminal: "Could not resolve hostname" | The robot is off, still starting (wait one more minute), or the computer is on another Wi-Fi |
| Terminal: "Permission denied" | Wrong password; try again |
| Terminal: "Address already in use" | Another Robotino window is open: close it, then try again |
| The page does not open | Open <http://127.0.0.1:8765> in the browser yourself |
| Page says "Disconnected" | Press Options on the controller or click **Connect controls** |
| Controller not shown | Press any button on it; try another USB port |
| Robot does not move | Check the page says **Connected** and **DRIVE**; check the speed is not 0% |
| Arm does not move | Press △ (ARM mode) |
| Red **UNDER-VOLTAGE** | Charge the batteries |
| Anything else | Press STOP, switch off, and tell the team what you saw |

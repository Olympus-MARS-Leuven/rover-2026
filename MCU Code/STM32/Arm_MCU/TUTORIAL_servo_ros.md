# Arm MCU: control the servos from ROS 2

Tutorial for Sona, Olympus MARS electronics team. Written 17 November 2026 for the NUCLEO-F446RE.

## 0. What you will build

At the end of this tutorial:

1. You type a command on the Raspberry Pi (ROS 2).
2. The command travels over the USB cable to the STM32 board (micro-ROS).
3. The four SG90 servos move to the angles you asked for.

The chain is:

```text
Pi (ROS 2 Jazzy)  --USB serial-->  micro-ROS Agent on the Pi  -->  STM32 (Arm_MCU firmware)  --PWM-->  4 servos
```

The board already knows how to talk to the Pi. The team tested it with a "heartbeat": the board sends a number that goes up by 1 every second. Your project, `Arm_MCU`, is a copy of that working project (`agent_test`). You will add three things to it:

- the TIM8 timer that makes the servo signals;
- a small servo driver (`servo.c` and `servo.h`);
- a ROS 2 subscriber that receives the angles.

**The agreed interface (do not change it without asking Adrien):**

| Item | Value |
|---|---|
| Node name | `arm_mcu` |
| Heartbeat topic | `/arm/heartbeat`, type `std_msgs/msg/Int32`, once per second |
| Command topic | `/arm/servo_cmd`, type `std_msgs/msg/Int16MultiArray` |
| Command values | 4 numbers, servo 1 to servo 4, angle in degrees, 0 to 180 |
| ROS domain | 42 (already set in the code) |
| Serial link | USART2, 115200 baud, through the board's USB cable |
| Safety rule | servos stay at their last position (they do not go limp) |

Read each step completely before you do it. If a result is not what the step says, stop and look at section 9 (problems), then ask Adrien.

---

## 1. Install the software (on your Windows laptop)

You need an ST account to download ST software. Create one at https://www.st.com (top right, "Login" then "Create account"). Use the same account inside CubeMX later.

Install, in this order:

| Software | Where to get it | Notes |
|---|---|---|
| **STM32CubeIDE 2.2.0** | https://www.st.com/en/development-tools/stm32cubeide.html | Take the normal (Eclipse) version, not the VS Code extension. Used to write, build and flash the code. |
| **STM32CubeMX** (6.18.1 or newer) | https://www.st.com/en/development-tools/stm32cubemx.html | Since CubeIDE 2.x, CubeMX is a separate program. Used to choose what each pin and timer does. |
| **Docker Desktop** | https://www.docker.com/products/docker-desktop/ | Builds the micro-ROS library automatically during the first build. Accept the WSL 2 option during installation. Restart the laptop if asked. |
| **GitHub Desktop** | https://desktop.github.com/ | To get the code and send your changes. Sign in with your GitHub account. |

Then:

1. Send your GitHub username to Adrien so he adds you to the `Olympus-MARS-Leuven` organisation, if he has not already done so.
2. Open Docker Desktop once and wait until it says "Engine running". **Docker Desktop must be running every time you build this project.**
3. Ask Adrien for the **Pi login**: its hostname or IP address, the user name and the password. You will connect to it with SSH.

---

## 2. Get the project from GitHub

1. Open GitHub Desktop. Click **File → Clone repository → GitHub.com**. Choose `Olympus-MARS-Leuven/rover-2026`. As local path, use `C:\Users\<your name>\Documents\GitHub\rover-2026`. Click **Clone**.
2. Check that the folder `rover-2026\MCU Code\STM32\Arm_MCU` exists. If it does not, Adrien has not pushed it yet: ask him.
3. Create your own branch so your work does not touch `main`. In GitHub Desktop: **Branch → New branch**. Name: `arm/feature/servo-ros-control`. Base it on `main`. Click **Create branch**.
   - The team rule for branch names is `[area]/[bug or feature]/[name]`.

Never work directly on `main`. It is protected: changes only go in through a pull request (section 8).

---

## 3. Open the project in STM32CubeIDE

1. Start STM32CubeIDE. It asks for a **workspace** folder. Choose a folder **outside** the GitHub folder, for example `C:\Users\<your name>\STM32CubeIDE\workspace_olympus`.
   - Why: the workspace contains a `.metadata` folder full of temporary files. If it is inside the repository, git tries to commit it and fails.
2. Close the "Information Center" tab if it opens.
3. Import the project: **File → STM32 Project Create/Import**. Under "Import STM32 Project", choose **STM32CubeMX/STM32CubeIDE Project** and click **Next**.
4. Browse to `...\rover-2026\MCU Code\STM32\Arm_MCU`. Click **Finish**.
   - If that menu does not work, use **File → Import → General → Existing Projects into Workspace**. Select the same folder. Make sure **"Copy projects into workspace" is NOT ticked**. Click **Finish**.
5. You should now see `Arm_MCU` in the Project Explorer on the left.

### First build (before changing anything)

This checks that your installation works before you change anything.

1. Start Docker Desktop and wait for "Engine running".
2. In CubeIDE, click on `Arm_MCU`, then **Project → Build Project** (or the hammer icon).
3. The first build downloads the micro-ROS builder and builds the micro-ROS library. **This can take 5 to 15 minutes.** You see Docker messages in the **Console** tab at the bottom.
4. Success looks like this at the end of the Console: `Build Finished. 0 errors`.

If it fails, see section 9 before going further.

---

## 4. Configure the servo timer in STM32CubeMX

### 4.1 What we configure and why

Each SG90 servo wants one pulse every 20 ms (50 Hz). The pulse width gives the angle:

| Pulse width | Angle we use |
|---|---|
| 1000 µs (1.0 ms) | 0° |
| 1500 µs (1.5 ms) | 90° (centre) |
| 2000 µs (2.0 ms) | 180° |

The timer clock on this board is 84 MHz. We divide it by 84 (prescaler = 83, because the timer adds 1). Each timer "tick" is then exactly 1 µs. With a period of 20000 ticks (counter period = 19999), we get 20 ms. That is why the pulse value in the code is directly the pulse width in microseconds: 1500 means 1.5 ms.

The servos are already wired to these pins (see `Motor + Servo Circuit` PDF and `PINMAP.md`):

| Servo | STM32 pin | Timer channel |
|---|---|---|
| SG90 #1 | PC6 | TIM8_CH1 |
| SG90 #2 | PC7 | TIM8_CH2 |
| SG90 #3 | PC8 | TIM8_CH3 |
| SG90 #4 | PC9 | TIM8_CH4 |

### 4.2 Open the project in CubeMX

1. **Close CubeIDE** (or at least do not build while CubeMX is open).
2. Start STM32CubeMX. **File → Load Project**. Open `...\rover-2026\MCU Code\STM32\Arm_MCU\Arm_MCU.ioc`.
3. If CubeMX asks to **migrate** the project to a newer version, click **Migrate**, and tell Adrien which CubeMX version you have.
4. If CubeMX says the firmware package **STM32Cube FW_F4 V1.28.3** is missing, let it download it. You may have to log in first: **Help → myST → Connection** with your ST account.

### 4.3 Turn on TIM8

1. Go to the **Pinout & Configuration** tab.
2. In the left list, open **Timers** and click **TIM8**.
3. In the **Mode** panel (middle top):
   - **Clock Source**: `Internal Clock`
   - **Channel1**: `PWM Generation CH1`
   - **Channel2**: `PWM Generation CH2`
   - **Channel3**: `PWM Generation CH3`
   - **Channel4**: `PWM Generation CH4`
   - Leave everything else (Slave Mode, Trigger Source, Combined Channels, etc.) as it is.
4. Look at the chip picture on the right. **PC6, PC7, PC8 and PC9 must turn green** and show `TIM8_CH1` to `TIM8_CH4`.
   - If CubeMX chose another pin for a channel, click on the correct pin (for example PC6) in the chip picture and choose `TIM8_CH1` from the list.
   - **Do not touch PA5** (the green LED LD2), **PA2/PA3** (USART2, the link to the Pi) or **PC13** (blue button).

### 4.4 Timer settings

In the **Configuration** panel (middle bottom), tab **Parameter Settings**:

**Counter Settings**

| Setting | Value |
|---|---|
| Prescaler (PSC - 16 bits value) | `83` |
| Counter Mode | `Up` |
| Counter Period (AutoReload Register) | `19999` |
| Internal Clock Division (CKD) | `No Division` |
| Repetition Counter (RCR) | `0` |
| auto-reload preload | `Enable` |

**Trigger Output (TRGO) Parameters** and **Break And Dead Time management**: leave the defaults.

**PWM Generation Channel 1**, then the same for **Channel 2, 3 and 4**:

| Setting | Value |
|---|---|
| Mode | `PWM mode 1` |
| Pulse (16 bits value) | `1500` |
| Output compare preload | `Enable` |
| Fast Mode | `Disable` |
| CH Polarity | `High` |
| CH Idle State | `Reset` |

Check all four channels. In the old Motor_Test project, channel 3 had Pulse = 0 by mistake.

You do **not** need any interrupt or DMA for TIM8. Leave the **NVIC Settings** and **DMA Settings** tabs of TIM8 empty.

### 4.5 Things you must NOT change

These parts make the link to the Pi work. Do not touch them:

- **Connectivity → USART2** (Asynchronous, 115200, with DMA).
- **System Core → DMA** (USART2_RX on DMA1 Stream 5, USART2_TX on DMA1 Stream 6).
- **Middleware → FREERTOS** (the defaultTask with stack size 3000).
- **System Core → SYS → Timebase Source = TIM6**.
- The **Clock Configuration** tab. Just check that **APB2 timer clocks (MHz)** shows **84**. TIM8 is on APB2.

### 4.6 Generate the code

1. Go to the **Project Manager** tab. Check:
   - Project Name: `Arm_MCU`
   - Toolchain / IDE: `STM32CubeIDE`
2. Click **GENERATE CODE** (top right). When it says the code was generated, click **Close**. Do not click "Open Project".
3. Close CubeMX.

CubeMX has now added `MX_TIM8_Init()` and the variable `htim8` to `main.c`. It also added the pin setup in `stm32f4xx_hal_msp.c`.

**Important rule:** CubeMX rewrites `main.c` every time you click GENERATE CODE. It only keeps what is between lines like `/* USER CODE BEGIN ... */` and `/* USER CODE END ... */`. Everything you add must go between those markers, or in your own files.

---

## 5. Write the code

Open CubeIDE again. Click on `Arm_MCU` and press **F5** (refresh) so it sees the files CubeMX changed.

### 5.1 Create the servo driver header: `Core/Inc/servo.h`

In the Project Explorer, right-click `Core/Inc` → **New → Header File**. Name it `servo.h`. Replace its content with:

```c
#ifndef SERVO_H
#define SERVO_H

#include <stdint.h>

#define SERVO_COUNT   4      /* servos on TIM8 CH1..CH4 = PC6..PC9 */
#define SERVO_MIN_US  1000   /* pulse for 0 degrees   */
#define SERVO_MAX_US  2000   /* pulse for 180 degrees */

/* Start the 4 PWM outputs and put every servo at the centre (1500 us). */
void Servo_Init(void);

/* Move one servo. index = 0..3 (servo 1..4), angle in degrees 0..180.
   Values outside 0..180 are limited to 0 or 180. */
void Servo_SetAngle(uint8_t index, int32_t angle_deg);

#endif /* SERVO_H */
```

### 5.2 Create the servo driver: `Core/Src/servo.c`

Right-click `Core/Src` → **New → Source File**. Name it `servo.c`. Content:

```c
#include "servo.h"
#include "main.h"

/* htim8 is created by CubeMX in main.c */
extern TIM_HandleTypeDef htim8;

static const uint32_t servo_channel[SERVO_COUNT] = {
  TIM_CHANNEL_1,  /* servo 1, PC6 */
  TIM_CHANNEL_2,  /* servo 2, PC7 */
  TIM_CHANNEL_3,  /* servo 3, PC8 */
  TIM_CHANNEL_4   /* servo 4, PC9 */
};

void Servo_Init(void)
{
  for (uint8_t i = 0; i < SERVO_COUNT; i++)
  {
    __HAL_TIM_SET_COMPARE(&htim8, servo_channel[i], 1500);
    HAL_TIM_PWM_Start(&htim8, servo_channel[i]);
  }
}

void Servo_SetAngle(uint8_t index, int32_t angle_deg)
{
  if (index >= SERVO_COUNT) { return; }
  if (angle_deg < 0)   { angle_deg = 0; }
  if (angle_deg > 180) { angle_deg = 180; }

  /* 0 deg -> 1000 us, 180 deg -> 2000 us. One timer tick = 1 us. */
  uint32_t pulse_us = SERVO_MIN_US
                    + ((uint32_t) angle_deg * (SERVO_MAX_US - SERVO_MIN_US)) / 180U;

  __HAL_TIM_SET_COMPARE(&htim8, servo_channel[index], pulse_us);
}
```

Why a separate file: CubeMX never touches `servo.c` and `servo.h`. Files in `Core/Src` and `Core/Inc` are built automatically.

Note on TIM8: it is an "advanced" timer, which has an extra master output switch. `HAL_TIM_PWM_Start` turns it on for you, so nothing else is needed.

### 5.3 Changes in `Core/Src/main.c`

Open `Core/Src/main.c`. Make the following 4 changes. Each one goes **between** the USER CODE markers named below.

**Change A: includes.** Find `/* USER CODE BEGIN Includes */`. The list already contains `#include <std_msgs/msg/int32.h>`. Add two lines under it, so the block ends like this:

```c
#include <std_msgs/msg/int32.h>
#include <std_msgs/msg/int16_multi_array.h>
#include "servo.h"

/* USER CODE END Includes */
```

**Change B: start the servos at boot.** Find `/* USER CODE BEGIN 2 */` (just after `MX_TIM8_Init();`). Make it:

```c
  /* USER CODE BEGIN 2 */
  Servo_Init();   /* all 4 servos to centre, PWM running */
  /* USER CODE END 2 */
```

**Change C: the function that runs when a command arrives.** Find `/* USER CODE BEGIN 4 */`. It already contains the transport functions, `error_loop` and `RCCHECK`. Add this **just before** `/* USER CODE END 4 */`:

```c
/* Called by the micro-ROS executor each time a message arrives on /arm/servo_cmd.
   data[0] = servo 1 ... data[3] = servo 4, in degrees.
   If fewer than 4 numbers are sent, only those servos move. */
static void servo_cmd_callback(const void * msgin)
{
  const std_msgs__msg__Int16MultiArray * cmd =
      (const std_msgs__msg__Int16MultiArray *) msgin;

  for (size_t i = 0; i < cmd->data.size && i < SERVO_COUNT; i++)
  {
    Servo_SetAngle((uint8_t) i, cmd->data.data[i]);
  }
}
```

**Change D: the micro-ROS task.** Find the function `StartDefaultTask`. Replace **everything between** `/* USER CODE BEGIN 5 */` and `/* USER CODE END 5 */` with the code below. It keeps the parts that already work (transport, memory, waiting for the Agent, domain 42). Only the end changes: new node name, new heartbeat topic, the subscriber and the executor.

```c
  /* USER CODE BEGIN 5 */

  /* 1. Tell micro-ROS to use USART2 (USB cable to the Pi) */
  rmw_uros_set_custom_transport(true, (void *) &huart2,
      cubemx_transport_open, cubemx_transport_close,
      cubemx_transport_write, cubemx_transport_read);

  /* 2. Tell micro-ROS to use FreeRTOS memory functions */
  rcl_allocator_t freeRTOS_allocator = rcutils_get_zero_initialized_allocator();
  freeRTOS_allocator.allocate      = microros_allocate;
  freeRTOS_allocator.deallocate    = microros_deallocate;
  freeRTOS_allocator.reallocate    = microros_reallocate;
  freeRTOS_allocator.zero_allocate = microros_zero_allocate;
  if (!rcutils_set_default_allocator(&freeRTOS_allocator)) { error_loop(); }

  /* 3. LD2 ON = waiting for the Agent on the Pi */
  HAL_GPIO_WritePin(LED2_GPIO_PORT, LED2_PIN, GPIO_PIN_SET);
  while (rmw_uros_ping_agent(100, 1) != RMW_RET_OK) { osDelay(500); }
  HAL_GPIO_WritePin(LED2_GPIO_PORT, LED2_PIN, GPIO_PIN_RESET);

  /* 4. Variables */
  rcl_allocator_t allocator = rcl_get_default_allocator();
  rclc_support_t support;
  rcl_node_t node;
  rcl_publisher_t heartbeat_pub;
  std_msgs__msg__Int32 heartbeat_msg;
  rcl_subscription_t servo_sub;
  static std_msgs__msg__Int16MultiArray servo_msg;  /* incoming command   */
  static int16_t servo_buffer[8];                   /* room for 8 numbers */
  rclc_executor_t executor = rclc_executor_get_zero_initialized_executor();

  /* 5. Start micro-ROS on ROS domain 42, create the node */
  rcl_init_options_t init_options = rcl_get_zero_initialized_init_options();
  RCCHECK(rcl_init_options_init(&init_options, allocator));
  RCCHECK(rcl_init_options_set_domain_id(&init_options, 42));
  RCCHECK(rclc_support_init_with_options(&support, 0, NULL, &init_options, &allocator));
  RCCHECK(rclc_node_init_default(&node, "arm_mcu", "", &support));

  /* 6. Heartbeat publisher */
  RCCHECK(rclc_publisher_init_default(&heartbeat_pub, &node,
      ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int32), "/arm/heartbeat"));

  /* 7. Servo command subscriber.
        An array message needs memory reserved in advance on a microcontroller:
        we point it to servo_buffer (max 8 numbers). */
  servo_msg.data.data         = servo_buffer;
  servo_msg.data.capacity     = 8;
  servo_msg.data.size         = 0;
  servo_msg.layout.dim.data     = NULL;  /* we do not use the layout part */
  servo_msg.layout.dim.capacity = 0;
  servo_msg.layout.dim.size     = 0;
  servo_msg.layout.data_offset  = 0;
  RCCHECK(rclc_subscription_init_default(&servo_sub, &node,
      ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int16MultiArray), "/arm/servo_cmd"));

  /* 8. Executor: checks for incoming messages and calls servo_cmd_callback.
        1 = number of things it handles (1 subscriber). */
  RCCHECK(rclc_executor_init(&executor, &support.context, 1, &allocator));
  RCCHECK(rclc_executor_add_subscription(&executor, &servo_sub, &servo_msg,
      &servo_cmd_callback, ON_NEW_DATA));

  /* 9. Main loop: handle commands every 10 ms, send heartbeat every 1000 ms */
  heartbeat_msg.data = 0;
  uint32_t last_heartbeat = osKernelGetTickCount();   /* 1 tick = 1 ms */
  for (;;)
  {
    rclc_executor_spin_some(&executor, RCL_MS_TO_NS(10));

    if (osKernelGetTickCount() - last_heartbeat >= 1000)
    {
      last_heartbeat += 1000;
      if (rcl_publish(&heartbeat_pub, &heartbeat_msg, NULL) == RCL_RET_OK)
      {
        HAL_GPIO_TogglePin(LED2_GPIO_PORT, LED2_PIN);  /* LD2 blinks = alive */
      }
      heartbeat_msg.data++;
    }
    osDelay(10);
  }
  /* USER CODE END 5 */
```

### 5.4 What the LED means

| LD2 (green LED) | Meaning |
|---|---|
| ON, not blinking | The board is waiting for the Agent on the Pi |
| Changes state once per second | Connected, heartbeat is being sent |
| Blinks very fast | A micro-ROS step failed (`RCCHECK` → `error_loop`). See section 9 |

### 5.5 Build

1. Docker Desktop running.
2. **Project → Build Project**.
3. Expect `Build Finished. 0 errors`. Warnings are OK for now; note them.
4. In the Console, the build prints the memory use (`text`, `data`, `bss`). Write these numbers down; Adrien wants to know them. The F446RE has 512 KB flash and 128 KB RAM.

---

## 6. Hardware: be safe first

The board you use is the drive test bench: it has the 4 motors and the 4 servos. Your firmware does not drive the motors (their pins are not configured), and the DRV8833 inputs have internal pull-downs, so the motors stay off. Still:

1. **Wheels off the ground**, or unplug the motor connectors.
2. **No load on the servos**: no arm parts, horns free to turn. When the firmware starts, all servos jump to the centre (90°).
3. Check the circuit as in the PDF ("Before switching on"): fuses in place, battery switch S1 OFF while you plug things in.
4. **Never power the servos from the Nucleo.** They get 5 V from the U2 UBEC. The Nucleo is powered by USB. The grounds are already connected together, do not remove that link.
5. The PDF advises: start with one servo at a time. For the first test, you can plug in only servo 1.

---

## 7. Flash and test with ROS 2

### 7.1 Flash the board (laptop)

1. Plug the Nucleo into your **laptop** with the USB cable.
2. In CubeIDE: right-click `Arm_MCU` → **Run As → STM32 C/C++ Application**. If a window opens, click **OK**. If it asks to update the ST-LINK firmware, you can say yes.
3. Wait for `Download verified successfully` (or similar) in the Console.
4. The LED LD2 should now be **ON and steady**: the board waits for the Agent. That is normal, the Pi is not connected yet.

### 7.2 Connect to the Pi

1. Unplug the USB cable from the laptop and plug it into the **Raspberry Pi**. The Nucleo has only one USB port: it is used for flashing AND for the Pi link.
2. Turn the battery switch S1 ON so the servos have power.
3. On your laptop, open **Windows PowerShell** and connect to the Pi (use the name, user and password Adrien gave you):

   ```bash
   ssh <user>@<pi-hostname-or-ip>
   ```

### 7.3 Window 1 on the Pi: start the Agent

The Agent is the program that connects the board to ROS 2. It must run **before** the board starts talking.

```bash
source /opt/ros/jazzy/setup.bash
source ~/microros_ws/install/local_setup.bash
export ROS_DOMAIN_ID=42
ros2 run micro_ros_agent micro_ros_agent serial --dev /dev/ttyACM0 --baud 115200
```

If Adrien or Hannah created a script for this (for example `~/start_agent.sh`), you can run that instead. Leave this window open.

Then **press the black RESET button** on the Nucleo. Within a few seconds the Agent prints lines about a new session, and LD2 starts changing once per second.

### 7.4 Window 2 on the Pi: check the board is visible

Open a second PowerShell window, `ssh` to the Pi again, then:

```bash
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=42
ros2 node list
ros2 topic list
ros2 topic echo /arm/heartbeat
```

**Pass:**
- `ros2 node list` shows `/arm_mcu`;
- `ros2 topic list` shows `/arm/heartbeat` and `/arm/servo_cmd`;
- `echo` prints `data: 12`, `data: 13`, and so on, once per second.

Stop `echo` with **Ctrl+C**.

### 7.5 Move the servos

In window 2:

```bash
# All servos to the centre
ros2 topic pub --once -w 1 /arm/servo_cmd std_msgs/msg/Int16MultiArray "{data: [90, 90, 90, 90]}"

# All to one side, then the other
ros2 topic pub --once -w 1 /arm/servo_cmd std_msgs/msg/Int16MultiArray "{data: [0, 0, 0, 0]}"
ros2 topic pub --once -w 1 /arm/servo_cmd std_msgs/msg/Int16MultiArray "{data: [180, 180, 180, 180]}"

# Each servo different
ros2 topic pub --once -w 1 /arm/servo_cmd std_msgs/msg/Int16MultiArray "{data: [0, 60, 120, 180]}"

# Only servo 1 (one number = only the first servo moves)
ros2 topic pub --once -w 1 /arm/servo_cmd std_msgs/msg/Int16MultiArray "{data: [45]}"
```

`-w 1` means: wait until 1 subscriber (the board) is found, then send. Without it, the message can leave before the connection is ready, and nothing happens.

**Pass:** each servo goes to the angle you sent and stays there. The heartbeat keeps counting during all tests.

Note: with 1000 to 2000 µs, many SG90 servos turn only about 90° in total, not a full 180°. That is expected and safe. Do not change `SERVO_MIN_US` or `SERVO_MAX_US` without asking Adrien: going too far makes the servo push against its end stop, which heats and damages it.

### 7.6 A predefined movement from a small ROS 2 program

This is the first step towards "the arm does predefined movements from the laptop". On the Pi, in window 2, create the file:

```bash
nano ~/servo_sequence.py
```

Paste this, then save with **Ctrl+O**, **Enter**, and exit with **Ctrl+X**:

```python
import rclpy
from rclpy.node import Node
from std_msgs.msg import Int16MultiArray

# Each line = angles for servo 1, 2, 3, 4 (degrees). One pose per second.
POSES = [
    [90, 90, 90, 90],
    [45, 90, 135, 90],
    [135, 90, 45, 90],
    [90, 45, 90, 135],
    [90, 90, 90, 90],
]


class ServoSequence(Node):
    def __init__(self):
        super().__init__('servo_sequence')
        self.pub = self.create_publisher(Int16MultiArray, '/arm/servo_cmd', 10)
        self.index = 0
        self.timer = self.create_timer(1.0, self.step)

    def step(self):
        if self.index >= len(POSES):
            self.get_logger().info('Sequence done')
            raise SystemExit
        msg = Int16MultiArray()
        msg.data = POSES[self.index]
        self.pub.publish(msg)
        self.get_logger().info(f'Pose {self.index}: {list(msg.data)}')
        self.index += 1


def main():
    rclpy.init()
    node = ServoSequence()
    try:
        rclpy.spin(node)
    except SystemExit:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

Run it (the Agent must still be running in window 1):

```bash
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=42
python3 ~/servo_sequence.py
```

**Pass:** the servos go through the 5 poses, one per second, and end at the centre. Change the poses to make your own movement.

---

## 8. Save your work on GitHub

1. In GitHub Desktop, look at the **Changes** list. You should see only:
   - `Arm_MCU.ioc`;
   - `Core/Src/main.c`, `Core/Src/stm32f4xx_hal_msp.c`, and maybe `Core/Inc/main.h` or `Core/Src/stm32f4xx_it.c`;
   - your new `Core/Inc/servo.h` and `Core/Src/servo.c`;
   - maybe `.mxproject` and `.cproject`.

   If you see `Debug/`, `.metadata/` or `.elf` files, **do not commit them**. Right-click → **Ignore** or ask Adrien.
2. Write a summary, for example `Arm_MCU: TIM8 servos controlled from /arm/servo_cmd`, and click **Commit to arm/feature/servo-ros-control**.
3. Click **Publish branch** (the first time) or **Push origin** (the next times).
4. Open a pull request: click **Create Pull Request** (GitHub opens in your browser). Write what you did and what you tested, add **Adrien as reviewer**, click **Create pull request**.
5. Copy `servo_sequence.py` into the repository too, for example in `arm/scripts/servo_sequence.py`, so the team can reuse it.

Commit often (after each step that works), not only at the end.

---

## 9. Problems and what to do

| What you see | Most likely reason | What to do |
|---|---|---|
| Build error mentioning `docker` in the pre-build step | Docker Desktop is not running, or still starting | Start Docker Desktop, wait for "Engine running", build again. |
| Build error `cannot find -lmicroros` or `rcl/rcl.h: No such file` | The micro-ROS library was not built | Check the Console for the Docker part of the build. Copy the first red error to Adrien. |
| Build error `htim8 undeclared` or `MX_TIM8_Init` missing | Code not generated, or CubeIDE did not refresh | Do section 4.6 again, then F5 in CubeIDE. |
| After GENERATE CODE, your code is gone | It was written outside a USER CODE block | Write it again between the markers. Commit often so you can recover it. |
| LD2 stays ON forever | Board cannot reach the Agent | Agent running? Cable on the Pi (not the laptop)? Press RESET after starting the Agent. Only one program may use `/dev/ttyACM0`. |
| LD2 blinks very fast | A micro-ROS step failed (usually memory or Agent) | Press RESET with the Agent running. If it repeats, tell Adrien which step you changed last. |
| `ros2 node list` is empty | Wrong domain, or no Agent | `export ROS_DOMAIN_ID=42` in every window. Check window 1 shows a session. |
| `/dev/ttyACM0` not found | Different port name | On the Pi: `ls /dev/ttyACM*` and use the name shown. |
| Heartbeat works, servos do not move | Servo power or wiring | S1 ON? 5 V on the servo red wire? Signal (orange) on PC6–PC9? Common ground? |
| Servos shake or the Nucleo resets when they move | Power problem | Servos must be on the UBEC, never on the Nucleo 5 V. Try one servo only. |
| Only some servos move | Fewer than 4 numbers sent, or a channel not enabled in CubeMX | Send 4 numbers. Check TIM8 CH1–CH4 in CubeMX (section 4.3). |
| `ros2 topic pub` returns but nothing happens | Message sent before connection | Use `-w 1` as in section 7.5. |

---

## 10. Checklist: send this to Adrien when you are done

- [ ] First build of the untouched `Arm_MCU` works (section 3).
- [ ] TIM8 configured in CubeMX, code generated (section 4).
- [ ] Code builds. Memory use: text = ____ , data = ____ , bss = ____ .
- [ ] `/arm_mcu`, `/arm/heartbeat` and `/arm/servo_cmd` visible on the Pi.
- [ ] Each servo moves to 0, 90 and 180 on command and holds its position.
- [ ] `servo_sequence.py` runs the 5 poses.
- [ ] Branch pushed and pull request opened, Adrien as reviewer.
- [ ] Anything strange you noticed (warnings, jitter, a servo that does not reach its angle).

## 11. Questions to think about (for the team meeting)

- Why must the Agent start before the board, and what happens if the Pi reboots while the board is running?
- Why does an array message need memory reserved in advance on a microcontroller, but not on the Pi?
- If the arm gets 7 servos later, what must change in CubeMX and in the code? Is one timer enough?
- Is holding the last position always the safest behaviour for an arm? When would it not be?

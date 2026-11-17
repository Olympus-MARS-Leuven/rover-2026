# Drive MCU: drive Robotone from ROS 2

Tutorial for Adrien, Matthias and Tanya, Olympus MARS electronics team. Written 17 November 2026 for the NUCLEO-F446RE in Robotone.

## 0. What you will build

At the end of this tutorial, the same ROS 2 command drives the **simulation** and the **real Robotone**:

```text
                         /cmd_vel (forward speed, turning speed)
 keyboard / script  ───────────────────────────┬──────────────────────────► simulation (Tanya)
                                               │
                                               ▼
                                 cmd_vel_to_motors.py (on the Pi)
                                               │  /drive/motor_cmd  (4 motor percentages)
                                               ▼
                         micro-ROS Agent (Pi) ── USB ──► STM32 Drive_MCU ── PWM ──► 2× DRV8833 ──► 4 motors
```

| Part | Who | What |
|---|---|---|
| **A. Firmware** | Adrien and Matthias | `Drive_MCU`: TIM3 and TIM4 PWM, a motor driver with a smooth start, a pause before reversing and an automatic stop, and a ROS 2 subscriber |
| **B. ROS side** | Tanya | Bridge from velocity commands to motor percentages, the predefined movement, and the link with the simulation |
| **C. Together** | All three | Find out which motor is which wheel, measure the robot, keyboard driving, and the same movement in simulation and on the robot |

Part A and part B can start at the same time. Tanya can test her scripts without the robot (section 8.3).

**The agreed interface (do not change it without telling the others):**

| Item | Value |
|---|---|
| Node name on the STM32 | `drive_mcu` |
| Heartbeat | `/drive/heartbeat`, `std_msgs/msg/Int32`, once per second |
| Motor command | `/drive/motor_cmd`, `std_msgs/msg/Int16MultiArray` |
| Motor values | 4 numbers, M1 to M4, from −100 to 100 % (the sign is the direction) |
| Missing values | if fewer than 4 numbers arrive, the missing motors get 0 |
| Safety | no command for 0.5 s → all motors stop |
| Velocity command (ROS side) | `geometry_msgs/msg/Twist` on `/cmd_vel` by default. It can be changed to the simulation's topic and type |
| ROS domain | 42 |
| Serial link | USART2, 115200 baud, through the board's USB cable |

The project `Drive_MCU` is a copy of the working heartbeat project (`agent_test`). It already connects to the Pi; we add the motors to it.

Read each step completely before doing it. If a result is not what the step says, stop and look at section 12 (problems).

---

## 1. What you need

### On the Windows laptops (Adrien, Matthias)

| Software | Notes |
|---|---|
| STM32CubeIDE 2.2.0 (Eclipse version) | Build and flash |
| STM32CubeMX 6.18.1 or newer | Pins and timers. Separate program since CubeIDE 2.x |
| GitHub Desktop | Branches, commits, pull requests |

You do **not** need Docker: the micro-ROS library `libmicroros.a` is already in the repository.

### On the Raspberry Pi 4 (already done for the heartbeat)

- Ubuntu 24.04, ROS 2 Jazzy, the micro-ROS Agent in `~/microros_ws`.
- **New:** the keyboard driving tool. Install it once:

  ```bash
  sudo apt update
  sudo apt install ros-jazzy-teleop-twist-keyboard
  ```

### On Tanya's computer

- Her ROS 2 Jazzy simulation of Robotone (Gazebo with ros2_control).
- Python 3 with ROS 2 (already there with the simulation).
- An SSH client to reach the Pi (PowerShell on Windows, or the terminal).

### Accounts and access

- GitHub: everyone in the `Olympus-MARS-Leuven` organisation.
- Pi: hostname or IP, user name and password (Adrien has them).

---

## 2. Branch

In GitHub Desktop:

1. Switch to `main` and click **Fetch origin**, then **Pull origin**. `main` must contain `MCU Code/STM32/Drive_MCU` and `drive/scripts/`.
2. **Branch → New branch** → `drive/feature/motor-ros-control`, based on `main`.

Everyone works on this branch. Commit after each step that works. Pull before you start working, and tell the others when you push.

---

# PART A: Firmware (Adrien and Matthias)

## 3. Import and first build

1. Start STM32CubeIDE with a workspace **outside** the GitHub folder (for example `C:\Users\<you>\STM32CubeIDE\workspace_olympus`).
2. **File → STM32 Project Create/Import → STM32CubeMX/STM32CubeIDE Project → Next**. Choose `...\rover-2026\MCU Code\STM32\Drive_MCU`. Click **Finish**.
3. Click on `Drive_MCU`, then **Project → Build Project**.
4. Expected: `Build Finished. 0 errors`. Nothing is changed yet; this only checks that the copy builds.

## 4. Configure TIM3 and TIM4 in STM32CubeMX

### 4.1 What and why

Each motor has two inputs on its DRV8833 driver:

| IN1 | IN2 | Motor |
|---|---|---|
| PWM | 0 | turns forward, speed = duty cycle |
| 0 | PWM | turns backward |
| 0 | 0 | stops (coasts) |

So 4 motors need 8 PWM signals. TIM3 and TIM4 each give 4.

| Motor | Driver / outputs | IN1 pin / channel | IN2 pin / channel |
|---|---|---|---|
| M1 | DRV8833 #1 OUT1/OUT2 | PA6 / TIM3_CH1 | PA7 / TIM3_CH2 |
| M2 | DRV8833 #1 OUT3/OUT4 | PB0 / TIM3_CH3 | PB1 / TIM3_CH4 |
| M3 | DRV8833 #2 OUT1/OUT2 | PB6 / TIM4_CH1 | PB7 / TIM4_CH2 |
| M4 | DRV8833 #2 OUT3/OUT4 | PB8 / TIM4_CH3 | PB9 / TIM4_CH4 |

PWM frequency: 84 MHz timer clock / (83 + 1) = 1 MHz, then / (499 + 1) = **2 kHz**. On the bench, 20 kHz made the motors behave erratically, so we keep 2 kHz. The compare value goes from 0 (0 %) to 500 (100 %).

### 4.2 Open the project

1. Close CubeIDE (or do not build while CubeMX is open).
2. STM32CubeMX → **File → Load Project** → `...\Drive_MCU\Drive_MCU.ioc`.
3. If it asks to migrate, click **Migrate** and note the version.

### 4.3 Choose the pins first (most reliable)

In **Pinout & Configuration**, on the chip picture, **left-click each pin and choose the function** from the list:

| Click on | Choose |
|---|---|
| PA6 | `TIM3_CH1` |
| PA7 | `TIM3_CH2` |
| PB0 | `TIM3_CH3` |
| PB1 | `TIM3_CH4` |
| PB6 | `TIM4_CH1` |
| PB7 | `TIM4_CH2` |
| PB8 | `TIM4_CH3` |
| PB9 | `TIM4_CH4` |

Why pins first: TIM3_CH1 can also come out on PB4 or PC6, and PC6 to PC9 are the servo pins. If you only enable the channels, CubeMX may choose the wrong pin.

The pins stay yellow or orange until the timer mode is set in the next step. **Do not touch** PA2/PA3 (USART2, the Pi link), PA5 (LED LD2), PC13 (button), PA13/PA14/PB3 (debug).

### 4.4 TIM3

Left list: **Timers → TIM3**.

**Mode** panel:

| Setting | Value |
|---|---|
| Clock Source | `Internal Clock` |
| Channel1 | `PWM Generation CH1` |
| Channel2 | `PWM Generation CH2` |
| Channel3 | `PWM Generation CH3` |
| Channel4 | `PWM Generation CH4` |

The 4 pins must now be green. Check on the chip picture: PA6, PA7, PB0, PB1.

**Configuration → Parameter Settings**:

| Counter setting | Value |
|---|---|
| Prescaler | `83` |
| Counter Mode | `Up` |
| Counter Period | `499` |
| Internal Clock Division | `No Division` |
| auto-reload preload | `Enable` |

For **PWM Generation Channel 1, 2, 3 and 4** (check all four):

| Setting | Value |
|---|---|
| Mode | `PWM mode 1` |
| Pulse | `0` |
| Output compare preload | `Enable` |
| Fast Mode | `Disable` |
| CH Polarity | `High` |

Leave Trigger Output at the defaults. No NVIC interrupt and no DMA are needed.

### 4.5 TIM4

Do exactly the same for **Timers → TIM4**, with the same values. Check that PB6, PB7, PB8 and PB9 are green.

### 4.6 Do not change

- USART2, DMA (Stream 5 and 6), FREERTOS, SYS (Timebase = TIM6), NVIC.
- **Clock Configuration**: just check **APB1 timer clocks = 84 MHz**. TIM3 and TIM4 are on APB1.

### 4.7 Generate

**Project Manager**: name `Drive_MCU`, toolchain `STM32CubeIDE`. Click **GENERATE CODE** → **Close**. Close CubeMX.

CubeMX added `MX_TIM3_Init()`, `MX_TIM4_Init()`, `htim3` and `htim4` in `main.c`, and the pin setup in `stm32f4xx_hal_msp.c`. It only keeps your code between `/* USER CODE BEGIN ... */` and `/* USER CODE END ... */`.

## 5. Write the code

Open CubeIDE, click on `Drive_MCU`, press **F5**.

### 5.1 `Core/Inc/motor.h` (new file)

Right-click `Core/Inc` → **New → Header File** → `motor.h`:

```c
#ifndef MOTOR_H
#define MOTOR_H

#include <stdint.h>

#define MOTOR_COUNT             4     /* M1..M4 on the two DRV8833 drivers        */
#define MOTOR_PWM_MAX           500   /* TIM3/TIM4 period 499 + 1 = 100 % duty     */
#define MOTOR_MAX_PERCENT       100   /* commands are limited to -100..100         */
#define MOTOR_RAMP_PCT_PER_S    500   /* speed change limit: 0 -> 100 % in 0.2 s   */
#define MOTOR_REVERSE_PAUSE_MS  150   /* full stop before changing direction       */
#define MOTOR_CMD_TIMEOUT_MS    500   /* no command for this long -> all motors stop */

/* Start the 8 PWM outputs with every motor stopped. */
void    Motor_Init(void);

/* Ask motor index 0..3 (M1..M4) for a speed in percent, -100..100.
   The sign is the direction. The motor gets there smoothly in Motor_Update(). */
void    Motor_SetTarget(uint8_t index, int32_t percent);

/* Ask all motors to stop (they ramp down in about 0.2 s). */
void    Motor_StopAll(void);

/* Call regularly (every ~10 ms) with the time since the last call. */
void    Motor_Update(uint32_t dt_ms);

/* Speed really applied now, -100..100 (for debugging). */
int16_t Motor_GetApplied(uint8_t index);

#endif /* MOTOR_H */
```

### 5.2 `Core/Src/motor.c` (new file)

Right-click `Core/Src` → **New → Source File** → `motor.c`:

```c
#include "motor.h"
#include "main.h"

/* htim3 and htim4 are created by CubeMX in main.c */
extern TIM_HandleTypeDef htim3;
extern TIM_HandleTypeDef htim4;

typedef struct
{
  TIM_HandleTypeDef *htim;
  uint32_t ch_in1;   /* DRV8833 IN1 (PWM here = forward) */
  uint32_t ch_in2;   /* DRV8833 IN2 (PWM here = reverse) */
} motor_hw_t;

static const motor_hw_t motor_hw[MOTOR_COUNT] =
{
  { &htim3, TIM_CHANNEL_1, TIM_CHANNEL_2 },  /* M1: PA6 / PA7, DRV8833 #1 OUT1/OUT2 */
  { &htim3, TIM_CHANNEL_3, TIM_CHANNEL_4 },  /* M2: PB0 / PB1, DRV8833 #1 OUT3/OUT4 */
  { &htim4, TIM_CHANNEL_1, TIM_CHANNEL_2 },  /* M3: PB6 / PB7, DRV8833 #2 OUT1/OUT2 */
  { &htim4, TIM_CHANNEL_3, TIM_CHANNEL_4 },  /* M4: PB8 / PB9, DRV8833 #2 OUT3/OUT4 */
};

/* +1 = normal, -1 = this motor is mounted the other way round.
   Fill this in with the motor identification test (tutorial section 9). */
static const int8_t motor_dir[MOTOR_COUNT] = { 1, 1, 1, 1 };

static int16_t  target[MOTOR_COUNT];         /* what ROS asked for, -100..100 */
static int16_t  applied[MOTOR_COUNT];        /* what the motor gets now       */
static uint32_t pause_left_ms[MOTOR_COUNT];  /* stop time left before reversing */

/* Write a speed (-100..100) to the two inputs of one DRV8833 channel. */
static void write_pwm(uint8_t i, int16_t percent)
{
  uint32_t magnitude = (uint32_t) (percent < 0 ? -percent : percent);
  uint32_t duty = magnitude * MOTOR_PWM_MAX / 100U;

  if (percent > 0)
  {
    __HAL_TIM_SET_COMPARE(motor_hw[i].htim, motor_hw[i].ch_in2, 0);
    __HAL_TIM_SET_COMPARE(motor_hw[i].htim, motor_hw[i].ch_in1, duty);
  }
  else if (percent < 0)
  {
    __HAL_TIM_SET_COMPARE(motor_hw[i].htim, motor_hw[i].ch_in1, 0);
    __HAL_TIM_SET_COMPARE(motor_hw[i].htim, motor_hw[i].ch_in2, duty);
  }
  else
  {
    __HAL_TIM_SET_COMPARE(motor_hw[i].htim, motor_hw[i].ch_in1, 0);
    __HAL_TIM_SET_COMPARE(motor_hw[i].htim, motor_hw[i].ch_in2, 0);
  }
}

void Motor_Init(void)
{
  for (uint8_t i = 0; i < MOTOR_COUNT; i++)
  {
    target[i] = 0;
    applied[i] = 0;
    pause_left_ms[i] = 0;
    write_pwm(i, 0);
    HAL_TIM_PWM_Start(motor_hw[i].htim, motor_hw[i].ch_in1);
    HAL_TIM_PWM_Start(motor_hw[i].htim, motor_hw[i].ch_in2);
  }
}

void Motor_SetTarget(uint8_t index, int32_t percent)
{
  if (index >= MOTOR_COUNT) { return; }
  if (percent >  MOTOR_MAX_PERCENT) { percent =  MOTOR_MAX_PERCENT; }
  if (percent < -MOTOR_MAX_PERCENT) { percent = -MOTOR_MAX_PERCENT; }
  target[index] = (int16_t) (percent * motor_dir[index]);
}

void Motor_StopAll(void)
{
  for (uint8_t i = 0; i < MOTOR_COUNT; i++) { target[i] = 0; }
}

void Motor_Update(uint32_t dt_ms)
{
  int32_t step = (int32_t) ((MOTOR_RAMP_PCT_PER_S * dt_ms) / 1000U);
  if (step < 1) { step = 1; }

  for (uint8_t i = 0; i < MOTOR_COUNT; i++)
  {
    /* 1. Still in the pause before a direction change: keep the motor stopped. */
    if (pause_left_ms[i] > 0)
    {
      pause_left_ms[i] = (pause_left_ms[i] > dt_ms) ? (pause_left_ms[i] - dt_ms) : 0;
      continue;
    }

    int32_t now  = applied[i];
    int32_t goal = target[i];

    /* 2. Direction change asked: first go down to 0. */
    if ((now > 0 && goal < 0) || (now < 0 && goal > 0)) { goal = 0; }

    /* 3. Move towards the goal by at most 'step' percent. */
    int32_t next = now;
    if (goal > now)      { next = (goal - now > step) ? (now + step) : goal; }
    else if (goal < now) { next = (now - goal > step) ? (now - step) : goal; }

    /* 4. We just reached 0 because of a direction change: start the pause. */
    if (now != 0 && next == 0 && target[i] != 0) { pause_left_ms[i] = MOTOR_REVERSE_PAUSE_MS; }

    applied[i] = (int16_t) next;
    write_pwm(i, (int16_t) next);
  }
}

int16_t Motor_GetApplied(uint8_t index)
{
  return (index < MOTOR_COUNT) ? applied[index] : 0;
}
```

**What it does, in simple words.** `Motor_SetTarget` only stores what ROS asks for. `Motor_Update` runs every ~10 ms and moves each motor towards its target:

- **Smooth start:** at most 5 % per 10 ms, so 0 to 100 % takes 0.2 s. This protects the gearboxes and avoids current spikes on the battery.
- **Direction change:** the motor first goes down to 0, waits 150 ms, then starts in the other direction. Reversing at full speed is hard on the gearbox and the DRV8833.
- **`motor_dir`:** fixes a motor that turns the wrong way, in software and not with a soldering iron (section 9).

This logic was tested on a computer with a fake timer: 0 to 100 % in 200 ms, reverse with a 160 ms pause, stop from any speed. It was not yet tested on the board.

### 5.3 Changes in `Core/Src/main.c`

Four changes, each **between** the USER CODE markers named below.

**Change A: includes.** In `/* USER CODE BEGIN Includes */`, under `#include <std_msgs/msg/int32.h>`, add:

```c
#include <std_msgs/msg/int16_multi_array.h>
#include "motor.h"
```

**Change B: motors stopped and PWM running at boot.** In `/* USER CODE BEGIN 2 */` (after `MX_TIM3_Init()` and `MX_TIM4_Init()`):

```c
  /* USER CODE BEGIN 2 */
  Motor_Init();   /* 8 PWM outputs running, all motors stopped */
  /* USER CODE END 2 */
```

**Change C: the function that runs when a command arrives.** Just **before** `/* USER CODE END 4 */` (after `error_loop` and `RCCHECK`):

```c
/* Time (ms) of the last /drive/motor_cmd, for the 0.5 s safety stop. */
static volatile uint32_t last_motor_cmd_tick = 0;

/* Called by the micro-ROS executor for each /drive/motor_cmd message.
   data[0] = M1 ... data[3] = M4, in percent -100..100.
   Missing values mean 0 (stop), for safety. */
static void motor_cmd_callback(const void * msgin)
{
  const std_msgs__msg__Int16MultiArray * cmd =
      (const std_msgs__msg__Int16MultiArray *) msgin;

  for (size_t i = 0; i < MOTOR_COUNT; i++)
  {
    int32_t value = (i < cmd->data.size) ? cmd->data.data[i] : 0;
    Motor_SetTarget((uint8_t) i, value);
  }
  last_motor_cmd_tick = osKernelGetTickCount();
}
```

**Change D: the micro-ROS task.** In `StartDefaultTask`, replace **everything between** `/* USER CODE BEGIN 5 */` and `/* USER CODE END 5 */` with:

```c
  /* USER CODE BEGIN 5 */

  /* 1. micro-ROS uses USART2 (USB cable to the Pi) */
  rmw_uros_set_custom_transport(true, (void *) &huart2,
      cubemx_transport_open, cubemx_transport_close,
      cubemx_transport_write, cubemx_transport_read);

  /* 2. micro-ROS uses FreeRTOS memory functions */
  rcl_allocator_t freeRTOS_allocator = rcutils_get_zero_initialized_allocator();
  freeRTOS_allocator.allocate      = microros_allocate;
  freeRTOS_allocator.deallocate    = microros_deallocate;
  freeRTOS_allocator.reallocate    = microros_reallocate;
  freeRTOS_allocator.zero_allocate = microros_zero_allocate;
  if (!rcutils_set_default_allocator(&freeRTOS_allocator)) { error_loop(); }

  /* 3. LD2 ON = waiting for the Agent on the Pi (motors stay stopped) */
  HAL_GPIO_WritePin(LED2_GPIO_PORT, LED2_PIN, GPIO_PIN_SET);
  while (rmw_uros_ping_agent(100, 1) != RMW_RET_OK) { osDelay(500); }
  HAL_GPIO_WritePin(LED2_GPIO_PORT, LED2_PIN, GPIO_PIN_RESET);

  /* 4. Variables */
  rcl_allocator_t allocator = rcl_get_default_allocator();
  rclc_support_t support;
  rcl_node_t node;
  rcl_publisher_t heartbeat_pub;
  std_msgs__msg__Int32 heartbeat_msg;
  rcl_subscription_t motor_sub;
  static std_msgs__msg__Int16MultiArray motor_msg;  /* incoming command   */
  static int16_t motor_buffer[8];                   /* room for 8 numbers */
  rclc_executor_t executor = rclc_executor_get_zero_initialized_executor();

  /* 5. micro-ROS on ROS domain 42, node "drive_mcu" */
  rcl_init_options_t init_options = rcl_get_zero_initialized_init_options();
  RCCHECK(rcl_init_options_init(&init_options, allocator));
  RCCHECK(rcl_init_options_set_domain_id(&init_options, 42));
  RCCHECK(rclc_support_init_with_options(&support, 0, NULL, &init_options, &allocator));
  RCCHECK(rclc_node_init_default(&node, "drive_mcu", "", &support));

  /* 6. Heartbeat publisher */
  RCCHECK(rclc_publisher_init_default(&heartbeat_pub, &node,
      ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int32), "/drive/heartbeat"));

  /* 7. Motor command subscriber. On a microcontroller, an array message
        needs memory reserved in advance: we point it to motor_buffer. */
  motor_msg.data.data           = motor_buffer;
  motor_msg.data.capacity       = 8;
  motor_msg.data.size           = 0;
  motor_msg.layout.dim.data     = NULL;
  motor_msg.layout.dim.capacity = 0;
  motor_msg.layout.dim.size     = 0;
  motor_msg.layout.data_offset  = 0;
  RCCHECK(rclc_subscription_init_default(&motor_sub, &node,
      ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int16MultiArray), "/drive/motor_cmd"));

  /* 8. Executor with 1 handle (the subscriber) */
  RCCHECK(rclc_executor_init(&executor, &support.context, 1, &allocator));
  RCCHECK(rclc_executor_add_subscription(&executor, &motor_sub, &motor_msg,
      &motor_cmd_callback, ON_NEW_DATA));

  /* 9. Main loop (1 tick = 1 ms):
        - read commands,
        - stop everything if no command for 0.5 s,
        - update the motors (ramp, reverse pause),
        - heartbeat every second. */
  heartbeat_msg.data = 0;
  uint32_t last_heartbeat = osKernelGetTickCount();
  uint32_t last_update    = osKernelGetTickCount();
  for (;;)
  {
    rclc_executor_spin_some(&executor, RCL_MS_TO_NS(5));

    uint32_t now = osKernelGetTickCount();
    if (now - last_motor_cmd_tick > MOTOR_CMD_TIMEOUT_MS) { Motor_StopAll(); }
    Motor_Update(now - last_update);
    last_update = now;

    if (now - last_heartbeat >= 1000)
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

**The safety rules in this code:**

| Situation | What happens |
|---|---|
| Board just powered, Agent not there | Motors stopped (`Motor_Init`), LD2 ON |
| A command arrives | Motors ramp to the new speeds |
| No command for 0.5 s (script stopped, Pi crashed, cable pulled, Wi-Fi lost) | All motors ramp down to 0 |
| Command asks the opposite direction | Down to 0, pause 150 ms, then the new direction |

Known limit: if the Agent restarts, the board does not reconnect by itself. Press RESET. Reconnecting automatically is a later improvement.

### 5.4 Build

**Project → Build Project** → `Build Finished. 0 errors`. Write down the memory numbers (`text`, `data`, `bss`) printed in the Console.

## 6. Safety before the first power-on

1. **Robotone on blocks: wheels off the ground.** A wrong sign or a wrong motor would make it drive off the table.
2. Check the circuit as in the PDF "Before switching on": fuses in place, S1 OFF while plugging.
3. Motor power comes from the U1 UBEC (6 V). The Nucleo is powered by USB. The grounds are connected; keep it so.
4. Have one hand near the S1 switch for the first tests.

## 7. Flash and first test

### 7.1 Flash

1. Nucleo on the **laptop** USB.
2. Right-click `Drive_MCU` → **Run As → STM32 C/C++ Application** → OK.
3. After `Download verified successfully`, LD2 is ON (waiting for the Agent).
4. Move the USB cable to the **Pi**. Turn S1 ON.

### 7.2 Window 1 on the Pi: Agent

```bash
ssh <user>@<pi>
source /opt/ros/jazzy/setup.bash
source ~/microros_ws/install/local_setup.bash
export ROS_DOMAIN_ID=42
ros2 run micro_ros_agent micro_ros_agent serial --dev /dev/ttyACM0 --baud 115200
```

Then press **RESET** on the Nucleo. LD2 starts changing once per second.

### 7.3 Window 2 on the Pi: check

```bash
ssh <user>@<pi>
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=42
ros2 node list                 # shows /drive_mcu
ros2 topic list                # shows /drive/heartbeat and /drive/motor_cmd
ros2 topic echo /drive/heartbeat
```

Ctrl+C to stop `echo`.

### 7.4 First motor test (wheels in the air)

A single message makes the motor run for only about 0.5 s and then stop: that is the safety timeout working. To keep a motor running, send the command repeatedly with `--rate 10` (10 times per second), and stop with **Ctrl+C**.

```bash
# One short pulse on M1 at 30 %: M1 turns for about half a second, then stops by itself
ros2 topic pub --once -w 1 /drive/motor_cmd std_msgs/msg/Int16MultiArray "{data: [30, 0, 0, 0]}"

# M1 at 30 % continuously. Ctrl+C -> it stops by itself within 0.5 s
ros2 topic pub --rate 10 /drive/motor_cmd std_msgs/msg/Int16MultiArray "{data: [30, 0, 0, 0]}"

# M1 backward
ros2 topic pub --rate 10 /drive/motor_cmd std_msgs/msg/Int16MultiArray "{data: [-30, 0, 0, 0]}"
```

**Pass:**
- M1 turns one way, then the other.
- It starts smoothly.
- It stops by itself about 0.5 s after Ctrl+C.
- The heartbeat keeps counting.

# PART B: ROS side (Tanya, can start in parallel with part A)

## 8. The bridge and the predefined movement

### 8.1 The two scripts

They are in the repository, in `drive/scripts/`:

| Script | What it does |
|---|---|
| `cmd_vel_to_motors.py` | Listens to a velocity command (`Twist`: forward speed `linear.x` in m/s, turning speed `angular.z` in rad/s) and sends the 4 motor percentages to `/drive/motor_cmd` 20 times per second. It sends 0 if no velocity command arrives for 0.5 s. |
| `drive_sequence.py` | The predefined movement: forward 2 s, stop, turn left 1.5 s, stop, backward 2 s, stop. Sends `Twist` (or `TwistStamped`) at 20 Hz. |

How the bridge computes the wheels (Robotone has fixed wheels: it turns by driving the left and right sides at different speeds):

```text
left  = v − w × track_width / 2
right = v + w × track_width / 2
percent = wheel speed / max_wheel_speed × 100   (then limited to ±max_percent)
```

Parameters of `cmd_vel_to_motors.py` (change at start with `--ros-args -p name:=value`):

| Parameter | Default | Meaning |
|---|---|---|
| `cmd_topic` | `/cmd_vel` | Topic it listens to |
| `stamped` | `false` | `true` if the topic is `TwistStamped` (what the Jazzy diff_drive_controller uses) |
| `track_width` | `0.30` | Distance in m between the centres of the left and right wheels. **Measure it** (section 9.2) |
| `max_wheel_speed` | `0.50` | Wheel speed in m/s at 100 %. **Measure it** (section 9.2) |
| `left_motors` | `[0, 1]` | Which motors (0 = M1 … 3 = M4) are on the left. **Check it** (section 9.1) |
| `right_motors` | `[2, 3]` | Which motors are on the right |
| `max_percent` | `60` | Safety limit. Raise it only after the first tests |
| `cmd_timeout` | `0.5` | Seconds without a command before it sends 0 |

### 8.2 Copy the scripts to the Pi

From the repository folder on your laptop (PowerShell or terminal):

```bash
scp drive/scripts/cmd_vel_to_motors.py drive/scripts/drive_sequence.py <user>@<pi>:~/
```

### 8.3 Test without the robot

You can check the bridge with nothing connected, on the Pi or on your own ROS 2 computer (`export ROS_DOMAIN_ID=42`, or another domain to stay alone):

```bash
# Window A
python3 ~/cmd_vel_to_motors.py
# Window B: what the bridge sends
ros2 topic echo /drive/motor_cmd
# Window C: a velocity command
ros2 topic pub --rate 10 /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.25}, angular: {z: 0.0}}"
```

**Expected:** window B shows `data: [50, 50, 50, 50]`. With `{linear: {x: 0.0}, angular: {z: 1.0}}` it shows `[-30, -30, 30, 30]`. After Ctrl+C in window C, it goes back to `[0, 0, 0, 0]` within 0.5 s. These exact numbers were checked with the default parameters.

**Warning:** on domain 42, if Robotone is powered and its Agent runs, it will move. Use another domain (`export ROS_DOMAIN_ID=7` in all three windows) for tests without the robot.

# PART C: Together on Robotone

## 9. Know the robot

### 9.1 Which motor is which wheel?

Wheels in the air. In window 2 on the Pi, run each line for 2 s, then Ctrl+C:

```bash
ros2 topic pub --rate 10 /drive/motor_cmd std_msgs/msg/Int16MultiArray "{data: [30, 0, 0, 0]}"
ros2 topic pub --rate 10 /drive/motor_cmd std_msgs/msg/Int16MultiArray "{data: [0, 30, 0, 0]}"
ros2 topic pub --rate 10 /drive/motor_cmd std_msgs/msg/Int16MultiArray "{data: [0, 0, 30, 0]}"
ros2 topic pub --rate 10 /drive/motor_cmd std_msgs/msg/Int16MultiArray "{data: [0, 0, 0, 30]}"
```

Fill in this table (add it to `PINMAP.md` in the repository):

| Motor | Which wheel? (front-left, rear-left, front-right, rear-right) | With +30, does the wheel turn so Robotone would go FORWARD? |
|---|---|---|
| M1 | | yes / no |
| M2 | | yes / no |
| M3 | | yes / no |
| M4 | | yes / no |

Then:

1. **Firmware (Adrien or Matthias):** in `motor.c`, put `-1` in `motor_dir` for every motor marked "no". Example: if M3 and M4 are "no", write `{ 1, 1, -1, -1 }`. Build, flash, and test again: all four must now go forward with +30.
2. **Bridge (Tanya):** note which motors are left and which are right. Example: left = M1 and M2 → `left_motors:=[0,1]`, right = M3 and M4 → `right_motors:=[2,3]`.

### 9.2 Measure the robot

- **track_width:** measure in metres between the centre of a left wheel and the centre of the right wheel.
- **max_wheel_speed:**
  1. Wheels in the air. Put a tape mark on one wheel.
  2. Send `{data: [100, 100, 100, 100]}` with `--rate 10` for exactly 10 s, and count the turns N.
  3. Measure the wheel diameter D in metres.
  4. Then `max_wheel_speed = π × D × N / 10` (m/s).

  On the ground it will be a bit slower (load, battery level). That is fine for now; the encoders will measure the real speed later.

Use the **same** track width and wheel diameter in Tanya's simulation model, so both sides talk about the same robot.

## 10. Drive

### 10.1 Window 3 on the Pi: start the bridge

```bash
ssh <user>@<pi>
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=42
python3 ~/cmd_vel_to_motors.py --ros-args \
  -p track_width:=<measured> -p max_wheel_speed:=<measured> \
  -p left_motors:="[0, 1]" -p right_motors:="[2, 3]" -p max_percent:=60
```

(Put your values from section 9.)

### 10.2 Keyboard driving (wheels in the air first, then on the floor)

In window 2:

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

| Key | Action |
|---|---|
| `i` | forward |
| `,` | backward |
| `j` / `l` | turn left / right on the spot |
| `k` | stop |
| `z` | slower (press a few times before starting) |
| `q` | faster |

Hold the key down. If Robotone stutters (the keyboard repeats slower than the 0.5 s timeout), restart the bridge with `-p cmd_timeout:=1.0`.

**Pass:**
- `i` → both sides turn forward.
- `j` → the left side goes backward and the right side forward (Robotone turns left).
- Releasing the keys → stop within about 0.5 s.

If `j` turns right, the left and right motor lists are swapped.

### 10.3 The predefined movement on the robot

Bridge still running (window 3). Clear space on the floor, then in window 2:

```bash
python3 ~/drive_sequence.py
```

**Pass:** forward about 2 × 0.2 = 0.4 m, stop, turn left, stop, backward, stop. Measure how far it went and how much it turned. Write it down.

## 11. Same movement in simulation and on the robot (Tanya)

1. Start the simulation. Find the topic and type of the drive controller's command:

   ```bash
   ros2 topic list -t | grep cmd_vel
   ```

   In ROS 2 Jazzy, the `diff_drive_controller` usually listens on `/diff_drive_controller/cmd_vel` with type `geometry_msgs/msg/TwistStamped`. Use what the command shows.

2. Run the same script on the simulation:

   ```bash
   python3 drive_sequence.py --ros-args -p cmd_topic:=/diff_drive_controller/cmd_vel -p stamped:=true
   ```

3. Compare with the real robot (section 10.3): distance, angle turned and time. Write down the differences and think about why: slip, friction, a speed limit in the controller, or the real top speed under load.

4. **Mirroring (Level 2 goal):** start the bridge with the simulation's topic:

   ```bash
   python3 ~/cmd_vel_to_motors.py --ros-args -p cmd_topic:=/diff_drive_controller/cmd_vel -p stamped:=true ...
   ```

   Then one command drives both at once. The simulation must run on **domain 42** and see the Pi (laptop–Pi discovery, as for the heartbeat). **Robotone on the floor will move at the same time as the simulation**, so clear the space first.

## 12. Save the work on GitHub

Commit on `drive/feature/motor-ros-control`:

- `Drive_MCU.ioc`, `Core/Src/main.c`, `Core/Src/stm32f4xx_hal_msp.c`, `Core/Inc/motor.h`, `Core/Src/motor.c`;
- the motor table in `PINMAP.md`;
- any changes to `drive/scripts/`.

Never commit `Debug/` or `.metadata/`. Push, open a pull request to `main`, and ask Adrien to review.

## 13. Problems and what to do

| What you see | Likely reason | What to do |
|---|---|---|
| `docker: not found` when building | `libmicroros.a` missing from your copy | Pull `main`; check `Drive_MCU\micro_ros_stm32cubemx_utils\microros_static_library_ide\libmicroros\libmicroros.a` (16 MB) |
| `htim3` / `htim4` undeclared | Code not generated or not refreshed | Section 4.7 again, then F5 |
| A motor never turns | Wrong pin in CubeMX, PWM not started, or wiring | Check the 8 pins are green in CubeMX on the right pins (section 4.3). Check `Motor_Init()` is in USER CODE 2 |
| A motor turns only in one direction | Its IN2 channel is missing in CubeMX | All 4 channels of TIM3 and TIM4 must be `PWM Generation` |
| Motor turns for 0.5 s then stops | Normal: the safety timeout | Send with `--rate 10`, or use the bridge |
| Motors jerk every second | A command source stops and starts | Use the bridge, or increase `--rate` |
| LD2 always ON | Board cannot reach the Agent | Agent running? Cable on the Pi? RESET after starting the Agent |
| LD2 blinks very fast | A micro-ROS step failed | RESET with the Agent running; tell Adrien what changed last |
| Nucleo resets when motors start | Power or ground problem | Motors on the UBEC, never the Nucleo. Check the ground link and fuses. Lower `max_percent` |
| Bridge sends 0 while teleop runs | Teleop on another topic or type | `ros2 topic info /cmd_vel`; set `cmd_topic` and `stamped` |
| Robotone turns the wrong way | Left and right swapped, or a wrong `motor_dir` | Section 9.1 again |
| Sim and robot do not both move | Different domain, or the laptop does not see the Pi | Same `ROS_DOMAIN_ID=42`; `ros2 node list` on the laptop must show `/drive_mcu` |

## 14. Checklist (send to Adrien)

- [ ] `Drive_MCU` builds unchanged (section 3).
- [ ] TIM3 and TIM4 on the right 8 pins, code generated.
- [ ] Builds with the motor code. Memory: text ____ data ____ bss ____.
- [ ] `/drive_mcu`, `/drive/heartbeat` and `/drive/motor_cmd` visible on the Pi.
- [ ] Each motor turns both ways, smooth start, stops by itself after 0.5 s.
- [ ] Motor table filled in, `motor_dir` set, all wheels go forward with +30.
- [ ] Track width ____ m, wheel diameter ____ m, `max_wheel_speed` ____ m/s.
- [ ] Keyboard driving works, and `j` turns left.
- [ ] `drive_sequence.py` on the robot: distance ____ m, angle ____ °.
- [ ] Same sequence in simulation: distance ____ m, angle ____ °. Differences explained.
- [ ] Pull request opened.

## 15. Questions for the team meeting

- Why is the 0.5 s timeout on the MCU and also in the bridge? What would happen with only one of them?
- What is a good ramp time for the real rover (60 kg)? What happens to the battery current without a ramp?
- The robot does not reach the commanded speed on the floor. What would the wheel encoders let us do about it?
- How many timers do 4 encoders need, and are enough left after TIM3, TIM4 (motors) and TIM6 (FreeRTOS)?
- Should the board reconnect automatically when the Agent restarts? How would you detect that the Agent is gone?

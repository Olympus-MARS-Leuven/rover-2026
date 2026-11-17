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

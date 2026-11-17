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

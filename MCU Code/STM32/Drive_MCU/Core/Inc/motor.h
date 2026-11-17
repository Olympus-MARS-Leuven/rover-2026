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

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

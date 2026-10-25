# Motor_Test - pin map and config reference

Board: NUCLEO-F446RE (STM32F446RET6). Keep this file up to date at every hardware or CubeMX change.

## Toolchain
- STM32CubeIDE 2.2.0 (build/flash/debug), standalone STM32CubeMX (the .ioc is edited only there; last saved with 6.18.1)
- Firmware package: STM32Cube FW_F4 V1.28.3
- Project type: Eclipse / managed build (STM32CubeIDE). Sources are in Src/ and Inc/ (NOT Core/Src).
- Debug: onboard ST-LINK (SWD)

## Clocks
HSI 16 MHz -> PLL (M=16, N=336, P=4) -> SYSCLK/HCLK 84 MHz. APB1 42 MHz, APB2 84 MHz, timer clocks 84 MHz.

## Motors (2x DRV8833, 4 DC motors with encoders) - PWM 2 kHz (TIM3 / TIM4: PSC 83, ARR 499, 0..500 = 0..100 %)
| Motor | Driver / outputs | IN1 pin / timer ch | IN2 pin / timer ch |
|-------|------------------|--------------------|--------------------|
| M1 | DRV8833 #1 OUT1/OUT2 | PA6 / TIM3_CH1 | PA7 / TIM3_CH2 |
| M2 | DRV8833 #1 OUT3/OUT4 | PB0 / TIM3_CH3 | PB1 / TIM3_CH4 |
| M3 | DRV8833 #2 OUT1/OUT2 | PB6 / TIM4_CH1 | PB7 / TIM4_CH2 |
| M4 | DRV8833 #2 OUT3/OUT4 | PB8 / TIM4_CH3 | PB9 / TIM4_CH4 |
Current code: forward = PWM on IN1, IN2 = 0.

## Servos (4x SG90) - PWM 50 Hz (TIM8: PSC 83, ARR 19999, compare value = pulse in microseconds)
| Servo | Pin / timer ch |
|-------|----------------|
| SG90 #1 | PC6 / TIM8_CH1 |
| SG90 #2 | PC7 / TIM8_CH2 |
| SG90 #3 | PC8 / TIM8_CH3 |
| SG90 #4 | PC9 / TIM8_CH4 |
Current code: 1000..2000 us, all four identical, 1500 = centre.

## Analog inputs (12 bit, software start, polling)
| Function | Pin | ADC |
|----------|-----|-----|
| Pot 1 - motor speed | PA0 | ADC1_IN0 |
| Pot 2 - servo position | PA1 | ADC2_IN1 |
Pots: outer pins 3.3 V and GND, wiper to the pin.

## Reserved by the Nucleo board (do not reuse)
| Pin | Use |
|-----|-----|
| PA2 / PA3 | USART2 TX / RX to the ST-LINK virtual COM port (USB serial to the computer). Pins configured, USART2 peripheral NOT enabled yet in the .ioc |
| PA5 | LED2 (green user LED) |
| PC13 | USER button B1, EXTI13 interrupt (falling edge), no callback in the code yet |
| PA13 / PA14 / PB3 | SWDIO / SWCLK / SWO (debug) |
| PC14 / PC15, PH0 / PH1 | 32 kHz crystal and HSE pins (not used as GPIO) |

## Encoders (motor connector pins 3 and 4: A phase and B phase; pin 2 = encoder +3.3 V/5 V, pin 5 = encoder GND)
Not wired yet. Pins and timers to be chosen later (TIM3, TIM4, TIM8 are already used for PWM). Update this file when done.

## Power (see Motor_Servo_Circuit.pdf)
NiMH 8.4 V -> fuse 5 A -> switch -> D1 -> U1 UBEC 6 V (motors, 2x 1 A fuses) and U2 UBEC 5 V (servos, 3 A fuse).
Nucleo and Raspberry Pi are powered from USB power banks; MCU GND must be common with the motor/servo ground.

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

MicroPython project for an ESP32-S3 CAM five-channel grayscale sensor line-following robot car. Uses PD (proportional-derivative) control with binary black/white detection (not continuous grayscale). Speed control is subtract-only — the PD correction only slows one side of the car, never accelerates beyond `BASE_SPEED`.

## Architecture

```
config.py          ← single source of truth: all pins, thresholds, PD gains, debug flags
gray_sensor.py     ← GraySensorArray: ADC reading with filtering (dummy→settle→sample→median)
motor.py           ← Motor (per-wheel PWM) + MotorDriver (left+right pair)
line_follower.py   ← main loop: read sensors → calculate binary error → PD control → drive motors
motor_speed_test.py ← utility: measure wheel RPM via quadrature encoders (PWM sweep or PID hold)
```

**Data flow in the main loop:** `GraySensorArray.read_state()` returns raw ADC values + boolean black flags per channel → `read_sensors()` maps them to sensor order → `calculate_error()` computes weighted-average error from binary values → `pd_control()` computes PD correction with outer-sensor boost, producing left/right motor speeds → `MotorDriver.drive()` applies PWM.

**Lost-line handling:** When all five sensors see white (`black_values` all zero), the car either holds its last motor output (if outer sensors haven't changed state — line just moved away briefly) or enters search mode (spins in the direction of the last known error to reacquire the line).

**Motor PWM:** Each motor uses two GPIO pins (forward + backward). Speed ±100 maps to PWM duty 0–100%. Direction reversal is handled in `Motor.set_speed()` via `config.LEFT_MOTOR_REVERSE` / `RIGHT_MOTOR_REVERSE`.

## How to work with this code

- There is **no build step, no test suite, no linter** — this is bare MicroPython flashed to an ESP32-S3. Edit files directly, then copy them to the device.
- **All tuning happens in `config.py`.** When adjusting PD behavior, sensor thresholds, motor trim, or debug output, `config.py` is the only file to touch.
- The five sensors are physically ordered left-to-right as `adc4, adc3, adc2, adc1, adc5` but mapped to logical positions `L2, L1, M, R1, R2` with weights `[-2, -1, 0, 1, 2]`.
- `line_follower.py` is the entry point for line following. `motor_speed_test.py` is a standalone utility — it does not import or depend on `line_follower.py`.
- ADC filtering parameters (`DUMMY_READS`, `SETTLE_US`, `SAMPLES_PER_CHANNEL`, `SAMPLE_GAP_US`) trade speed vs. stability. Higher values = more stable readings but slower control loop.
- The `TURN_DIR` config flips the sign of the PD correction. Set to `-1` if the car turns the wrong way.

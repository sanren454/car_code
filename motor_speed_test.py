from machine import Pin
import time

import config
from motor import MotorDriver


# Wheel encoder pin configuration.
# ENCODER_CPR means the number of counted pulses per wheel revolution.
# This test counts only channel-A rising edges. If your encoder datasheet says
# 11 PPR on the motor shaft and the gearbox is 30:1, set CPR to 11 * 30.
LEFT_ENCODER_A_PIN = 16
LEFT_ENCODER_B_PIN = 17
RIGHT_ENCODER_A_PIN = 18
RIGHT_ENCODER_B_PIN = 19
ENCODER_CPR = 60

# Flip these if the measured RPM is negative while the wheel moves forward.
LEFT_ENCODER_REVERSE = False
RIGHT_ENCODER_REVERSE = False

# "sweep": run several PWM percentages and print measured RPM.
# "pid": hold TARGET_RPM with closed-loop PWM control.
SPEED_TEST_MODE = "sweep"
SPEED_TEST_PWM_STEPS = [25, 35, 45, 55, 65]
SPEED_TEST_STEP_DURATION_MS = 3000
SPEED_TEST_PRINT_INTERVAL_MS = 250

TARGET_RPM_LEFT = 120
TARGET_RPM_RIGHT = 120
PID_TEST_DURATION_MS = 15000
PID_MIN_PWM = 20
PID_MAX_PWM = 85
PID_KP = 0.35
PID_KI = 0.08
PID_KD = 0.02


class QuadratureEncoder:
    def __init__(self, a_pin, b_pin, reverse=False):
        self.count = 0
        self.reverse = reverse
        self.pin_a = Pin(a_pin, Pin.IN, Pin.PULL_UP)
        self.pin_b = Pin(b_pin, Pin.IN, Pin.PULL_UP)
        self.pin_a.irq(trigger=Pin.IRQ_RISING, handler=self._on_rising_a)

    def _on_rising_a(self, pin):
        step = -1 if self.pin_b.value() == 0 else 1
        if self.reverse:
            step = -step
        self.count += step

    def read(self):
        return self.count

    def stop(self):
        self.pin_a.irq(handler=None)


class WheelSpeedMeter:
    def __init__(self):
        self.left = QuadratureEncoder(
            LEFT_ENCODER_A_PIN,
            LEFT_ENCODER_B_PIN,
            LEFT_ENCODER_REVERSE,
        )
        self.right = QuadratureEncoder(
            RIGHT_ENCODER_A_PIN,
            RIGHT_ENCODER_B_PIN,
            RIGHT_ENCODER_REVERSE,
        )
        self.last_ms = time.ticks_ms()
        self.last_left_count = self.left.read()
        self.last_right_count = self.right.read()

    def sample(self):
        now_ms = time.ticks_ms()
        interval_ms = time.ticks_diff(now_ms, self.last_ms)
        if interval_ms <= 0:
            interval_ms = 1

        left_count = self.left.read()
        right_count = self.right.read()
        delta_left = left_count - self.last_left_count
        delta_right = right_count - self.last_right_count

        self.last_ms = now_ms
        self.last_left_count = left_count
        self.last_right_count = right_count

        left_rpm = self._delta_to_rpm(delta_left, interval_ms)
        right_rpm = self._delta_to_rpm(delta_right, interval_ms)

        return {
            "interval_ms": interval_ms,
            "left_count": left_count,
            "right_count": right_count,
            "delta_left": delta_left,
            "delta_right": delta_right,
            "left_rpm": left_rpm,
            "right_rpm": right_rpm,
        }

    def _delta_to_rpm(self, delta_count, interval_ms):
        return delta_count * 60000 / (ENCODER_CPR * interval_ms)

    def stop(self):
        self.left.stop()
        self.right.stop()


class Pid:
    def __init__(self, kp, ki, kd, output_min, output_max):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.output_min = output_min
        self.output_max = output_max
        self.integral = 0
        self.last_error = 0

    def update(self, target, actual, dt_s, current_output):
        if dt_s <= 0:
            dt_s = 0.001

        error = target - actual
        self.integral += error * dt_s
        derivative = (error - self.last_error) / dt_s
        self.last_error = error

        output = current_output
        output += self.kp * error
        output += self.ki * self.integral
        output += self.kd * derivative
        return clamp(output, self.output_min, self.output_max)


def clamp(value, low, high):
    value = int(value)
    if value < low:
        return low
    if value > high:
        return high
    return value


def print_header():
    print("=" * 72)
    print("Motor speed test")
    print("mode:", SPEED_TEST_MODE)
    print("encoder cpr:", ENCODER_CPR)
    print(
        "left encoder pins: A={} B={}".format(
            LEFT_ENCODER_A_PIN,
            LEFT_ENCODER_B_PIN,
        )
    )
    print(
        "right encoder pins: A={} B={}".format(
            RIGHT_ENCODER_A_PIN,
            RIGHT_ENCODER_B_PIN,
        )
    )
    print("Press Ctrl+C to stop.")
    print("=" * 72)


def print_sample(label, left_pwm, right_pwm, sample):
    print(
        "{} dt={}ms L_pwm={} R_pwm={} L_cnt={} R_cnt={} L_d={} R_d={} L_rpm={:.1f} R_rpm={:.1f}".format(
            label,
            sample["interval_ms"],
            left_pwm,
            right_pwm,
            sample["left_count"],
            sample["right_count"],
            sample["delta_left"],
            sample["delta_right"],
            sample["left_rpm"],
            sample["right_rpm"],
        )
    )


def run_pwm_sweep(motors, meter):
    print("PWM sweep started")
    print("steps:", SPEED_TEST_PWM_STEPS)

    for pwm in SPEED_TEST_PWM_STEPS:
        left_pwm = clamp(pwm + config.LEFT_TRIM, -100, 100)
        right_pwm = clamp(pwm + config.RIGHT_TRIM, -100, 100)
        step_start_ms = time.ticks_ms()
        last_print_ms = step_start_ms
        motors.drive(left_pwm, right_pwm)
        print("step pwm={}".format(pwm))

        while time.ticks_diff(time.ticks_ms(), step_start_ms) < SPEED_TEST_STEP_DURATION_MS:
            now_ms = time.ticks_ms()
            if time.ticks_diff(now_ms, last_print_ms) >= SPEED_TEST_PRINT_INTERVAL_MS:
                sample = meter.sample()
                print_sample("sweep", left_pwm, right_pwm, sample)
                last_print_ms = now_ms
            time.sleep_ms(10)

    motors.stop()
    print("PWM sweep finished")


def run_pid_hold(motors, meter):
    left_pid = Pid(
        PID_KP,
        PID_KI,
        PID_KD,
        PID_MIN_PWM,
        PID_MAX_PWM,
    )
    right_pid = Pid(
        PID_KP,
        PID_KI,
        PID_KD,
        PID_MIN_PWM,
        PID_MAX_PWM,
    )
    left_pwm = PID_MIN_PWM
    right_pwm = PID_MIN_PWM
    start_ms = time.ticks_ms()
    last_print_ms = start_ms

    print("PID hold started")
    print("target L={}rpm R={}rpm".format(TARGET_RPM_LEFT, TARGET_RPM_RIGHT))

    while time.ticks_diff(time.ticks_ms(), start_ms) < PID_TEST_DURATION_MS:
        now_ms = time.ticks_ms()
        if time.ticks_diff(now_ms, last_print_ms) >= SPEED_TEST_PRINT_INTERVAL_MS:
            sample = meter.sample()
            dt_s = sample["interval_ms"] / 1000

            left_pwm = left_pid.update(
                TARGET_RPM_LEFT,
                sample["left_rpm"],
                dt_s,
                left_pwm,
            )
            right_pwm = right_pid.update(
                TARGET_RPM_RIGHT,
                sample["right_rpm"],
                dt_s,
                right_pwm,
            )

            motors.drive(left_pwm, right_pwm)
            print_sample("pid", left_pwm, right_pwm, sample)
            last_print_ms = now_ms

        time.sleep_ms(10)

    motors.stop()
    print("PID hold finished")


def main():
    motors = MotorDriver()
    meter = WheelSpeedMeter()
    print_header()

    try:
        if SPEED_TEST_MODE == "pid":
            run_pid_hold(motors, meter)
        else:
            run_pwm_sweep(motors, meter)
    except KeyboardInterrupt:
        print("Stopped by user")
    finally:
        motors.stop()
        meter.stop()
        print("Motors stopped")


if __name__ == "__main__":
    main()

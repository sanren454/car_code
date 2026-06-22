from machine import Pin, PWM

import config


class Motor:
    def __init__(self, forward_pin, backward_pin, reversed_dir=False):
        self.forward_pwm = PWM(Pin(forward_pin), freq=config.PWM_FREQ)
        self.backward_pwm = PWM(Pin(backward_pin), freq=config.PWM_FREQ)
        self.reversed_dir = reversed_dir
        self.stop()

    def _set_pwm_percent(self, pwm, percent):
        percent = max(0, min(100, int(percent)))
        try:
            pwm.duty_u16(percent * 65535 // 100)
        except AttributeError:
            pwm.duty(percent * 1023 // 100)

    def set_speed(self, speed):
        speed = max(-100, min(100, int(speed)))
        if self.reversed_dir:
            speed = -speed

        if speed > 0:
            self._set_pwm_percent(self.forward_pwm, speed)
            self._set_pwm_percent(self.backward_pwm, 0)
        elif speed < 0:
            self._set_pwm_percent(self.forward_pwm, 0)
            self._set_pwm_percent(self.backward_pwm, -speed)
        else:
            self.stop()

    def stop(self):
        self._set_pwm_percent(self.forward_pwm, 0)
        self._set_pwm_percent(self.backward_pwm, 0)


class MotorDriver:
    def __init__(self):
        self.left = Motor(
            config.LEFT_MOTOR_FORWARD_PIN,
            config.LEFT_MOTOR_BACKWARD_PIN,
            config.LEFT_MOTOR_REVERSE,
        )
        self.right = Motor(
            config.RIGHT_MOTOR_FORWARD_PIN,
            config.RIGHT_MOTOR_BACKWARD_PIN,
            config.RIGHT_MOTOR_REVERSE,
        )

    def drive(self, left_speed, right_speed):
        self.left.set_speed(left_speed)
        self.right.set_speed(right_speed)

    def stop(self):
        self.left.stop()
        self.right.stop()

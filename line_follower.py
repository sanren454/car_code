import time

import config
from gray_sensor import GraySensorArray
from motor import MotorDriver


def decide_action(black, delta):
    if black["adc1"] or black["adc5"]:
        if delta["adc1"] >= delta["adc5"]:
            return "sharp_left"
        return "sharp_right"

    if black["adc2"] or black["adc4"]:
        if delta["adc2"] >= delta["adc4"]:
            return "slight_left"
        return "slight_right"

    if black["adc3"]:
        return "forward"

    return "lost"


def action_to_speed(action):
    if action == "forward":
        return config.BASIC_SPEED, config.BASIC_SPEED

    if action == "slight_left":
        return config.SLIGHT_TURN_INNER_SPEED, config.SLIGHT_TURN_OUTER_SPEED

    if action == "slight_right":
        return config.SLIGHT_TURN_OUTER_SPEED, config.SLIGHT_TURN_INNER_SPEED

    if action == "sharp_left":
        return -config.SHARP_TURN_SPEED, config.SHARP_TURN_SPEED

    if action == "sharp_right":
        return config.SHARP_TURN_SPEED, -config.SHARP_TURN_SPEED

    return 0, 0


class ConfirmedDecision:
    def __init__(self):
        self.last_candidate = None
        self.count = 0
        self.current = "lost"

    def update(self, candidate):
        if candidate == self.last_candidate:
            self.count += 1
        else:
            self.last_candidate = candidate
            self.count = 1

        if self.count >= config.CONFIRM_COUNT:
            self.current = candidate

        return self.current


def main():
    sensors = GraySensorArray()
    motors = MotorDriver()
    decision = ConfirmedDecision()

    try:
        motors.stop()
        sensors.calibrate_baseline()
        print("Line follower started. Press Ctrl+C to stop.")
        last_debug_ms = 0

        while True:
            raw, delta, black = sensors.read_state()
            candidate = decide_action(black, delta)
            action = decision.update(candidate)
            left_speed, right_speed = action_to_speed(action)
            motors.drive(left_speed, right_speed)

            now_ms = time.ticks_ms()
            if config.DEBUG_PRINT and time.ticks_diff(now_ms, last_debug_ms) >= config.DEBUG_INTERVAL_MS:
                print(
                    "action={} L={} R={} raw={} delta={} black={}".format(
                        action,
                        left_speed,
                        right_speed,
                        raw,
                        delta,
                        black,
                    )
                )
                last_debug_ms = now_ms

            time.sleep_ms(config.CONTROL_INTERVAL_MS)

    except KeyboardInterrupt:
        print("Stopped by user.")
    finally:
        motors.stop()


if __name__ == "__main__":
    main()

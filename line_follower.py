import time

import config
from gray_sensor import GraySensorArray
from motor import MotorDriver


def limit_speed(speed):
    speed = int(speed)

    if speed > config.MAX_SPEED:
        return config.MAX_SPEED
    if speed < -config.MAX_SPEED:
        return -config.MAX_SPEED

    if 0 < speed < config.MIN_SPEED:
        return config.MIN_SPEED
    if -config.MIN_SPEED < speed < 0:
        return -config.MIN_SPEED

    return speed


def read_sensors(sensor_array):
    raw_by_channel, black_by_channel = sensor_array.read_state()

    raw_values = []
    black_values = []

    for channel in config.FOLLOWER_CHANNELS:
        raw = raw_by_channel[channel]
        raw_values.append(raw)
        black_values.append(1 if black_by_channel[channel] else 0)

    return raw_values, black_values


def calculate_error(black_values, last_error):
    black_count = sum(black_values)

    if black_count <= 0:
        return last_error, True

    weighted_sum = 0
    for weight, is_black in zip(config.FOLLOWER_WEIGHTS, black_values):
        weighted_sum += weight * is_black

    return weighted_sum / black_count, False


def has_edge_black(black_values):
    return black_values[0] or black_values[-1]


def pd_control(error, last_error, black_values, dt_s):
    if dt_s <= 0:
        dt_s = 0.001

    derivative = (error - last_error) / dt_s
    correction = config.Kp * error + config.Kd * derivative
    if has_edge_black(black_values):
        correction *= config.EDGE_CORRECTION_GAIN

    correction = config.TURN_DIR * correction

    left_speed = config.BASE_SPEED + correction
    right_speed = config.BASE_SPEED - correction

    left_output = limit_speed(left_speed + config.LEFT_TRIM)
    right_output = limit_speed(right_speed + config.RIGHT_TRIM)

    return correction, left_output, right_output


def update_search_direction(error, last_search_direction):
    if error < -config.SEARCH_DIRECTION_ERROR_THRESHOLD:
        return -1
    if error > config.SEARCH_DIRECTION_ERROR_THRESHOLD:
        return 1
    return last_search_direction


def outer_black_unchanged(black_values, last_outer_black):
    if last_outer_black is None:
        return False

    return black_values[0] == last_outer_black[0] and black_values[-1] == last_outer_black[1]


def search_line(last_search_direction):
    if not config.LOST_LINE_SEARCH:
        return 0, 0, 0

    direction = -1 if last_search_direction < 0 else 1
    direction = config.TURN_DIR * direction

    if direction < 0:
        left_output = -config.SEARCH_SPEED
        right_output = config.SEARCH_SPEED + config.RIGHT_TRIM
    else:
        left_output = config.SEARCH_SPEED + config.LEFT_TRIM
        right_output = -config.SEARCH_SPEED

    return 0, limit_speed(left_output), limit_speed(right_output)


def format_values(names, values):
    parts = []
    for name, value in zip(names, values):
        parts.append("{}={}".format(name, value))
    return " ".join(parts)


def print_startup_info():
    if not config.DEBUG:
        return

    print("Five-channel IR PD line follower started")
    print("order:", ", ".join(config.FOLLOWER_SENSOR_NAMES))
    print("channels:", ", ".join(config.FOLLOWER_CHANNELS))
    print("weights:", config.FOLLOWER_WEIGHTS)
    print("thresholds:", config.BLACK_RAW_THRESHOLDS)
    print("BLACK_IS_HIGH:", config.BLACK_IS_HIGH)
    print("LOST_LINE_HOLD:", config.LOST_LINE_HOLD)
    print("LOST_LINE_SEARCH:", config.LOST_LINE_SEARCH)
    print("TURN_DIR:", config.TURN_DIR)
    print("BASE_SPEED:", config.BASE_SPEED)
    print("Kp:", config.Kp)
    print("Kd:", config.Kd)
    print("CONTROL_DT_MS:", config.CONTROL_DT_MS)
    print("LEFT_TRIM:", config.LEFT_TRIM)
    print("RIGHT_TRIM:", config.RIGHT_TRIM)
    print("PWM_FREQ:", config.PWM_FREQ)


def main():
    sensors = GraySensorArray()
    motors = MotorDriver()

    last_error = 0
    last_search_direction = 0
    last_outer_black = None
    last_left_output = 0
    last_right_output = 0
    last_debug_ms = time.ticks_ms()
    start_ms = time.ticks_ms()
    last_control_ms = start_ms

    print_startup_info()

    try:
        while True:
            now_ms = time.ticks_ms()
            elapsed_ms = time.ticks_diff(now_ms, last_control_ms)
            if elapsed_ms <= 0:
                elapsed_ms = 1
            dt_s = config.CONTROL_DT_MS / 1000

            raw_values, black_values = read_sensors(sensors)
            mode = None

            error, line_lost = calculate_error(black_values, last_error)

            if line_lost:
                outer_unchanged = outer_black_unchanged(black_values, last_outer_black)
                hold_enabled = config.LOST_LINE_HOLD and outer_unchanged
                if hold_enabled:
                    mode = "hold"
                    correction = 0
                    left_output = last_left_output
                    right_output = last_right_output
                else:
                    mode = "search"
                    correction, left_output, right_output = search_line(last_search_direction)
            else:
                outer_unchanged = True
                mode = "pd"
                last_outer_black = (black_values[0], black_values[-1])
                correction, left_output, right_output = pd_control(
                    error,
                    last_error,
                    black_values,
                    dt_s,
                )
                last_error = error
                last_search_direction = update_search_direction(error, last_search_direction)

            motors.drive(left_output, right_output)
            last_left_output = left_output
            last_right_output = right_output
            last_control_ms = now_ms

            now_ms = time.ticks_ms()
            if config.DEBUG and time.ticks_diff(now_ms, last_debug_ms) >= config.DEBUG_INTERVAL_MS:
                print(
                    "t={}ms raw=[{}] binary=[{}] lost={} outer_same={} mode={} error={:.2f} dt={}ms actual_dt={}ms correction={:.2f} last_side={} L={} R={}".format(
                        time.ticks_diff(now_ms, start_ms),
                        format_values(config.FOLLOWER_SENSOR_NAMES, raw_values),
                        format_values(config.FOLLOWER_SENSOR_NAMES, black_values),
                        1 if line_lost else 0,
                        1 if outer_unchanged else 0,
                        mode,
                        error,
                        config.CONTROL_DT_MS,
                        elapsed_ms,
                        correction,
                        last_search_direction,
                        left_output,
                        right_output,
                    )
                )
                last_debug_ms = now_ms

            time.sleep_ms(config.LOOP_DELAY_MS)

    except KeyboardInterrupt:
        print("Line follower stopped")
    finally:
        motors.stop()
        print("Motors stopped")


if __name__ == "__main__":
    main()

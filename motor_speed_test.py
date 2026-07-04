from machine import Pin
import time

from motor import MotorDriver


LEFT_TEST_SPEED = 35
RIGHT_TEST_SPEED = 36

TEST_DURATION_MS = 1000000
PRINT_INTERVAL_MS = 500
ENCODER_CPR = 60

LEFT_ENCODER_A_PIN = 16
LEFT_ENCODER_B_PIN = 17
RIGHT_ENCODER_A_PIN = 18
RIGHT_ENCODER_B_PIN = 19


left_encoder_count = 0
right_encoder_count = 0

left_encoder_a = Pin(LEFT_ENCODER_A_PIN, Pin.IN, Pin.PULL_UP)
left_encoder_b = Pin(LEFT_ENCODER_B_PIN, Pin.IN, Pin.PULL_UP)
right_encoder_a = Pin(RIGHT_ENCODER_A_PIN, Pin.IN, Pin.PULL_UP)
right_encoder_b = Pin(RIGHT_ENCODER_B_PIN, Pin.IN, Pin.PULL_UP)


def clamp_speed(speed):
    return max(-100, min(100, int(speed)))


def left_encoder_callback(pin):
    global left_encoder_count
    if left_encoder_b.value() == 0:
        left_encoder_count -= 1
    else:
        left_encoder_count += 1


def right_encoder_callback(pin):
    global right_encoder_count
    if right_encoder_b.value() == 0:
        right_encoder_count -= 1
    else:
        right_encoder_count += 1


def read_encoders():
    return left_encoder_count, right_encoder_count


def calc_rpm(delta_count, interval_ms):
    return (delta_count / ENCODER_CPR) * (60000 / interval_ms)


def main():
    left_speed = clamp_speed(LEFT_TEST_SPEED)
    right_speed = clamp_speed(RIGHT_TEST_SPEED)
    motors = MotorDriver()

    left_encoder_a.irq(trigger=Pin.IRQ_RISING, handler=left_encoder_callback)
    right_encoder_a.irq(trigger=Pin.IRQ_RISING, handler=right_encoder_callback)

    print("=" * 50)
    print("双电机定值速度测试")
    print("左电机速度: {}%".format(left_speed))
    print("右电机速度: {}%".format(right_speed))
    print("测试时间: {} ms".format(TEST_DURATION_MS))
    print("编码器 CPR: {}".format(ENCODER_CPR))
    print("按 Ctrl+C 可提前停止")
    print("=" * 50)

    start_ms = time.ticks_ms()
    last_print_ms = start_ms
    last_left_count = 0
    last_right_count = 0

    try:
        motors.drive(left_speed, right_speed)

        while time.ticks_diff(time.ticks_ms(), start_ms) < TEST_DURATION_MS:
            now_ms = time.ticks_ms()
            if time.ticks_diff(now_ms, last_print_ms) >= PRINT_INTERVAL_MS:
                left_count, right_count = read_encoders()
                delta_left = left_count - last_left_count
                delta_right = right_count - last_right_count
                interval_ms = time.ticks_diff(now_ms, last_print_ms)

                left_rpm = calc_rpm(delta_left, interval_ms)
                right_rpm = calc_rpm(delta_right, interval_ms)
                elapsed_ms = time.ticks_diff(now_ms, start_ms)

                print(
                    "t={}ms L_set={} R_set={} L_count={} R_count={} L_rpm={:.1f} R_rpm={:.1f}".format(
                        elapsed_ms,
                        left_speed,
                        right_speed,
                        left_count,
                        right_count,
                        left_rpm,
                        right_rpm,
                    )
                )

                last_left_count = left_count
                last_right_count = right_count
                last_print_ms = now_ms

            time.sleep_ms(20)

    except KeyboardInterrupt:
        print("测试被手动停止")
    finally:
        motors.stop()
        left_encoder_a.irq(handler=None)
        right_encoder_a.irq(handler=None)
        print("电机已停止")


if __name__ == "__main__":
    main()

# Original five-channel gray sensor ADC pin configuration.
# Sensor order from left to right: adc4, adc3, adc2, adc1, adc5.
ADC_PINS = {
    "adc1": 27,
    "adc2": 33,
    "adc3": 32,
    "adc4": 35,
    "adc5": 34,
}

CHANNELS = ["adc4", "adc3", "adc2", "adc1", "adc5"]

# Five-channel line follower configuration.
FOLLOWER_CHANNELS = ["adc4", "adc3", "adc2", "adc1", "adc5"]
FOLLOWER_SENSOR_NAMES = ["L2", "L1", "M", "R1", "R2"]
FOLLOWER_WEIGHTS = [-2, -1.2, 0, 1.2, 2]
BLACK_IS_HIGH = False

# PD and speed parameters.
BASE_SPEED = 60
MAX_SPEED = 100
# 电机死区补偿：非零输出如果落在 -25..25 内，会提升到对应方向的 25。
MIN_SPEED = 25
Kp = 16
Kd = 7
SEARCH_SPEED = 80

# 急弯降速：L2/R2 检测到黑线时基础速度降到 50。
# 外侧灯离开黑线后继续保持 18ms，再恢复 BASE_SPEED。
SHARP_TURN_SLOWDOWN_ENABLED = True
SHARP_TURN_SPEED = 50
SHARP_TURN_RELEASE_DELAY_MS = 18

# 环岛/宽黑线屏蔽急弯降速，避免环岛区域被误判成急弯。
SHARP_TURN_IGNORE_ROUNDABOUT = True
ROUNDABOUT_MIN_BLACK_COUNT = 4

# Outer sensor boost increases steering when L2/R2 sees the line.
OUTER_TURN_GAIN = 1.1

# Limit D term spikes to reduce steering jitter at high speed.
DERIVATIVE_LIMIT = 10000

LOST_LINE_HOLD = True
LOST_LINE_SEARCH = True
SEARCH_DIRECTION_ERROR_THRESHOLD = 0.15

# Wheel trim and correction direction.
LEFT_TRIM = 1
RIGHT_TRIM = 1
TURN_DIR = 1

# Main loop and debug output.
CONTROL_DT_MS = 6
LOOP_DELAY_MS = 1
DEBUG = True
DEBUG_INTERVAL_MS = 300

# ADC filtering parameters.
# Increase these values if readings jump or adjacent channels interfere.
DUMMY_READS = 1
SETTLE_US = 100
SAMPLES_PER_CHANNEL = 2
SAMPLE_GAP_US = 40

# Black-line raw ADC thresholds.
# Many line sensors output high voltage on white/background and low voltage on black.
# With BLACK_IS_HIGH = False, a channel is black when raw <= threshold.
# Set it to True only if your module outputs higher ADC values on black.
BLACK_RAW_THRESHOLDS = {
    "adc1": 2000,
    "adc2": 2000,
    "adc3": 2000,
    "adc4": 2000,
    "adc5": 2000,
}

# Motor pin configuration.
LEFT_MOTOR_FORWARD_PIN = 14
LEFT_MOTOR_BACKWARD_PIN = 25
RIGHT_MOTOR_FORWARD_PIN = 15
RIGHT_MOTOR_BACKWARD_PIN = 13

PWM_FREQ = 1000

# Set to True if a motor turns opposite to the expected direction.
LEFT_MOTOR_REVERSE = True
RIGHT_MOTOR_REVERSE = True

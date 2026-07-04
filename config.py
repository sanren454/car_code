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
FOLLOWER_ADC_PINS = [ADC_PINS[name] for name in FOLLOWER_CHANNELS]
FOLLOWER_WEIGHTS = [-2, -1, 0, 1, 2]
FOLLOWER_THRESHOLDS = [2000, 2000, 2000, 2000, 2000]
BLACK_IS_HIGH = False
ADC_MAX_VALUE = 4095

# PD and speed parameters.
BASE_SPEED = 35	
MIN_BASE_SEED = 25
MAX_SPEED = 80
MIN_SPEED = 25
Kp = 15
Kd = 1.5
SEARCH_SPEED = 34

LOST_LINE_SEARCH = False                                              
SEARCH_DIRECTION_ERROR_THRESHOLD = 0.15
LOST_LINE_CONFIRM_MS = 400
OUTER_STABLE_RAW_DELTA = 120

# Wheel trim and correction direction.
LEFT_TRIM = 0
RIGHT_TRIM = 1
TURN_DIR = 1

# Edge handling.
EDGE_CORRECTION_GAIN = 1.05

# Main loop and debug output.
CONTROL_DT_MS = 20
LOOP_DELAY_MS = 5
DEBUG = True
DEBUG_INTERVAL_MS = 200

# ADC filtering parameters.
# Increase these values if readings jump or adjacent channels interfere.
DUMMY_READS = 2
SETTLE_US = 500
SAMPLES_PER_CHANNEL = 7
SAMPLE_GAP_US = 150

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

ADC_PINS = {
    "adc1": 27,  # far left
    "adc2": 33,  # left
    "adc3": 32,  # center
    "adc4": 35,  # right
    "adc5": 34,  # far right
}

CHANNELS = ["adc1", "adc2", "adc3", "adc4", "adc5"]

# ADC filtering. Increase these if channel-to-channel influence is still visible.
DUMMY_READS = 2
SETTLE_US = 500
SAMPLES_PER_CHANNEL = 7
SAMPLE_GAP_US = 150

# Baseline calibration. Put all sensors on white/background before starting.
CALIBRATION_TIME_MS = 1200
CALIBRATION_INTERVAL_MS = 20

# Black line is detected by baseline - current_value.
# These defaults are conservative values based on gray_sensor_data.csv.
# Increase a value if that sensor false-triggers; decrease it if detection is late.
BLACK_DELTA_THRESHOLDS = {
    "adc1": 400,
    "adc2": 400,
    "adc3": 250,
    "adc4": 250,
    "adc5": 400,
}

# Require the same decision for multiple loops before applying it.
# Set to 1 for fastest response.
CONFIRM_COUNT = 2

# Loop timing.
CONTROL_INTERVAL_MS = 20
DEBUG_PRINT = True
DEBUG_INTERVAL_MS = 200

# Motor pins: two PWM pins per motor.
# Forward pin gets PWM for forward rotation, backward pin gets PWM for reverse.
# These values are based on your motor test code.
LEFT_MOTOR_FORWARD_PIN = 15
LEFT_MOTOR_BACKWARD_PIN = 13

RIGHT_MOTOR_FORWARD_PIN = 14
RIGHT_MOTOR_BACKWARD_PIN = 25

PWM_FREQ = 1000

# Speed values are percentages: 0-100.
BASIC_SPEED = 45
SLIGHT_TURN_INNER_SPEED = 25
SLIGHT_TURN_OUTER_SPEED = 55
SHARP_TURN_SPEED = 45

# If a motor direction is reversed, change the corresponding value to True.
LEFT_MOTOR_REVERSE = False
RIGHT_MOTOR_REVERSE = False

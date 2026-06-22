from machine import ADC, Pin
import time

import config


class GraySensorArray:
    def __init__(self):
        self.adc_objects = {}
        self.baseline = {}
        self._init_adc()

    def _init_adc(self):
        print("Init gray sensor ADC channels...")
        for name in config.CHANNELS:
            pin_num = config.ADC_PINS[name]
            try:
                adc = ADC(Pin(pin_num))
                adc.atten(ADC.ATTN_11DB)
                try:
                    adc.width(ADC.WIDTH_12BIT)
                except AttributeError:
                    pass
                self.adc_objects[name] = adc
                print("{} GPIO{} ok".format(name, pin_num))
            except Exception as e:
                print("{} GPIO{} failed: {}".format(name, pin_num, e))

    def _read_channel_filtered(self, adc):
        for _ in range(config.DUMMY_READS):
            adc.read()
            time.sleep_us(config.SAMPLE_GAP_US)

        time.sleep_us(config.SETTLE_US)

        readings = []
        for _ in range(config.SAMPLES_PER_CHANNEL):
            readings.append(adc.read())
            time.sleep_us(config.SAMPLE_GAP_US)

        readings.sort()
        return readings[len(readings) // 2]

    def read_raw(self):
        values = {}
        for name in config.CHANNELS:
            adc = self.adc_objects[name]
            values[name] = self._read_channel_filtered(adc)
        return values

    def calibrate_baseline(self):
        print("")
        print("Calibrating baseline. Put all sensors on white/background.")
        totals = {name: 0 for name in config.CHANNELS}
        count = 0
        start_ms = time.ticks_ms()

        while time.ticks_diff(time.ticks_ms(), start_ms) < config.CALIBRATION_TIME_MS:
            values = self.read_raw()
            for name in config.CHANNELS:
                totals[name] += values[name]
            count += 1
            time.sleep_ms(config.CALIBRATION_INTERVAL_MS)

        for name in config.CHANNELS:
            self.baseline[name] = totals[name] // max(count, 1)

        print("Baseline:", self.baseline)
        print("")
        return self.baseline

    def read_state(self):
        if not self.baseline:
            raise RuntimeError("Call calibrate_baseline() before read_state().")

        raw = self.read_raw()
        delta = {}
        black = {}
        for name in config.CHANNELS:
            delta[name] = self.baseline[name] - raw[name]
            black[name] = delta[name] >= config.BLACK_DELTA_THRESHOLDS[name]

        return raw, delta, black


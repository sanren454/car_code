from machine import ADC, Pin
import time

import config


class GraySensorArray:
    def __init__(self):
        self.adc_objects = {}
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

    def read_state(self):
        raw = self.read_raw()
        black = {}
        for name in config.CHANNELS:
            threshold = config.BLACK_RAW_THRESHOLDS[name]
            if config.BLACK_IS_HIGH:
                black[name] = raw[name] >= threshold
            else:
                black[name] = raw[name] <= threshold

        return raw, black

from machine import ADC, Pin
import time


class GraySensorSampler:
    def __init__(self):
        self.adc_pins = {
            "adc1": 27,
            "adc2": 33,
            "adc3": 32,
            "adc4": 35,
            "adc5": 34,
        }
        self.adc_objects = {}
        self.dummy_reads = 2
        self.settle_us = 500
        self.samples_per_channel = 7
        self.sample_gap_us = 150
        self._init_adc()

    def _init_adc(self):
        print("Init ADC channels...")
        for name, pin_num in self.adc_pins.items():
            try:
                adc = ADC(Pin(pin_num))
                adc.atten(ADC.ATTN_11DB)
                try:
                    adc.width(ADC.WIDTH_12BIT)
                except AttributeError:
                    pass
                self.adc_objects[name] = adc
                print("{} (GPIO{}) init ok".format(name, pin_num))
            except Exception as e:
                print("{} (GPIO{}) init failed: {}".format(name, pin_num, e))

    def _read_channel_filtered(self, adc):
        # After ADC channel switching, discard early readings to reduce mux carry-over.
        for _ in range(self.dummy_reads):
            adc.read()
            time.sleep_us(self.sample_gap_us)

        time.sleep_us(self.settle_us)

        readings = []
        for _ in range(self.samples_per_channel):
            readings.append(adc.read())
            time.sleep_us(self.sample_gap_us)

        readings.sort()
        return readings[len(readings) // 2]

    def read_all_raw(self):
        values = {}
        for name, adc in self.adc_objects.items():
            try:
                values[name] = self._read_channel_filtered(adc)
            except Exception as e:
                print("{} read failed: {}".format(name, e))
                values[name] = -1
        return values

    def collect(self, duration_s=30, interval_ms=100):
        samples = []
        start_ms = time.ticks_ms()
        next_ms = start_ms
        sample_count = 0

        print("")
        print("Start collecting 5-channel gray sensor ADC raw values")
        print("Duration: {}s, interval: {}ms".format(duration_s, interval_ms))
        print(
            "Filter: dummy_reads={}, settle_us={}, samples_per_channel={}, median".format(
                self.dummy_reads,
                self.settle_us,
                self.samples_per_channel,
            )
        )
        print("Move or cover each sensor during collection to check curve changes")
        print("Press Ctrl+C to stop early")
        print("")

        try:
            while time.ticks_diff(time.ticks_ms(), start_ms) < duration_s * 1000:
                now_ms = time.ticks_ms()
                if time.ticks_diff(now_ms, next_ms) >= 0:
                    elapsed_ms = time.ticks_diff(now_ms, start_ms)
                    values = self.read_all_raw()
                    row = {"time_ms": elapsed_ms}
                    row.update(values)
                    samples.append(row)
                    sample_count += 1

                    print(
                        "{:>6.2f}s  adc1={:>4} adc2={:>4} adc3={:>4} adc4={:>4} adc5={:>4}".format(
                            elapsed_ms / 1000.0,
                            values.get("adc1", -1),
                            values.get("adc2", -1),
                            values.get("adc3", -1),
                            values.get("adc4", -1),
                            values.get("adc5", -1),
                        )
                    )
                    next_ms = time.ticks_add(next_ms, interval_ms)
                time.sleep_ms(1)
        except KeyboardInterrupt:
            print("")
            print("Collection stopped by user")

        print("")
        print("Collection done, {} samples".format(sample_count))
        return samples

    def save_csv(self, samples, filename="gray_sensor_data.csv"):
        headers = ["time_ms", "adc1", "adc2", "adc3", "adc4", "adc5"]
        with open(filename, "w") as f:
            f.write(",".join(headers) + "\n")
            for row in samples:
                f.write(
                    "{},{},{},{},{},{}\n".format(
                        row.get("time_ms", 0),
                        row.get("adc1", -1),
                        row.get("adc2", -1),
                        row.get("adc3", -1),
                        row.get("adc4", -1),
                        row.get("adc5", -1),
                    )
                )
        print("CSV saved on ESP32 filesystem: {}".format(filename))


def main():
    sampler = GraySensorSampler()
    samples = sampler.collect(duration_s=30, interval_ms=100)
    sampler.save_csv(samples)
    print("")
    print("Next: copy gray_sensor_data.csv to PC, then run plot_gray_adc.py to generate the chart.")


if __name__ == "__main__":
    main()

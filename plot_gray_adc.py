import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt


CHANNELS = ["adc1", "adc2", "adc3", "adc4", "adc5"]


def load_csv(csv_path):
    times = []
    channel_values = {name: [] for name in CHANNELS}

    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            times.append(float(row["time_ms"]) / 1000.0)
            for name in CHANNELS:
                channel_values[name].append(int(row[name]))

    return times, channel_values


def plot_adc(csv_path, output_path):
    times, channel_values = load_csv(csv_path)
    if not times:
        raise ValueError("CSV has no sample data")

    plt.figure(figsize=(12, 6), dpi=120)
    for name in CHANNELS:
        plt.plot(times, channel_values[name], linewidth=1.4, label=name)

    plt.title("5-Channel Gray Sensor ADC Raw Values")
    plt.xlabel("Time (s)")
    plt.ylabel("ADC Raw Value (0-4095)")
    plt.ylim(0, 4095)
    plt.grid(True, linestyle="--", alpha=0.35)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path)
    print("Image saved: {}".format(output_path))
    plt.show()


def main():
    parser = argparse.ArgumentParser(description="Plot ESP32 5-channel gray sensor ADC CSV data.")
    parser.add_argument("csv", nargs="?", default="gray_sensor_data.csv", help="CSV file exported from ESP32")
    parser.add_argument("-o", "--output", default="gray_sensor_adc_plot.png", help="Output image path")
    args = parser.parse_args()

    csv_path = Path(args.csv)
    output_path = Path(args.output)
    plot_adc(csv_path, output_path)


if __name__ == "__main__":
    main()

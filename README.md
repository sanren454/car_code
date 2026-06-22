# 五路灰度传感器 ADC 测试

## 1. ESP32-S3 采集

把 `esp32_gray_sampler.py` 上传到 ESP32，并在 Thonny 中运行。

默认配置:

- GPIO27: adc1
- GPIO33: adc2
- GPIO32: adc3
- GPIO35: adc4
- GPIO34: adc5
- 采集 30 秒
- 每 100 ms 采样一次
- 保存文件: `gray_sensor_data.csv`

需要修改采集时长或采样间隔时，改 `main()` 里的这一行:

```python
samples = sampler.collect(duration_s=30, interval_ms=100)
```

## 2. 导出数据

采集结束后，从 ESP32 文件系统下载 `gray_sensor_data.csv` 到电脑。

## 3. 电脑端画图

安装依赖:

```powershell
pip install matplotlib
```

在保存 CSV 的目录运行:

```powershell
python plot_gray_adc.py gray_sensor_data.csv -o gray_sensor_adc_plot.png
```

输出图像的横轴是时间，纵轴是 ADC 原始值，五条曲线分别对应 `adc1` 到 `adc5`。

## 4. 黑线循迹

循迹代码文件:

- `config.py`: 所有可调参数，包括 ADC 引脚、阈值、电机引脚、速度、滤波参数
- `gray_sensor.py`: 灰度传感器读取、滤波、启动基线校准、变化量判断
- `motor.py`: 左右电机正反转和 PWM 控制
- `line_follower.py`: 主循迹逻辑

使用前必须确认 `config.py` 里的电机引脚:

```python
LEFT_MOTOR_FORWARD_PIN = 15
LEFT_MOTOR_BACKWARD_PIN = 13

RIGHT_MOTOR_FORWARD_PIN = 14
RIGHT_MOTOR_BACKWARD_PIN = 25
```

运行 `line_follower.py` 前，把五路传感器都放在白底或非黑线背景上。程序启动后会先校准基线，之后用 `baseline - current_value` 的变化量判断黑线。

当前逻辑:

- `adc1` 检测到黑线: 左轮反转，右轮正转，大左转
- `adc5` 检测到黑线: 左轮正转，右轮反转，大右转
- `adc2` 检测到黑线: 两轮正转，左慢右快，小左转
- `adc4` 检测到黑线: 两轮正转，左快右慢，小右转
- `adc3` 检测到黑线: 两轮同速正转
- 五路都没有检测到黑线: 停车

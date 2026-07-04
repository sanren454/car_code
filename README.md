# 五路灰度传感器循迹

后续代码修改以本 README 为准。当前循迹程序使用五路灰度传感器、连续强度 error 和 PD 控制。

## 1. 引脚配置

原五路 ADC 引脚固定如下：

- `adc1`: GPIO27
- `adc2`: GPIO33
- `adc3`: GPIO32
- `adc4`: GPIO35
- `adc5`: GPIO34

传感器从左到右的物理顺序固定如下：

```text
adc4, adc3, adc2, adc1, adc5
```

对应逻辑名称和权重：

- `adc4`: L2，权重 -2
- `adc3`: L1，权重 -1
- `adc2`: M，权重 0
- `adc1`: R1，权重 1
- `adc5`: R2，权重 2

## 2. 主要文件

- `config.py`: ADC、电机、阈值、PD、搜线和调试参数
- `gray_sensor.py`: 五路 ADC 初始化、滤波读取、黑线判断
- `motor.py`: 左右电机 PWM 控制
- `line_follower.py`: 五路 PD 循迹主程序
- `motor_speed_test.py`: 双电机定值速度测试

## 3. 黑线判断

默认灰度传感器检测到黑线时 ADC 原始值更低：

```python
BLACK_IS_HIGH = False
```

此时某一路满足下面条件就认为检测到黑线：

```python
raw <= threshold
```

如果你的模块检测到黑线时 ADC 原始值更高，改成：

```python
BLACK_IS_HIGH = True
```

此时判断条件变为：

```python
raw >= threshold
```

当前五路阈值顺序是 `L2, L1, M, R1, R2`：

```python
FOLLOWER_THRESHOLDS = [2000, 2000, 2000, 2000, 2000]
```

`gray_sensor.py` 使用 `BLACK_RAW_THRESHOLDS` 按 ADC 名称查阈值，数值需要和上面的五路顺序保持一致。

## 4. PD 循迹

循迹程序按五路连续黑线强度计算 error，不使用固定动作表。

中路 `M` 检测到黑线时优先级最高，但不会把修正量直接清零。程序会保留上一轮 `correction` 的一小部分，让车平滑回正：

```python
CENTER_DAMPING_GAIN = 0.35
correction = last_correction * CENTER_DAMPING_GAIN
```

只有 `M` 没有检测到黑线时，才按下面的连续 error 和 PD 逻辑修正。这样 `L1/R1` 灰度变化时仍然执行原来的修正逻辑，而进入中路时不会因为修正量突变为 0 造成超调。

黑线强度映射：

```python
strength = (ADC_MAX_VALUE - raw) / ADC_MAX_VALUE
```

如果 `BLACK_IS_HIGH = True`，则映射反过来：

```python
strength = raw / ADC_MAX_VALUE
```

error 计算：

```python
error = sum(weight_i * strength_i) / sum(strength_i)
```

PD 控制：

```python
correction = Kp * error + Kd * (error - last_error)
correction = TURN_DIR * correction
left_speed = BASE_SPEED + correction
right_speed = BASE_SPEED - correction
```

五路最外侧 `L2/R2` 检测到黑线时，会用 `EDGE_CORRECTION_GAIN` 轻微加强修正。

## 5. 丢线处理

五路 `black` 全是 `0` 时，程序还会先看连续强度总和：

```python
LINE_PRESENT_STRENGTH_MIN = 0.35
```

如果当前帧不是全 4095，而是某一路还有明显黑线强度，例如 `L2=1488`，程序继续使用连续强度计算 PD，不进入丢线。

如果五路 ADC 都接近 `4095`，连续强度也会接近 0。此时当前帧已经没有足够位置信息，不能靠当前帧算出线在哪里，只能靠上一段时间的运动连续性处理。

当前策略是：正常循迹时保存最左侧 `L2` 和最右侧 `R2` 的原始值。五路全白后，先比较当前 `L2/R2` 和上一次正常循迹时的 `L2/R2` 是否基本没变：

```python
OUTER_STABLE_RAW_DELTA = 120
```

如果两侧读数变化很小，说明两边背景没有明显变化，黑线更可能卡在中间传感器缝隙里，程序会保持上一次电机输出继续向前跨过去。

但这个判断不能无限保持，因为车完全跑到白地上时两侧也可能一直不变。所以仍然保留最大确认时间：

```python
LOST_LINE_CONFIRM_MS = 250
```

如果两侧变化明显，或者全白持续超过确认时间，再按最近可靠的连续 `error` 方向搜线：

- `error < -SEARCH_DIRECTION_ERROR_THRESHOLD`: 记录为向左搜线
- `error > SEARCH_DIRECTION_ERROR_THRESHOLD`: 记录为向右搜线
- `abs(error)` 没超过阈值时保持原方向
- 启动后还没有可靠方向记录时，默认向右搜线

关闭丢线搜线：

```python
LOST_LINE_SEARCH = False
```

关闭后，丢线时左右电机输出为 `0`。

## 6. 电机控制方式

电机不是直接给固定电压控制，而是通过 ESP32 的 PWM 输出控制电机驱动板。

每个电机有两个 PWM 引脚：

- 左电机：GPIO14 前进，GPIO25 后退
- 右电机：GPIO15 前进，GPIO13 后退

`speed > 0` 时前进 PWM 有占空比、后退 PWM 为 0；`speed < 0` 时反过来。`speed` 的绝对值就是 PWM 占空比百分比，范围 `0` 到 `100`。

当前 PWM 频率：

```python
PWM_FREQ = 1000
```

也就是 1 kHz PWM。

## 7. 调试输出

`DEBUG = True` 时会按 `DEBUG_INTERVAL_MS` 打印一行调试数据，包括：

- 运行时间
- 五路 ADC 原始值
- 五路连续黑线强度
- 五路黑线判断结果
- error
- correction
- 搜线方向
- 左右电机输出

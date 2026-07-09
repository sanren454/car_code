# 五路灰度传感器循迹

当前程序使用五路灰度传感器的二值黑白判断计算 `error`，再用 PD 控制左右电机差速。电机速度采用又加又减逻辑：PD 修正量会提高一侧电机速度并降低另一侧电机速度，修正量足够大时允许一侧反转。电机死区按正负 25 处理，非零输出落在 `-25..25` 内时会补偿到 `-25` 或 `25`。不使用连续灰度强度算法，也没有中间传感器触发后的单独回正逻辑。

## 1. 传感器和引脚

ADC 引脚：

- `adc1`: GPIO27
- `adc2`: GPIO33
- `adc3`: GPIO32
- `adc4`: GPIO35
- `adc5`: GPIO34

传感器从左到右的物理顺序：

```text
adc4, adc3, adc2, adc1, adc5
```

对应逻辑名称和权重：

- `adc4`: L2，权重 `-2`
- `adc3`: L1，权重 `-1`
- `adc2`: M，权重 `0`
- `adc1`: R1，权重 `1`
- `adc5`: R2，权重 `2`

相关配置：

```python
CHANNELS = ["adc4", "adc3", "adc2", "adc1", "adc5"]
FOLLOWER_CHANNELS = ["adc4", "adc3", "adc2", "adc1", "adc5"]
FOLLOWER_SENSOR_NAMES = ["L2", "L1", "M", "R1", "R2"]
FOLLOWER_WEIGHTS = [-2, -1, 0, 1, 2]
```

## 2. 黑线判断

默认传感器检测到黑线时 ADC 原始值更低：

```python
BLACK_IS_HIGH = False
```

此时判断条件是：

```python
raw <= BLACK_RAW_THRESHOLDS[channel]
```

如果你的传感器检测到黑线时 ADC 原始值更高，改成：

```python
BLACK_IS_HIGH = True
```

此时判断条件变为：

```python
raw >= BLACK_RAW_THRESHOLDS[channel]
```

当前每路阈值：

```python
BLACK_RAW_THRESHOLDS = {
    "adc1": 2000,
    "adc2": 2000,
    "adc3": 2000,
    "adc4": 2000,
    "adc5": 2000,
}
```

## 3. 二值 error 计算

`read_sensors()` 输出五路二值状态：

```text
black_values = [L2, L1, M, R1, R2]
```

含义：

```text
1 = 黑线
0 = 白底
```

`calculate_error()` 使用二值加权平均：

```python
error = sum(weight_i * black_i) / sum(black_i)
```

例子：

```text
[0, 0, 1, 0, 0] -> error = 0
[0, 1, 0, 0, 0] -> error = -1
[0, 0, 0, 1, 0] -> error = 1
[0, 0, 0, 1, 1] -> error = 1.5
```

五路全白时：

```text
[0, 0, 0, 0, 0]
```

程序认为丢线。

## 4. PD 控制

PD 修正量：

```python
derivative = (error - last_error) / dt_s
correction = Kp * error + Kd * derivative
```

`dt_s` 来自实测控制循环间隔，`CONTROL_DT_MS` 只作为调试输出里的目标周期：

```python
elapsed_ms = time.ticks_diff(now_ms, last_control_ms)
dt_s = elapsed_ms / 1000
```

左右电机输出采用又加又减逻辑：

```python
base_speed = int(BASE_SPEED)
left_speed = base_speed + correction
right_speed = base_speed - correction

left_output = limit_output_speed(left_speed + LEFT_TRIM)
right_output = limit_output_speed(right_speed + RIGHT_TRIM)
```

这样直行时两侧接近 `BASE_SPEED`，转弯时一侧加速、另一侧减速；当修正量大于基础速度时，减速侧会变成反向输出。

五路最外侧 `L2/R2` 检测到黑线时，会用 `OUTER_TURN_GAIN` 加强修正。

急弯时会临时降低基础速度：只要 `L2/R2` 检测到黑线，PD 使用 `SHARP_TURN_SPEED` 作为基础速度；外侧灯离开黑线后继续保持 `SHARP_TURN_RELEASE_DELAY_MS`，再恢复 `BASE_SPEED`。

主要参数：

```python
BASE_SPEED = 40
MAX_SPEED = 100
MIN_SPEED = 25
SHARP_TURN_SPEED = 50
SHARP_TURN_RELEASE_DELAY_MS = 18
Kp = 13
Kd = 1.5
CONTROL_DT_MS = 6
OUTER_TURN_GAIN = 1.25
LEFT_TRIM = 0
RIGHT_TRIM = 1
TURN_DIR = 1
```

`MIN_SPEED = 25` 用于补偿电机死区：输出为 `0` 时保持停止；非零输出如果在 `-25..25` 内，会被提升到对应方向的最小有效 PWM。

## 5. 丢线处理

五路 `black_values` 全是 `0` 时，程序进入丢线判断。

正常循迹时会保存上一轮有效循迹时最外侧传感器的二值状态：

```text
last_outer_black = (L2, R2)
```

丢线时比较当前最外侧传感器的二值状态：

```text
current_outer_black = (L2, R2)
```

判断逻辑：

- 五路全白，并且最外侧 `L2/R2` 的黑白状态没有变化：轻微丢线。
- 轻微丢线时，如果 `LOST_LINE_HOLD = True`，进入 `hold`，保持上一轮电机输出。
- 五路全白，并且最外侧 `L2/R2` 的黑白状态发生变化：进入 `search`。

相关配置：

```python
LOST_LINE_HOLD = True
LOST_LINE_SEARCH = True
SEARCH_SPEED = 34
SEARCH_DIRECTION_ERROR_THRESHOLD = 0.15
```

`LOST_LINE_SEARCH = True` 时，程序会按最近一次可靠的 `error` 方向旋转搜线。改成 `False` 后，进入 `search` 会输出 `0, 0`。

## 6. 电机控制

每个电机使用两个 PWM 引脚：

- 左电机：GPIO14 前进，GPIO25 后退
- 右电机：GPIO15 前进，GPIO13 后退

`speed > 0` 时前进 PWM 有占空比，后退 PWM 为 `0`；`speed < 0` 时反过来。`speed` 的绝对值就是 PWM 占空比百分比。

当前电机配置：

```python
PWM_FREQ = 1000
LEFT_MOTOR_REVERSE = True
RIGHT_MOTOR_REVERSE = True
```

## 7. ADC 滤波参数

每一路 ADC 读取时会先丢弃若干次读数，再等待稳定，然后正式采样并取中值：

```python
DUMMY_READS = 1
SETTLE_US = 100
SAMPLES_PER_CHANNEL = 2
SAMPLE_GAP_US = 40
```

含义：

- `DUMMY_READS`: 正式采样前先读几次并丢弃
- `SETTLE_US`: 丢弃读数后等待稳定的时间，单位微秒
- `SAMPLES_PER_CHANNEL`: 每一路正式采样次数
- `SAMPLE_GAP_US`: 两次 ADC 读取之间的间隔，单位微秒

这些参数越大，读数越稳，但控制循环越慢；越小，反应越快，但读数更容易抖。

## 8. 调试输出

`DEBUG = True` 时会按 `DEBUG_INTERVAL_MS` 打印一行调试数据，包括：

- 运行时间
- 五路 ADC 原始值
- 五路二值黑白判断 `binary`
- 是否丢线 `lost`
- 最外侧黑白是否未变化 `outer_same`
- 当前模式 `mode`
- `error`
- 当前基础速度 `base`
- 配置使用的 `dt`
- 实测循环间隔 `actual_dt`
- `correction`
- 最近搜线方向 `last_side`
- 左右电机输出


# ESP32 设备 WiFi 连接配置不生效问题处理说明

## 一、 问题背景
在修改 `fishbot_config.h` 中的 WiFi 名称（SSID）和密码后，代码编译及烧录均正常通过，但设备重启后仍尝试连接旧的 WiFi 网络（`m5`），导致串口反复输出 `NO_AP_FOUND` 和 UDP 数据发送失败（`could not send data: 118`）的报错。

## 二、 根本原因分析
**ESP32 的 NVS（非易失性存储）配置优先级高于代码中的默认值。**
设备在第一次烧录运行时，会将当时的 WiFi 信息写入 NVS 配置区。在此后的每次开机中，程序都会优先从 NVS 读取配置，而代码中修改后的 `fishbot_config.h` 仅仅是改变了“出厂默认值”，**无法覆盖**已经保存在 NVS 中的旧配置。

## 三、 解决过程与操作步骤

### 步骤 1：擦除 ESP32 Flash (清空 NVS)
为了让设备丢掉旧配置，必须执行全片擦除。在 VS Code 中执行 PlatformIO 的擦除任务：

```bash
# 尝试在终端执行以下命令：
pio run --target erase
```

### 步骤 2：解决命令行报错（环境变量问题）
在执行上述命令时，PowerShell 提示 `pio : 无法将“pio”项识别为 cmdlet...`。
**原因**：PlatformIO 的虚拟环境路径未被添加到系统全局环境变量中。
**解决方案**：使用 `platformio.exe` 的绝对路径来执行擦除命令：
```powershell
C:\Users\zhq40\.platformio\penv\Scripts\platformio.exe run --target erase
```
*(注：执行此命令后，ESP32 内部的 NVS 配置区已被彻底清空。)*

### 步骤 3：重新编译并烧录
确认 `fishbot_config.h` 中的 WiFi 信息正确（需为 **2.4G** 频段），并在 VS Code 底部状态栏点击 **“→”（Upload）** 进行重新编译和烧录。

## 四、 验证结果

重新烧录后，连接串口监视器，观察到以下关键日志，证明 WiFi 问题已成功解决：
```text
17:10:59.993 > [  1424][V][WiFiGeneric.cpp:356] _arduino_event_cb(): STA Connected: SSID: HUAWEI-3TKA5K...
17:11:00.056 > [  1486][V][WiFiGeneric.cpp:370] _arduino_event_cb(): STA Got New IP:192.168.3.125
17:11:00.070 > [  1501][D][WiFiGeneric.cpp:1103] _eventCallback(): STA IP: 192.168.3.125, MASK: 255.255.255.0, GW: 192.168.3.1
```
- 成功连接到了新配置的 WiFi（`HUAWEI-3TKA5K`）。
- 成功获取到了局域网 IP 地址（`192.168.3.125`）。
- 不再出现 `NO_AP_FOUND` 及相关的 UDP 发送错误。

## 五、 遗留问题提示（待后续排查）
网络问题解决后，串口日志中仍存在硬件初始化异常，需进一步检查硬件接线：
1. **I2C 通信失败**：日志报 `i2cRead returned Error 263`。应检查 MPU6050/OLED 的 SDA(18)、SCL(19) 引脚及供电是否正常。
2. **电机参数异常**：日志显示 `init motor param 0: ... / (0 * 1078214656)`，分母为 0，可能是由于擦除 Flash 导致电机校准数据丢失，或代码初始化逻辑依赖 I2C 传感器数据。

--- 
*文档结束*
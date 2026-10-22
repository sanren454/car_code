# Micro-ROS 上位机部署学习计划

适用环境：已有 Ubuntu 22.04 实体机或双系统。依据《Micro-ROS 环境部署简要说明》整理，并参考同目录的《环境搭建env_setup.docx》。当前先部署 Ubuntu 上位机，开发板型号确认后再安排固件。

本阶段目标：ROS 2 Humble 的示例通信正常，micro-ROS Agent 能以 UDP 8888 启动并监听。以下命令供你在 Ubuntu 的 Bash 终端逐段执行；尚未在你的 Ubuntu 机器上运行验证。遇到错误先处理当前步骤，不要继续叠加安装。

## 1 学习顺序和验收标准

每次学习完成一阶段即可，时间是建议安排，可按进度调整。

| 阶段 | 建议时间 | 要理解的内容 | 实际操作 | 验收标准 |
| --- | --- | --- | --- | --- |
| 1 系统检查 | 20 分钟 | Ubuntu 版本、终端、环境变量、IP 地址 | 运行下一节的检查命令 | 确认为 22.04，知道 ROS 是否已安装 |
| 2 ROS 2 基础 | 1 至 2 小时 | 节点、话题、发布者、订阅者，source 的作用 | 安装或检查 Humble，运行 talker/listener | listener 连续收到消息 |
| 3 Agent 安装 | 1 至 2 小时，依网络和编译速度变化 | Agent 在 PC 上做什么，工作空间是什么 | 用官方 micro_ros_setup 的 humble 分支构建 Agent | 找到 micro_ros_agent 包，程序可以启动 |
| 4 网络检查 | 30 分钟 | PC IP、UDP 端口、防火墙、局域网可达性 | 启动 Agent，查看 UDP 8888 | 端口监听正常，记录上位机 IP |
| 5 复现操作 | 20 分钟 | 新终端为何需要重新加载环境 | 在新终端重新启动并验证 | 能独立复现启动过程 |

第一轮先学会节点、话题、工作空间、source、IP 和端口。DDS 内部实现、QoS 细节、TF、SLAM 和 Nav2 留到实际需要时继续学。

## 2 现在先做系统检查

在 Ubuntu 终端执行，Windows PowerShell 不适用这些命令：

```bash
cat /etc/os-release
uname -m
ls /opt/ros
printenv ROS_DISTRO
command -v ros2
ip -br -4 addr
df -h "$HOME"
```

检查方式：

- `VERSION_ID` 应为 `22.04`。
- `ls /opt/ros` 若显示 `humble`，说明有 Humble 安装目录，仍需加载后验证。
- `printenv ROS_DISTRO` 没有输出，可能仅仅是当前终端没有加载环境。
- `/opt/ros` 不存在，则进入下一节安装流程。
- 记录连接路由器的网卡 IPv4；不要把 `127.0.0.1` 或容器虚拟网卡地址当成将来的 Agent 地址。
- 确认用户目录所在磁盘有空间容纳 ROS、源码、构建产物和后续固件工具链；不要按原文中的约 1GB 当作整个环境的总预算。

这组输出是后续选择安装分支的依据。若系统已经有其他 ROS 版本，先确认现状，不要直接覆盖安装或在同一终端混用环境。

## 3 安装或验证 ROS 2 Humble

### 已经安装 Humble

```bash
source /opt/ros/humble/setup.bash
printenv ROS_DISTRO
ros2 --help
```

期望版本为 `humble`。`source` 会把 ROS 的命令和包路径加入当前终端；新开的终端需要再次执行。

### 尚未安装 Humble

按 [ROS 2 Humble 官方 Ubuntu 安装说明](https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debs.html) 完成 UTF-8 检查、Universe 仓库和 ROS 软件源配置。已有 UTF-8 中文 locale 可以保留，无需为了 ROS 改成英文桌面。

软件源配置采用官方当前的 `ros2-apt-source` 流程；不要同时添加多套来源不明的 ROS 源或重复导入旧密钥。官方网页若访问受限，可参考其 [官方源文件](https://github.com/ros2/ros2_documentation/blob/humble/source/Installation/Ubuntu-Install-Debs.rst) 及其中引用的软件源配置文件。

配置软件源后，在 Ubuntu 执行：

```bash
sudo apt update
sudo apt upgrade
sudo apt install ros-humble-desktop ros-dev-tools
source /opt/ros/humble/setup.bash
printenv ROS_DISTRO
ros2 --help
```

阅读 apt 的变更列表后再确认，尤其不要确认意外移除关键系统组件的操作。选择 Desktop 是为了后续继续使用 RViz 和官方示例。

### 做一个 ROS 通信练习

终端 A：

```bash
source /opt/ros/humble/setup.bash
ros2 run demo_nodes_cpp talker
```

终端 B：

```bash
source /opt/ros/humble/setup.bash
ros2 run demo_nodes_py listener
```

终端 C：

```bash
source /opt/ros/humble/setup.bash
ros2 node list
ros2 topic list
ros2 topic info /chatter
ros2 topic echo /chatter
```

验收：B 中持续出现收到消息的日志，C 中可以看到 `/chatter`。用 Ctrl+C 停止对应终端的程序。这个练习只验证 PC 内的 ROS 通信。

理解：talker 是发布节点，listener 是订阅节点，`/chatter` 是它们使用的话题。后续 ESP32 和 PC 同样通过话题交换数据。

## 4 安装 micro-ROS Agent

Agent 的位置在 Ubuntu。ESP32 端以后运行 micro-ROS 客户端，通过 WiFi UDP 联系 Agent，Agent 将通信接入 ROS 2。

原文提到 `apt install ros-humble-micro-ros-agent`。能否直接安装取决于配置的软件源与包是否实际可用，不能保证每台机器都有这个包。如需检查，可运行 `apt-cache policy ros-humble-micro-ros-agent`。本计划统一采用 [官方 humble 构建流程](https://github.com/micro-ROS/micro_ros_setup/tree/humble)，只走一条安装路线。

### 4.1 准备工具和 rosdep

```bash
source /opt/ros/humble/setup.bash
sudo apt update
sudo apt install build-essential cmake git python3-pip python3-rosdep python3-vcstool python3-colcon-common-extensions
```

首次使用 rosdep 才执行：

```bash
sudo rosdep init
```

如果提示已经初始化，不要重复初始化或删除配置，继续：

```bash
rosdep update
```

`rosdep` 根据 ROS 包的声明安装系统依赖；它和负责构建工作空间的 `colcon` 分工不同。

### 4.2 构建 micro_ros_setup

以下假设 `~/microros_ws` 是新建的专用工作空间。如果它已包含以前的项目，先检查内容再决定复用，不要覆盖原目录。

```bash
mkdir -p ~/microros_ws/src
cd ~/microros_ws
git clone --branch humble https://github.com/micro-ROS/micro_ros_setup.git src/micro_ros_setup
rosdep install --from-paths src --ignore-src --rosdistro humble -y
colcon build --packages-select micro_ros_setup
source install/local_setup.bash
```

学习工作空间中的四个目录：`src` 放源码，`build` 放编译中间文件，`install` 放可加载的构建结果，`log` 放日志。

### 4.3 获取并构建 Agent

仍在同一个工作空间中执行：

```bash
cd ~/microros_ws
ros2 run micro_ros_setup create_agent_ws.sh
ros2 run micro_ros_setup build_agent.sh
source install/local_setup.bash
ros2 pkg prefix micro_ros_agent
```

两个脚本分别负责准备 Agent 源码与依赖、构建 Agent。依赖下载也需要网络，第一次构建耗时较长，实际时间以机器和网络为准。

验收：构建无错误，`ros2 pkg prefix micro_ros_agent` 返回安装路径。若失败，保留终端第一处实际报错及 `log`；不要只凭最后一行 Failed 判断原因。

## 5 启动 Agent 并检查网络

### 5.1 终端 A 启动 Agent

```bash
source /opt/ros/humble/setup.bash
source ~/microros_ws/install/local_setup.bash
ros2 run micro_ros_agent micro_ros_agent udp4 --port 8888 -v6
```

- `udp4`：使用 IPv4 UDP。
- `--port 8888`：监听端口，未来 ESP32 的目标端口也填写 8888。
- `-v6`：详细日志，方便联调。

Agent 会持续运行。当前没有 ESP32 客户端时，没有会话建立日志属于正常现象。

### 5.2 终端 B 检查监听和 IP

```bash
ss -lunp 'sport = :8888'
ip -br -4 addr
sudo ufw status
```

验收：看到 UDP 8888 的监听记录，Agent 进程未退出，并记录 PC 的局域网 IP。需要核对进程时，可以用 `sudo ss -lunp 'sport = :8888'`。

如果 UFW 已启用且规则没有放行该端口，再执行：

```bash
sudo ufw allow 8888/udp
sudo ufw status
```

如果 UFW 是 inactive，无需为了本实验开启它。不要把“Agent 已启动”当作“网络已经双向打通”的证据。

未来连接 ESP32 时，先让 PC 与 ESP32 位于可互访的局域网；避免访客网络或 AP 客户端隔离。ESP32 使用其支持的 WiFi 频段，PC 可以用有线或其他频段，只要两者能互访，不要求 PC 也必须连同一个 2.4GHz SSID。

### 5.3 新终端复现

Ctrl+C 停止 Agent，打开一个新的 Ubuntu 终端，重新执行 5.1，再在另一个终端执行监听检查。先掌握手动加载环境，熟练后再按需写入自己的 shell 启动配置。

## 6 本阶段完成清单

- [ ] Ubuntu 为 22.04。
- [ ] 加载后 `ROS_DISTRO` 为 `humble`。
- [ ] talker/listener 收发成功。
- [ ] 能解释 node、topic、publisher、subscriber 的作用。
- [ ] micro_ros_setup 和 Agent 构建成功。
- [ ] 新终端加载环境后可以启动 Agent。
- [ ] Agent 运行时 UDP 8888 处于监听状态。
- [ ] 已记录未来给 ESP32 使用的上位机 IP 和端口。

做到这里，上位机的准备工作完成。ESP32 会话、话题数据、里程计准确性和电机控制尚未验证，需留到下位机联调阶段。

## 7 后续再学的内容

确认普通 ESP32 或 ESP32-S3 的具体板型后，再配置 VS Code、PlatformIO 和对应客户端工程。先发布一个简单计数话题，再验证订阅；之后再接 `/cmd_vel`、编码器和 `/odom`。双板雷达转发、TF、建图和导航依次后置。

现有 `car_code` 是 MicroPython 项目，不能直接添加 C++ micro-ROS 库后编译。固件应另建工程；更换固件前备份板上需要保留的文件和配置。

原始配套文档中有几个要留意的细节：

1. `featheresp32` 是 [Adafruit ESP32 Feather 的配置 ID](https://docs.platformio.org/en/latest/boards/espressif32/featheresp32.html)，不能一概等同于 ESP32 DevKit V1，更不能用于所有 ESP32-S3。
2. [micro_ros_platformio](https://github.com/micro-ROS/micro_ros_platformio) 支持显式设置发行版；本方案固定 Humble，后续客户端也明确配置，避免依赖上游默认值。
3. 修改固件中的默认 WiFi 值不一定覆盖已经写入 NVS 的配置。出现问题时先核对配置读写逻辑；全片擦除会同时清除其他保存数据，不作为默认部署步骤。
4. 没有底盘固件时，不应期待出现 `/odom`、`/imu` 或 `/cmd_vel`。即使后续出现 `/odom`，也还需要验证编码器、尺寸参数和数据变化是否正确。

## 8 当前第一项任务

先执行第 2 节的系统检查，把终端输出发回。确认 Humble 是否已安装，再从第 3 节对应分支继续。这样可以避免重复配置软件源或重复安装。

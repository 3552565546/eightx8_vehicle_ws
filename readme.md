# 8×8 八轮差速无人车 Gazebo 仿真项目



https://github.com/user-attachments/assets/09b9768a-9705-4520-8134-a47107acc0f9



## 1. 项目简介

本项目基于 **ROS Noetic + Gazebo** 搭建了一辆 **8×8 八轮差速驱动（Skid-Steer）无人车**：

- 将车身、8 个车轮、6 个摄像头、2 个 Kinect、1 个激光雷达等 **STL 网格（mesh）模型**导入 URDF/Xacro，完成整车建模；
- 构建了带闭合围墙与多处障碍的**城市道路仿真环境**；
- 为无人车装配 **6 个摄像头 + 2 个 Kinect + 1 个 128 线激光雷达**，实现周围感知区域全覆盖；
- 通过**键盘遥控**车辆，并使用 **rqt** 绘制行驶轨迹、纵/横向速度、横摆角速度等信息；
- 在 Gazebo 中基于 **gmapping + amcl + move_base** 实现 **SLAM 建图**与**自主导航返回起点**，并通过 RViz 显示丰富的过程信息。

## 2. 环境依赖

| 软件 | 版本 |
| ---- | ---- |
| Ubuntu | 20.04 |
| ROS | Noetic |
| Gazebo | 11 |
| Python | 3.8 |

需要安装的 ROS 功能包：

- `xacro`、`gazebo_ros`、`gazebo_plugins`、`gazebo_msgs`
- `joint_state_publisher`、`joint_state_publisher_gui`、`robot_state_publisher`
- `gmapping`（SLAM 建图）、`amcl`（蒙特卡洛定位）、`move_base`（路径规划与运动控制）、`map_server`（地图加载/保存）
- `rqt`、`rqt_graph`、`rqt_plot`、`rviz`

```bash
sudo apt-get install ros-noetic-gmapping ros-noetic-amcl ros-noetic-move-base \
  ros-noetic-map-server ros-noetic-gazebo-ros ros-noetic-gazebo-plugins \
  ros-noetic-joint-state-publisher ros-noetic-joint-state-publisher-gui \
  ros-noetic-rqt ros-noetic-rqt-graph ros-noetic-rqt-plot
```

## 3. 目录结构

```
dazuoye/
├── launch/            # 启动文件（Gazebo、SLAM、导航、建图保存等）
├── urdf/              # URDF/Xacro 模型与传感器仿真配置
├── meshes/            # 车体、车轮、摄像头、雷达等 STL 网格模型
├── worlds/            # Gazebo 世界文件（城市道路等）
├── map/               # 保存/加载的 SLAM 地图（nav.pgm / nav.yaml）
├── param/             # move_base 代价地图与局部规划器参数
├── rviz/              # RViz 配置文件
├── config/            # 关节名称等配置
├── scripts/           # 键盘控制、自动返航、运动监控等 Python 节点
└── rqt/               # rqt 截图（轨迹、速度、计算图等）
```

## 4. 车辆模型（对应要求 1：mesh 导入 URDF/Xacro）

### 4.1 模型文件组织

所有几何体均以 **STL 网格** 形式存放于 `meshes/`，并通过 Xacro 宏批量实例化：

| 文件 | 说明 |
| ---- | ---- |
| `urdf/dazuoye_main.urdf.xacro` | 总入口，`<xacro:include>` 引入所有子文件 |
| `urdf/base.urdf.xacro` | 车体 `base_link` |
| `urdf/wheels.urdf.xacro` | 8 个车轮（`wheel1`~`wheel8`），关节 `basewheel1`~`basewheel8`（continuous） |
| `urdf/rotors.urdf.xacro` | 2 个转子 |
| `urdf/cameras.urdf.xacro` | 6 个摄像头外形 mesh |
| `urdf/kinects.urdf.xacro` | 2 个 Kinect 外形 mesh |
| `urdf/leida.urdf.xacro` | 激光雷达外形 mesh |

### 4.2 差速驱动

`urdf/control.xacro` 使用 `libgazebo_ros_skid_steer_drive.so` 插件，将左右两侧各 4 个轮子作为差速驱动组，发布 `/odom` 里程计、订阅 `/cmd_vel` 速度指令，实现八轮滑移转向。

## 5. 仿真环境（对应要求 2：闭合路线 + 障碍）

世界文件：`worlds/urban_closed_course_with_walls.world`

- **闭合边界**：东、南、西、北四面围墙，形成封闭环境；
- **城市道路**：南北主干道 + 东西主干道十字交叉，含中心标线；
- **建筑物**：四个街角的楼宇（东北、西北、东南、西南）；
- **障碍物（≥4 处）**：
  1. 中央环岛（圆柱）；
  2. 施工围栏（橙色长条）；
  3. 两辆停放车辆（蓝色、红色）；
  4. 两个交通锥；
  5. 路旁路灯等附属物。

其余世界文件：`empty.world`（空世界）、`house.world`（简单室内/室外环境）。

## 6. 传感器配置（对应要求 3：感知全覆盖）

| 传感器 | 数量 | 配置文件 | 主要话题 |
| ------ | ---- | -------- | -------- |
| RGB 摄像头 | 6（`camera1`~`camera6`） | `urdf/cameras.urdf.xacro` + `urdf/camerareal.xacro` | `/cameraN/image_raw` |
| Kinect 深度相机 | 2（`kinect1`、`kinect2`） | `urdf/kinects.urdf.xacro` + `urdf/kinectreal.xacro` | `/kinectN/rgb/image_raw`、`/kinectN/depth/image_raw`、`/kinectN/depth/points` |
| 128 线激光雷达 | 1（`leida`） | `urdf/leida.urdf.xacro` + `urdf/lidarreal-128.xacro` | `/velodyne_points` |
| 2D 雷达（备用） | 1 | `urdf/lidarreal.xacro` | `/scan` |

- 6 个摄像头分别布置于车头、车尾与车身两侧，2 个 Kinect 布置于车身前/后部，128 线激光雷达安装于车顶（水平 360°、垂直 −25°~+15°），实现车辆周围感知区域全覆盖。
- 128 线雷达探测范围 0.1~300 m，水平 1024 采样、垂直 128 线。

## 7. 键盘控制与 rqt 可视化（对应要求 4）

### 7.1 键盘控制

`scripts/eightx8_keyboard_teleop.py`，向 `/cmd_vel` 发布 `geometry_msgs/Twist`：

| 按键 | 功能 |
| ---- | ---- |
| W / S | 前进 / 后退 |
| A / D | 左转 / 右转 |
| Q | 紧急停止 |
| E / C | 增加 / 减少线速度 |
| R / F | 增加 / 减少角速度 |

### 7.2 rqt 绘图

在遥控行驶过程中，分别执行：

```bash
# 行驶轨迹（X-Y 位置）
rqt_plot /odom/pose/pose/position/x:y

# 纵向速度 vx（单位 m/s）
rqt_plot /odom/twist/twist/linear/x

# 横摆角速度 ωz（单位 rad/s）
rqt_plot /odom/twist/twist/angular/z
```

绘制结果示例存放于 `rqt/`（`position.png`、`linear_v.png`、`angular_v.png`），**纵横轴含义与单位**如下：

| 图 | 横轴 | 纵轴 |
| -- | ---- | ---- |
| 轨迹图 `position.png` | 位置 x（m） | 位置 y（m） |
| 线速度图 `linear_v.png` | 时间（s） | 纵向速度 vx（m/s） |
| 角速度图 `angular_v.png` | 时间（s） | 横摆角速度 ωz（rad/s） |

### 7.3 计算图

```bash
rqt_graph
```

计算图（见 `rqt/rosgraph.png`）显示了键盘节点 `eightx8_keyboard_teleop` → `/cmd_vel` → Gazebo 差速插件 → `/odom` → gmapping/amcl 等节点的完整数据流。

## 8. 自主导航与 SLAM（对应要求 5）

- **SLAM 建图**：使用网络下载的 **gmapping** 功能包，键盘遥控（或 `slam_auto.launch` 半自动）巡游环境完成建图，并用 `map_saver` 保存地图；
- **定位**：**amcl** 自适应蒙特卡洛定位，匹配激光雷达数据与已知地图；
- **路径规划与运动控制**：**move_base** 全局/局部代价地图 + 局部规划器，实现避障与路径跟踪；
- **自主返回起点**：`scripts/auto_return_node.py` 记录起始点（2D Pose Estimate 或 tf 获取），在收到目标点（2D Nav Goal）并到达后，自动导航返回起点；
- **RViz 显示**：`rviz/nav.rviz`、`rviz/gmapping.rviz` 等配置，显示地图、代价地图、激光点云、摄像头图像、全局/局部路径、粒子等丰富过程信息。

## 9. 快速开始

```bash
# 1. 编译
cd ~/eightx8_vehicle_ws
catkin_make
source devel/setup.bash

# 2. 启动 Gazebo（城市道路环境 + 无人车模型）
roslaunch dazuoye gazebo.launch world_name:=urban_closed_course_with_walls.world

# 3. 键盘遥控建图（或使用 slam_auto.launch 半自动建图）
roslaunch dazuoye gmapping.launch
rosrun dazuoye eightx8_keyboard_teleop.py

# 4. 保存地图
roslaunch dazuoye mapsave.launch

# 5. 重新启动 Gazebo 并导航，自主返回起点
roslaunch dazuoye gazebo.launch world_name:=urban_closed_course_with_walls.world
roslaunch dazuoye nav.launch
# 在 RViz 中：先用 "2D Pose Estimate" 设置起点，再用 "2D Nav Goal" 设置目标点，
# 车辆到达目标点后由 auto_return_node 自动返回起点。
```

## 10. launch 文件说明

| 文件 | 说明 |
| ---- | ---- |
| `gazebo.launch` | 启动 Gazebo、加载世界与机器人模型 |
| `display.launch` | 仅在 RViz 中显示机器人模型与传感器 |
| `gmapping.launch` | 启动 gmapping 建图节点 |
| `slam_auto.launch` | 集成 gmapping + move_base 的半自动建图 |
| `mapsave.launch` | 调用 map_saver 保存地图 |
| `map_load.launch` | 调用 map_server 加载地图 |
| `amcl.launch` | 启动 amcl 定位节点 |
| `movebase.launch` | 启动 move_base 导航节点 |
| `nav.launch` | 集成 RViz + 地图 + amcl + move_base + 自动返航的完整导航 |

## 11. scripts 文件说明

| 文件 | 说明 |
| ---- | ---- |
| `eightx8_keyboard_teleop.py` | WASD 键盘遥控 |
| `circular_motion.py` | 圆周运动控制 |
| `auto_return_node.py` | 到达目标点后自动返回起点 |
| `wheel_speed_monitor.py` | 订阅 `/joint_states` 监控轮速 |

## 12. 常见问题

- **模型不显示 / 传感器无数据**：确认 `gazebo_ros`、`gazebo_plugins` 已安装，并执行 `source devel/setup.bash`。
- **地图坐标系漂移**：导航时确保已先用 "2D Pose Estimate" 设置初始位姿。
- **自动返航不生效**：确认 `move_base` 已正常运行（`nav.launch` 会一并启动），且起始点已成功记录。


launch文件夹：
	amcl.launch:自适应蒙特卡洛定位启动文件，用于小车定位，在nav.launch中集成；
	display.launch：在rviz中显示各项传感器信息等；
	gazebo.launch:启动gazebo，显示小车模型及世界文件；
	gmapping.launch：gmapping建图启动文件，在slam_auto.launch中集成；
	map_load.launch：加载地图启动文件；
	mapsave.launch：保存地图启动文件；
	movebase.launch：路径规划与运动控制启动文件，在nav.launch中集成；
	nav.launch：导航启动文件，集成所有导航相关的启动文件并在rviz中显示；
	slam_auto.launch：半自动建图启动文件；
map文件夹：用于存放保存的地图；
meshes文件夹：用于存放车模型的stl文件；
param文件夹：
	base_local_planner_params.yaml：定义局部规划器的行为参数；
	costmap_common_params.yaml：定义全局和局部代价地图共有的参数；
	global_costmap_params.yaml：定义全局代价地图的特定参数；
	local_costmap_params.yaml：定义局部代价地图的特定参数；
rviz文件夹：
	display.rviz：在rviz中自动加载camera等传感器配置，在display.launch使用；
	gmapping.rviz：在rviz中自动加载建图相关的配置，在gmapping.launch使用；
	nav.rviz：在rviz中自动加载导航相关配置，在nav.launch使用；
scripts文件夹：
	auto_return_node.py：自动返回起点脚本；
	circular_motion.py：圆周运动脚本；
	eightx8_keyboard_teleop.py：键盘控制脚本；
	wheel_speed_monitor.py：轮子速度监控脚本；
urdf文件夹：存放车模型，传感器仿真等文件；
world文件夹：
	empty.world：空世界；
	house.world：简单环境；
	urban_closed_course_with_walls.world：城市环境；
导航实现流程：
	1.启动gazebo.launch，显示小车和环境；
	2.启动gmapping.launch，通过键盘控制小车实现建图；或者启动slam_auto.launch，通过2D nav goal半自动建图；
	3.启动mapsave.launch，保存地图；
	4.重新启动gazebo.launch以及nav.launch，通过2D pose Estimate设置起点，通过2D nav goal设置终点，小车开始导航并实现返回起点，这一步可以在启动nav.launch的终端界面看；
	

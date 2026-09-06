#!/usr/bin/env python3
"""
八轮差速驱动机器人圆周运动控制节点
适用于ROS Noetic
控制话题：/cmd_vel (geometry_msgs/Twist)
功能：让机器人以设定的线速度和角速度做圆周运动
"""

import rospy
import math
import signal
import sys
from geometry_msgs.msg import Twist

class CircularMotionController:
    def __init__(self):
        # 初始化ROS节点
        rospy.init_node('circular_motion_controller', anonymous=True)
        
        # 创建Twist消息发布者
        self.cmd_vel_pub = rospy.Publisher('/cmd_vel', Twist, queue_size=10)
        
        # 圆周运动参数（可调节）
        self.linear_speed = rospy.get_param('~linear_speed', 0.5)     # 线速度 m/s
        self.angular_speed = rospy.get_param('~angular_speed', 0.5)   # 角速度 rad/s
        self.duration = rospy.get_param('~duration', 0)               # 运行时间，0为无限
        self.publish_rate = rospy.get_param('~publish_rate', 10)      # 发布频率 Hz
        
        # 圆周运动参数计算
        if self.angular_speed != 0:
            self.radius = self.linear_speed / abs(self.angular_speed)  # 圆周半径
            self.circumference = 2 * math.pi * self.radius             # 圆周长
            self.period = 2 * math.pi / abs(self.angular_speed)        # 周期（秒）
        
        # 控制标志
        self.is_running = True
        
        # 设置信号处理，以便Ctrl+C可以优雅退出
        signal.signal(signal.SIGINT, self.signal_handler)
        
        # 打印参数信息
        self.print_parameters()
        
    def print_parameters(self):
        """打印当前圆周运动参数"""
        print("\n" + "="*60)
        print("八轮差速驱动机器人圆周运动控制")
        print("="*60)
        print(f"线速度: {self.linear_speed:.2f} m/s")
        print(f"角速度: {self.angular_speed:.2f} rad/s")
        
        if self.angular_speed != 0:
            print(f"圆周半径: {self.radius:.2f} m")
            print(f"圆周长: {self.circumference:.2f} m")
            print(f"运动周期: {self.period:.2f} 秒")
            print(f"旋转方向: {'逆时针' if self.angular_speed > 0 else '顺时针'}")
        else:
            print("警告: 角速度为0，将做直线运动")
        
        if self.duration > 0:
            print(f"运行时间: {self.duration} 秒")
        else:
            print("运行时间: 无限 (按Ctrl+C停止)")
        
        print(f"发布频率: {self.publish_rate} Hz")
        print("="*60 + "\n")
        
    def signal_handler(self, sig, frame):
        """处理Ctrl+C信号"""
        print("\n\n检测到Ctrl+C，正在停止圆周运动...")
        self.is_running = False
        sys.exit(0)
        
    def calculate_circular_motion(self):
        """计算圆周运动的Twist消息"""
        twist_msg = Twist()
        
        # 设置线速度（x方向）
        twist_msg.linear.x = self.linear_speed
        twist_msg.linear.y = 0.0
        twist_msg.linear.z = 0.0
        
        # 设置角速度（绕z轴旋转）
        twist_msg.angular.x = 0.0
        twist_msg.angular.y = 0.0
        twist_msg.angular.z = self.angular_speed
        
        return twist_msg
    
    def run(self):
        """执行圆周运动"""
        rate = rospy.Rate(self.publish_rate)
        
        # 等待一段时间，确保所有连接建立
        rospy.sleep(1.0)
        
        print("开始圆周运动...")
        
        start_time = rospy.Time.now().to_sec()
        iteration = 0
        
        try:
            while not rospy.is_shutdown() and self.is_running:
                # 检查是否达到运行时间限制
                if self.duration > 0:
                    current_time = rospy.Time.now().to_sec()
                    elapsed = current_time - start_time
                    
                    if elapsed >= self.duration:
                        print(f"\n达到运行时间限制 ({self.duration} 秒)，停止运动。")
                        break
                
                # 计算并发布圆周运动指令
                twist_msg = self.calculate_circular_motion()
                self.cmd_vel_pub.publish(twist_msg)
                
                # 每10次迭代打印一次状态
                if iteration % 10 == 0:
                    elapsed_time = rospy.Time.now().to_sec() - start_time
                    if self.angular_speed != 0:
                        revolutions = elapsed_time / self.period
                        distance = self.linear_speed * elapsed_time
                        print(f"已运行: {elapsed_time:.1f}秒 | 距离: {distance:.1f}m | 圈数: {revolutions:.2f}")
                
                iteration += 1
                rate.sleep()
                
        except Exception as e:
            rospy.logerr(f"圆周运动控制错误: {e}")
        finally:
            self.stop_robot()
            
    def stop_robot(self):
        """停止机器人"""
        print("\n停止机器人...")
        
        # 发布停止指令
        stop_twist = Twist()
        stop_twist.linear.x = 0.0
        stop_twist.angular.z = 0.0
        
        # 连续发布几次确保机器人停止
        for i in range(5):
            self.cmd_vel_pub.publish(stop_twist)
            rospy.sleep(0.1)
            
        print("机器人已完全停止。")
        
    def interactive_mode(self):
        """交互式模式：允许用户动态调整参数"""
        print("\n进入交互式圆周运动模式")
        print("可用命令:")
        print("  s - 显示当前参数")
        print("  v [值] - 设置线速度 (例如: v 0.8)")
        print("  w [值] - 设置角速度 (例如: w 0.6)")
        print("  r [值] - 设置圆周半径 (例如: r 1.0)")
        print("  t [值] - 设置运行时间秒数 (0为无限)")
        print("  g - 开始/继续圆周运动")
        print("  p - 暂停运动")
        print("  q - 退出")
        
        self.is_running = False
        
        while not rospy.is_shutdown():
            try:
                user_input = input("\n输入命令: ").strip().split()
                
                if not user_input:
                    continue
                    
                command = user_input[0].lower()
                
                if command == 's':
                    self.print_parameters()
                    
                elif command == 'v' and len(user_input) > 1:
                    try:
                        new_speed = float(user_input[1])
                        if new_speed >= 0:
                            self.linear_speed = new_speed
                            if self.angular_speed != 0:
                                self.radius = self.linear_speed / abs(self.angular_speed)
                                self.circumference = 2 * math.pi * self.radius
                            print(f"线速度已设置为: {self.linear_speed} m/s")
                        else:
                            print("错误: 线速度不能为负数")
                    except ValueError:
                        print("错误: 请输入有效的数字")
                        
                elif command == 'w' and len(user_input) > 1:
                    try:
                        new_angular = float(user_input[1])
                        self.angular_speed = new_angular
                        if self.angular_speed != 0:
                            self.radius = self.linear_speed / abs(self.angular_speed)
                            self.circumference = 2 * math.pi * self.radius
                            self.period = 2 * math.pi / abs(self.angular_speed)
                        print(f"角速度已设置为: {self.angular_speed} rad/s")
                        print(f"旋转方向: {'逆时针' if self.angular_speed > 0 else '顺时针'}")
                    except ValueError:
                        print("错误: 请输入有效的数字")
                        
                elif command == 'r' and len(user_input) > 1:
                    try:
                        new_radius = float(user_input[1])
                        if new_radius > 0:
                            # 保持线速度不变，调整角速度以达到目标半径
                            if self.linear_speed > 0:
                                self.angular_speed = self.linear_speed / new_radius
                                self.radius = new_radius
                                self.circumference = 2 * math.pi * self.radius
                                self.period = 2 * math.pi / abs(self.angular_speed)
                                print(f"圆周半径已设置为: {self.radius} m")
                                print(f"角速度自动调整为: {self.angular_speed} rad/s")
                            else:
                                print("错误: 线速度必须大于0才能设置半径")
                        else:
                            print("错误: 半径必须为正数")
                    except ValueError:
                        print("错误: 请输入有效的数字")
                        
                elif command == 't' and len(user_input) > 1:
                    try:
                        new_duration = float(user_input[1])
                        if new_duration >= 0:
                            self.duration = new_duration
                            print(f"运行时间已设置为: {self.duration} 秒")
                        else:
                            print("错误: 时间不能为负数")
                    except ValueError:
                        print("错误: 请输入有效的数字")
                        
                elif command == 'g':
                    print("开始圆周运动...")
                    self.is_running = True
                    self.run_duration()
                    
                elif command == 'p':
                    print("暂停圆周运动...")
                    self.is_running = False
                    self.stop_robot()
                    
                elif command == 'q':
                    print("退出交互模式...")
                    self.stop_robot()
                    break
                    
                else:
                    print("未知命令，请重试")
                    
            except EOFError:
                break
            except Exception as e:
                print(f"命令执行错误: {e}")
                
    def run_duration(self):
        """运行指定时间的圆周运动"""
        if self.duration > 0:
            print(f"开始 {self.duration} 秒的圆周运动...")
            self.run()
        else:
            # 无限运行，直到用户中断
            print("开始无限圆周运动 (按Ctrl+C停止)...")
            self.run()

def main():
    """主函数"""
    print("="*60)
    print("八轮差速驱动机器人圆周运动控制脚本")
    print("="*60)
    print("使用方式:")
    print("  1. 直接运行: rosrun dazuoye circular_motion.py")
    print("  2. 带参数运行: rosrun dazuoye circular_motion.py _linear_speed:=0.6 _angular_speed:=0.4")
    print("  3. 交互模式: rosrun dazuoye circular_motion.py _interactive:=true")
    print("="*60)
    
    # 检查是否启用交互模式
    interactive_mode = rospy.get_param('~interactive', False)
    
    try:
        controller = CircularMotionController()
        
        if interactive_mode:
            controller.interactive_mode()
        else:
            controller.run()
            
    except rospy.ROSInterruptException:
        print("ROS中断，停止圆周运动")
    except Exception as e:
        print(f"脚本运行错误: {e}")

if __name__ == '__main__':
    main()

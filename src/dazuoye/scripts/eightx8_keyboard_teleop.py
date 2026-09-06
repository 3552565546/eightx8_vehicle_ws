#!/usr/bin/env python3
"""
自定义八轮差速驱动机器人键盘控制节点
适用于ROS Noetic
控制话题：/cmd_vel (geometry_msgs/Twist)
键位布局：WASD
"""

import rospy
import sys
import select
import termios
import tty
from geometry_msgs.msg import Twist

class EightX8KeyboardTeleop:
    def __init__(self):
        # 初始化ROS节点
        rospy.init_node('eightx8_keyboard_teleop', anonymous=True)
        
        # 创建Twist消息发布者
        self.cmd_vel_pub = rospy.Publisher('/cmd_vel', Twist, queue_size=10)
        
        # 控制参数 - 可动态调节
        self.linear_speed = rospy.get_param('~linear_speed', 2.0)  # 默认线速度 0.5 m/s
        self.angular_speed = rospy.get_param('~angular_speed', 4.0)  # 默认角速度 1.0 rad/s
        self.speed_step = rospy.get_param('~speed_step', 0.1)  # 速度调节步长
        
        # 终端设置
        self.settings = termios.tcgetattr(sys.stdin)
        
        # 当前运动状态
        self.current_twist = Twist()
        self.status = 0
        
        rospy.on_shutdown(self.cleanup)
        
    def get_key(self):
        """非阻塞方式获取单个按键"""
        tty.setraw(sys.stdin.fileno())
        rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
        if rlist:
            key = sys.stdin.read(1)
        else:
            key = ''
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
        return key
    
    def print_controls(self):
        """显示控制说明"""
        controls = """
==========================================
    八轮差速驱动机器人键盘控制 (WASD布局)
==========================================
运动控制：
    W : 前进     (线速度 +{:.1f} m/s)
    S : 后退     (线速度 -{:.1f} m/s)
    A : 左转     (角速度 +{:.1f} rad/s)
    D : 右转     (角速度 -{:.1f} rad/s)
    Q : 紧急停止

速度调节：
    E : 增加线速度 (+{:.1f} m/s)
    C : 减少线速度 (-{:.1f} m/s)
    R : 增加角速度 (+{:.1f} rad/s)
    F : 减少角速度 (-{:.1f} rad/s)

状态显示：
    当前线速度: {:.1f} m/s
    当前角速度: {:.1f} rad/s
    按 Ctrl+C 退出
==========================================
""".format(self.linear_speed, self.linear_speed, 
           self.angular_speed, self.angular_speed,
           self.speed_step, self.speed_step,
           self.speed_step, self.speed_step,
           self.current_twist.linear.x, self.current_twist.angular.z)
        print(controls)
    
    def update_status(self):
        """更新状态显示（简洁版）"""
        if self.status % 10 == 0:  # 每10次更新显示一次完整控制说明
            print("\033[2J\033[H")  # 清屏
            self.print_controls()
        
        # 显示实时速度状态
        status_line = "指令: 线速度={:5.1f} m/s, 角速度={:5.1f} rad/s".format(
            self.current_twist.linear.x, self.current_twist.angular.z)
        print(f"\r{status_line}", end='', flush=True)
        self.status += 1
    
    def run(self):
        """主控制循环"""
        print("\033[2J\033[H")  # 清屏
        self.print_controls()
        
        try:
            while not rospy.is_shutdown():
                key = self.get_key()
                
                if key == '':
                    # 没有按键，继续发布当前指令（保持运动）
                    pass
                
                # ===== 运动控制 =====
                elif key == 'w' or key == 'W':  # 前进
                    self.current_twist.linear.x = self.linear_speed
                    self.current_twist.angular.z = 0.0
                elif key == 's' or key == 'S':  # 后退
                    self.current_twist.linear.x = -self.linear_speed
                    self.current_twist.angular.z = 0.0
                elif key == 'a' or key == 'A':  # 左转
                    self.current_twist.linear.x = 0.0
                    self.current_twist.angular.z = self.angular_speed
                elif key == 'd' or key == 'D':  # 右转
                    self.current_twist.linear.x = 0.0
                    self.current_twist.angular.z = -self.angular_speed
                elif key == 'q' or key == 'Q':  # 停止
                    self.current_twist.linear.x = 0.0
                    self.current_twist.angular.z = 0.0
                
                # ===== 速度调节 =====
                elif key == 'e' or key == 'E':  # 增加线速度
                    self.linear_speed += self.speed_step
                    print(f"\n线速度增加至: {self.linear_speed:.1f} m/s")
                elif key == 'c' or key == 'C':  # 减少线速度
                    if self.linear_speed > self.speed_step:
                        self.linear_speed -= self.speed_step
                    print(f"\n线速度减少至: {self.linear_speed:.1f} m/s")
                elif key == 'r' or key == 'R':  # 增加角速度
                    self.angular_speed += self.speed_step
                    print(f"\n角速度增加至: {self.angular_speed:.1f} rad/s")
                elif key == 'f' or key == 'F':  # 减少角速度
                    if self.angular_speed > self.speed_step:
                        self.angular_speed -= self.speed_step
                    print(f"\n角速度减少至: {self.angular_speed:.1f} rad/s")
                
                # ===== 退出 =====
                elif key == '\x03':  # Ctrl+C
                    break
                else:
                    # 忽略其他按键
                    continue
                
                # 发布控制指令
                self.cmd_vel_pub.publish(self.current_twist)
                
                # 更新状态显示
                self.update_status()
                
        except Exception as e:
            rospy.logerr(f"控制循环错误: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """清理资源"""
        # 发布停止指令
        stop_twist = Twist()
        stop_twist.linear.x = 0.0
        stop_twist.angular.z = 0.0
        self.cmd_vel_pub.publish(stop_twist)
        
        # 恢复终端设置
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
        print("\n\n控制节点已关闭，机器人已停止。")

def main():
    try:
        controller = EightX8KeyboardTeleop()
        controller.run()
    except rospy.ROSInterruptException:
        pass

if __name__ == '__main__':
    main()

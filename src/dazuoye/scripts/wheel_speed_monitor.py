#!/usr/bin/env python3
import rospy
from sensor_msgs.msg import JointState

def joint_callback(msg):
    if msg.velocity:  # 确保有速度数据
        print("轮子速度 (rad/s):")
        for i, name in enumerate(msg.name):
            if 'wheel' in name:  # 只显示轮子
                print(f"  {name}: {msg.velocity[i]:+.4f}")
        print("-"*30)

rospy.init_node('wheel_speed_monitor')
rospy.Subscriber("/joint_states", JointState, joint_callback)
rospy.spin()

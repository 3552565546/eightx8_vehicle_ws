#!/usr/bin/env python
# file: auto_return_node.py

import rospy
import actionlib
import tf
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal
from std_msgs.msg import String

class AutoReturnNode:
    def __init__(self):
        rospy.init_node('auto_return_node')
        
        # 存储起始位置
        self.start_pose = None
        self.target_pose = None
        self.is_navigating = False
        self.return_mode = False  # 是否为返回模式
        
        # 订阅RViz的目标点
        rospy.Subscriber('/move_base_simple/goal', PoseStamped, 
                        self.goal_callback, queue_size=1)
        
        # 订阅初始位置（从RViz的2D Pose Estimate）
        rospy.Subscriber('/initialpose', PoseWithCovarianceStamped,
                        self.initialpose_callback, queue_size=1)
        
        # 发布状态信息
        self.status_pub = rospy.Publisher('/auto_return/status', String, queue_size=10)
        
        # move_base客户端
        self.move_base = actionlib.SimpleActionClient('move_base', MoveBaseAction)
        rospy.loginfo("等待move_base服务器...")
        self.move_base.wait_for_server(rospy.Duration(5.0))
        
        rospy.loginfo("自动返回节点已启动!")
        rospy.loginfo("请先在RViz中设置初始位置（2D Pose Estimate）")
        rospy.loginfo("然后在RViz中设置目标点（2D Nav Goal）")
        rospy.loginfo("机器人到达目标点后将自动返回起点")
        
        # 如果没有从RViz获取初始位置，尝试从tf获取当前位置
        if self.start_pose is None:
            rospy.Timer(rospy.Duration(1.0), self.try_get_start_pose)
        
        rospy.spin()
    
    def initialpose_callback(self, msg):
        """记录RViz中设置的初始位置"""
        if self.start_pose is None:
            self.start_pose = msg.pose.pose
            rospy.loginfo("✅ 起始位置已记录: x=%.2f, y=%.2f", 
                         self.start_pose.position.x,
                         self.start_pose.position.y)
            self.publish_status("start_recorded")
    
    def try_get_start_pose(self, event):
        """尝试从tf获取当前位置作为起始位置"""
        if self.start_pose is not None:
            return
            
        try:
            listener = tf.TransformListener()
            listener.waitForTransform('/map', '/base_footprint', 
                                     rospy.Time(), rospy.Duration(0.1))
            (trans, rot) = listener.lookupTransform('/map', '/base_footprint', 
                                                   rospy.Time(0))
            
            from geometry_msgs.msg import Pose
            self.start_pose = Pose()
            self.start_pose.position.x = trans[0]
            self.start_pose.position.y = trans[1]
            self.start_pose.position.z = trans[2]
            self.start_pose.orientation.x = rot[0]
            self.start_pose.orientation.y = rot[1]
            self.start_pose.orientation.z = rot[2]
            self.start_pose.orientation.w = rot[3]
            
            rospy.loginfo("📍 从当前位置记录为起始点: x=%.2f, y=%.2f", 
                         self.start_pose.position.x,
                         self.start_pose.position.y)
            self.publish_status("start_recorded_from_tf")
        except:
            pass
    
    def goal_callback(self, msg):
        """接收到RViz的目标点"""
        if self.is_navigating:
            rospy.logwarn("正在导航中，忽略新目标点")
            return
        
        if self.start_pose is None:
            rospy.logwarn("⚠️ 未设置起始位置，请先在RViz中设置2D Pose Estimate")
            return
        
        self.target_pose = msg.pose
        rospy.loginfo("🎯 收到目标点: x=%.2f, y=%.2f", 
                     self.target_pose.position.x,
                     self.target_pose.position.y)
        
        # 开始前往目标点
        self.go_to_target()
    
    def go_to_target(self):
        """导航到目标点"""
        self.is_navigating = True
        self.return_mode = False
        rospy.loginfo("🚀 开始前往目标点...")
        self.publish_status("going_to_target")
        
        # 发送目标点
        goal = MoveBaseGoal()
        goal.target_pose.header.frame_id = "map"
        goal.target_pose.header.stamp = rospy.Time.now()
        goal.target_pose.pose = self.target_pose
        
        self.move_base.send_goal(goal)
        
        # 设置完成回调
        self.move_base.wait_for_result()
        
        # 检查结果
        state = self.move_base.get_state()
        
        if state == actionlib.GoalStatus.SUCCEEDED:
            rospy.loginfo("✅ 到达目标点!")
            self.publish_status("target_reached")
            
            # 等待2秒，然后返回起点
            rospy.sleep(2.0)
            self.return_to_start()
        else:
            rospy.logwarn("❌ 无法到达目标点")
            self.publish_status("target_failed")
            self.is_navigating = False
    
    def return_to_start(self):
        """返回起始点"""
        self.return_mode = True
        rospy.loginfo("🔙 开始返回起始点...")
        self.publish_status("returning_to_start")
        
        # 发送起始点作为目标
        goal = MoveBaseGoal()
        goal.target_pose.header.frame_id = "map"
        goal.target_pose.header.stamp = rospy.Time.now()
        goal.target_pose.pose = self.start_pose
        
        self.move_base.send_goal(goal)
        
        # 等待结果
        self.move_base.wait_for_result()
        
        # 检查结果
        state = self.move_base.get_state()
        
        if state == actionlib.GoalStatus.SUCCEEDED:
            rospy.loginfo("🎉 成功返回起始点!")
            self.publish_status("return_completed")
        else:
            rospy.logwarn("⚠️ 返回起始点失败")
            self.publish_status("return_failed")
        
        self.is_navigating = False
        self.return_mode = False
    
    def publish_status(self, status):
        """发布状态信息"""
        msg = String()
        msg.data = status
        self.status_pub.publish(msg)

if __name__ == '__main__':
    try:
        AutoReturnNode()
    except rospy.ROSInterruptException:
        rospy.loginfo("节点已关闭")

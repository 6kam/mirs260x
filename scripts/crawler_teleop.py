#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
from geometry_msgs.msg import Twist

class TankTeleop(Node):
    def __init__(self):
        super().__init__('tank_teleop')
        
        # パラメータの宣言
        self.declare_parameter('axis_left', 1)      # 左スティック縦
        self.declare_parameter('axis_right', 3)     # 右スティック縦
        self.declare_parameter('enable_button', 9)  # L1ボタン
        self.declare_parameter('scale_linear', 0.5)
        self.declare_parameter('scale_angular', 1.0)
        
        # パブリッシャとサブスクライバ
        self.publisher_ = self.create_publisher(Twist, 'cmd_vel', 10)
        self.subscription = self.create_subscription(
            Joy,
            'joy',
            self.joy_callback,
            10)
            
    def joy_callback(self, msg):
        # パラメータの取得
        axis_left = self.get_parameter('axis_left').value
        axis_right = self.get_parameter('axis_right').value
        enable_button = self.get_parameter('enable_button').value
        scale_linear = self.get_parameter('scale_linear').value
        scale_angular = self.get_parameter('scale_angular').value
        
        # --- 詳細デバッグログ ---
        self.get_logger().info(f'Axes: {[f"{a:.2f}" for a in msg.axes]}, Buttons: {msg.buttons}')
        # ----------------------

        twist = Twist()
        
        # 有効化ボタンの判定（デバッグのため一時的に常にTrue）
        is_enabled = True
        # if len(msg.buttons) > enable_button:
        #     if msg.buttons[enable_button] == 1:
        #         is_enabled = True
        
        if is_enabled:
            if len(msg.axes) > max(axis_left, axis_right):
                v_l = msg.axes[axis_left]
                v_r = msg.axes[axis_right]
                
                twist.linear.x = ((v_l + v_r) / 2.0) * scale_linear
                twist.angular.z = ((v_r - v_l) / 2.0) * scale_angular
                
                self.get_logger().info(f'Enabled(BTN {enable_button}) -> Linear: {twist.linear.x:.2f}, Angular: {twist.angular.z:.2f}')
            else:
                self.get_logger().warn(f'Axis index error! Need max {max(axis_left, axis_right)}, but got {len(msg.axes)}')
        
        self.publisher_.publish(twist)

def main(args=None):
    rclpy.init(args=args)
    tank_teleop = TankTeleop()
    try:
        rclpy.spin(tank_teleop)
    except KeyboardInterrupt:
        pass
    finally:
        tank_teleop.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()

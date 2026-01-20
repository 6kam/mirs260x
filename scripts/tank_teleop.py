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
        self.declare_parameter('axis_right', 4)     # 右スティック縦
        self.declare_parameter('enable_button', 10)  # L1ボタン
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
        
        twist = Twist()
        
        # デバッグログ: ボタンと軸の入力を表示
        if len(msg.buttons) > enable_button:
            enable_val = msg.buttons[enable_button]
            # self.get_logger().info(f'Enable Button({enable_button}): {enable_val}, Axes: {msg.axes}')
        else:
            self.get_logger().warn(f'Button index {enable_button} out of range! Max: {len(msg.buttons)-1}')
            return

        # 有効化ボタン（L1）が押されているか確認
        if msg.buttons[enable_button] == 1:
            # スティック入力の取得 (-1.0 ～ 1.0)
            if len(msg.axes) > axis_right:
                v_l = msg.axes[axis_left]
                v_r = msg.axes[axis_right]
                
                # タンクドライブから Twist (linear.x, angular.z) への変換
                twist.linear.x = ((v_l + v_r) / 2.0) * scale_linear
                twist.angular.z = ((v_r - v_l) / 2.0) * scale_angular
                
                self.get_logger().info(f'Publishing: Linear={twist.linear.x:.2f}, Angular={twist.angular.z:.2f}')
            else:
                self.get_logger().warn(f'Axis index out of range! Left:{axis_left}, Right:{axis_right}, Max:{len(msg.axes)-1}')
        else:
            # L1が押されていないときはログを間引いて出すか、停止コマンドを送る
            pass
            
        self.publisher_.publish(twist)

def main(args=None):
    rclpy.init(args=args)
    tank_teleop = TankTeleop()
    rclpy.spin(tank_teleop)
    tank_teleop.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

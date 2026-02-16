#動作しません。要修正
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    pkg_share = get_package_share_directory('mirs')
    config_file = os.path.join(pkg_share, 'config', 'joystick.yaml')

    return LaunchDescription([
        Node(
            package='joy',
            executable='joy_node',
            name='joy_node',
            parameters=[{
                'dev': '/dev/input/js0',
                'deadzone': 0.1,
                'autorepeat_rate': 20.0,
            }]
        ),
        Node(
            package='mirs',
            executable='crawler_teleop.py',
            name='crawler_teleop_node',
            parameters=[config_file],
        )
    ])

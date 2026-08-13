import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.substitutions import Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

def generate_launch_description():
    package_name = 'mirs'
    urdf_file_name = 'mirs_2.urdf'

    # URDFファイルのパスを取得
    urdf_path = os.path.join(
        get_package_share_directory(package_name),
        'urdf',
        urdf_file_name)

    robot_desc = ParameterValue(Command(['xacro ', urdf_path]), value_type=str)

    return LaunchDescription([
        # Robot State Publisherノードを起動
        # ここでURDFの中身をパラメータとして渡すことが最も重要です
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='screen',
            parameters=[{'robot_description': robot_desc}],
        ),
        
        Node(
            package='joint_state_publisher_gui',
            executable='joint_state_publisher_gui',
            name='joint_state_publisher_gui',
            parameters=[{'robot_description': robot_desc}]
        ),

        # (オプション) RViz2 (可視化ツール) の起動
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            output='screen',
        ),
    ])

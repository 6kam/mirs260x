import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    # パッケージ名とURDFファイル名を指定
    package_name = 'mirs_description'
    urdf_file_name = 'mirs.urdf'

    # URDFファイルのパスを取得
    urdf_path = os.path.join(
        get_package_share_directory(package_name),
        'urdf',
        urdf_file_name)

    # URDFファイルの中身を読み込む
    with open(urdf_path, 'r') as infp:
        robot_desc = infp.read()

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
        
        # (オプション) Joint State Publisher (タイヤを動かすGUIを表示する場合)
        Node(
            package='joint_state_publisher_gui',
            executable='joint_state_publisher_gui',
            name='joint_state_publisher_gui',
        ),

        # (オプション) RViz2 (可視化ツール) の起動
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            output='screen',
        ),
    ])

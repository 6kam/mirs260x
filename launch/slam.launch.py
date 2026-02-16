import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():

    # パッケージの 'share' ディレクトリへのパスを取得
    mirs_share_dir = get_package_share_directory('mirs')

    # --- 1. mirs.launch.py（ハードウェア起動）のインクルード ---
    mirs_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(mirs_share_dir, 'launch', 'mirs.launch.py')
        ),
        launch_arguments={'use_ekf_global': 'false'}.items()
    )
    
    use_rviz = DeclareLaunchArgument(
        'use_rviz',
        default_value='true',
        description='Whether to start RViz'
    )

    # --- 2. SLAM (slam_toolbox) の設定 ---
    slam_config_file = LaunchConfiguration('slam_config_file')
    declare_arg_slam_config_file = DeclareLaunchArgument(
        'slam_config_file',
        default_value=os.path.join(
            mirs_share_dir,
            'config',
            'slam_toolbox_config.yaml')
    )

    # slam_toolbox ノードの定義
    slam_node = Node(
        package='slam_toolbox', 
        executable='async_slam_toolbox_node',
        output='screen',
        parameters=[
            slam_config_file,
            {'use_sim_time': False}
        ],
    )

    # --- 3. Rviz の設定 ---
    rviz2_file = LaunchConfiguration('rviz2_file')
    declare_arg_rviz2_config_path = DeclareLaunchArgument(
        'rviz2_file', 
        default_value=os.path.join(
            mirs_share_dir,
            'rviz',
            'default.rviz')
    )

    # Rviz ノードの定義
    rviz2_node = Node(
        name='rviz2',
        package='rviz2', 
        executable='rviz2', 
        output='screen',
        arguments=['-d', rviz2_file],
        parameters=[
            {'use_sim_time': False}
        ],
        condition=IfCondition(LaunchConfiguration('use_rviz'))
    )

    # --- 4. 起動するノードをリスト化 ---
    ld = LaunchDescription()
    
    # 引数の宣言を追加
    ld.add_action(declare_arg_slam_config_file)
    ld.add_action(declare_arg_rviz2_config_path)
    ld.add_action(use_rviz)

    # 起動するノードを追加
    ld.add_action(mirs_launch)   # T1 の役割
    ld.add_action(slam_node)     # T2 の役割
    ld.add_action(rviz2_node)    # T3 の役割

    return ld

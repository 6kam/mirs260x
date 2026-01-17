import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():

    # パッケージの 'share' ディレクトリへのパスを取得
    mirs_share_dir = get_package_share_directory('mirs')

    # --- 1. mirs.launch.py（ハードウェア起動）のインクルード ---
    # mirs.launch.py をインクルードする設定
    # これで odometry, micro_ros_agent, lidar, 正しいTF が起動する
    mirs_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(mirs_share_dir, 'launch', 'mirs.launch.py')
        )
    )

    # --- 2. SLAM (slam_toolbox) の設定 ---
    # slam_toolbox の設定ファイルへのパス
    slam_config_file = LaunchConfiguration('slam_config_file')
    declare_arg_slam_config_file = DeclareLaunchArgument(
        'slam_config_file',
        # install フォルダではなく、src フォルダのファイルを直接指定する
        default_value=os.path.join(
            '/home/sawara/mirs_ws/src/mirs_mg5/mirs/config', # あなたの環境の絶対パス
            'slam_toolbox_config.yaml'),
        description='The full path to the config file for SLAM')

    # slam_toolbox ノードの定義
    slam_node = Node(
        package='slam_toolbox', 
        executable='async_slam_toolbox_node',
        output='screen',
        parameters=[
            slam_config_file,
            {'use_sim_time': False} # 実時間で動作させる
        ],
    )

    # --- 3. Rviz の設定 ---
    # Rviz の設定ファイルへのパス
    rviz2_file = LaunchConfiguration('rviz2_file')
    declare_arg_rviz2_config_path = DeclareLaunchArgument(
        'rviz2_file', 
        default_value=os.path.join(
            mirs_share_dir, # install フォルダの .rviz を使う
            'rviz',
            'default.rviz'),
        description='The full path to the rviz file'
    )

    # Rviz ノードの定義
    rviz2_node = Node(
        name='rviz2',
        package='rviz2', 
        executable='rviz2', 
        output='screen',
        arguments=['-d', rviz2_file],
        parameters=[
            {'use_sim_time': False} # 実時間で動作させる
        ],
    )

    # --- 4. 起動するノードをリスト化 ---
    ld = LaunchDescription()
    
    # 引数の宣言を追加
    ld.add_action(declare_arg_slam_config_file)
    ld.add_action(declare_arg_rviz2_config_path)

    # 起動するノードを追加
    ld.add_action(mirs_launch)   # T1 の役割
    ld.add_action(slam_node)     # T2 の役割
    ld.add_action(rviz2_node)    # T3 の役割

    return ld

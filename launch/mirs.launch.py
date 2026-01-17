import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    # パッケージのインストールディレクトリを取得 (推奨される方法)
    # これを使うには CMakeLists.txt で config フォルダが install されている必要があります
    pkg_share = get_package_share_directory('mirs')

    # --- 引数の定義 ---
    esp_port = DeclareLaunchArgument(
        'esp_port', default_value='/dev/ttyUSB1',
        description='Set esp32 usb port.')
    
    lidar_port = DeclareLaunchArgument(
        'lidar_port', default_value='/dev/ttyUSB0',
        description='Set lidar usb port.')

    use_sim_time = DeclareLaunchArgument(
        'use_sim_time', default_value='false',
        description='Use simulated clock if true')
    
    # --- 設定ファイルのパス ---
    # 既存の設定ファイル
    config_file_path = os.path.join(pkg_share, 'config', 'config.yaml')
    
    # ★追加: EKF用の設定ファイル (ekf.yaml)
    ekf_config_path = os.path.join(pkg_share, 'config', 'ekf_params.yaml')
    ekf_global_config_path = os.path.join(pkg_share, 'config', 'ekf_global_params.yaml')

    # --- ノードの定義 ---

    # 1. オドメトリ配信ノード (注意: C++側でTF配信をOFFにすること！)
    odometry_node = Node(
        package='mirs',
        executable='odometry_publisher',
        name='odometry_publisher',
        output='screen',
        parameters=[config_file_path, {'use_sim_time': LaunchConfiguration('use_sim_time')}]
    )

    # 2. パラメータ管理ノード
    parameter_node = Node(
        package='mirs',
        executable='parameter_publisher',
        name='parameter_publisher',
        output='screen',
        parameters=[config_file_path, {'use_sim_time': LaunchConfiguration('use_sim_time')}]
    )

    # 3. Micro-ROS Agent
    micro_ros = Node(
        package='micro_ros_agent',
        executable='micro_ros_agent',
        name='micro_ros_agent',
        output='screen',
        arguments=['serial', '--dev', LaunchConfiguration('esp_port'), '-v6']
    )

    # 4. LiDARドライバ
    sllidar_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('sllidar_ros2'), 'launch', 'sllidar_s1_launch.py')
        ),
        launch_arguments={'serial_port': LaunchConfiguration('lidar_port'), 'serial_baudrate': '256000'}.items()
    )

    # 5. Static TF (Base Link -> Laser)
    # URDFを使うためコメントアウト
    # tf2_ros_node = Node(
    #     package='tf2_ros',
    #     executable='static_transform_publisher',
    #     output='screen',
    #     arguments=["0", "0", "0.3", "0", "0", "0", "base_link", "laser"]
    # )

    # ★追加: Robot State Publisher (URDF)
    urdf_file_name = 'mirs.urdf'
    urdf_path = os.path.join(
        get_package_share_directory('mirs_description'),
        'urdf',
        urdf_file_name)
    with open(urdf_path, 'r') as infp:
        robot_desc = infp.read()

    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_desc, 'use_sim_time': LaunchConfiguration('use_sim_time')}],
    )

    # ★追加: robot_localization (EKF) ノード x2

    # Local EKF (odom -> base_link)
    ekf_node_local = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node_local',
        output='screen',
        parameters=[ekf_config_path, {'use_sim_time': LaunchConfiguration('use_sim_time')}],
        remappings=[('/odometry/filtered', '/odometry/local')]
    )

    # Global EKF (map -> odom)
    ekf_node_global = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node_global',
        output='screen',
        parameters=[ekf_global_config_path, {'use_sim_time': LaunchConfiguration('use_sim_time')}],
        remappings=[('/odometry/filtered', '/odometry/global')]
    )

    # --- 起動リストの作成 ---
    ld = LaunchDescription()
    
    ld.add_action(esp_port)
    ld.add_action(lidar_port)
    ld.add_action(use_sim_time)

    ld.add_action(odometry_node)
    ld.add_action(parameter_node)
    ld.add_action(micro_ros)
    ld.add_action(sllidar_launch)

    # ld.add_action(tf2_ros_node)
    ld.add_action(robot_state_publisher_node)
    
    # ★追加: EKFを起動リストに追加
    ld.add_action(ekf_node_local)
    ld.add_action(ekf_node_global)

    return ld

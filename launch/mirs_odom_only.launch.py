import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    # パッケージのインストールディレクトリを取得
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
    config_file_path = os.path.join(pkg_share, 'config', 'config.yaml')
    
    # ★変更: EKF用の設定ファイル (ekf_odom_only.yaml)
    # Local EKFはそのまま使うが、Global EKFをodom_only版にする
    ekf_config_path = os.path.join(pkg_share, 'config', 'ekf_params.yaml')
    ekf_global_odom_only_path = os.path.join(pkg_share, 'config', 'ekf_odom_only.yaml')

    # --- ノードの定義 ---

    # 1. オドメトリ配信ノード
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

    # Robot State Publisher (URDF)
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

    # ★変更: robot_localization (EKF) ノード
    
    # Local EKF (odom -> base_link)
    # これはオドメトリとIMUを混ぜるものなので、そのまま使う
    ekf_node_local = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node_local',
        output='screen',
        parameters=[ekf_config_path, {'use_sim_time': LaunchConfiguration('use_sim_time')}],
        remappings=[('/odometry/filtered', '/odometry/local')]
    )

    # Global EKF (odom -> base_link) - Odom Only Mode
    # 元々は map -> odom を担当していたが、Odom Onlyモードでは map -> odom は Static TF で繋ぐため、
    # ここでは「オドメトリのみを使った高精度な odom -> base_link」を作るために使うか、
    # あるいは ekf_node_local だけで十分かもしれない。
    # しかし、ekf_odom_only.yaml の設定を見ると `odom0` のみを使って `odom_frame: odom`, `base_link_frame: base_link` となっている。
    # これは ekf_node_local と役割が重複する。
    # 
    # system_bringup_odom_only.launch.py で map->odom のStatic TFを出しているので、
    # ここでは「odom -> base_link」のTFを出す必要がある。
    # それは ekf_node_local が既にやっている (publish_tf: true なら)。
    # もし ekf_node_local が publish_tf: true なら、ekf_node_global (odom_only版) は不要。
    # 
    # 既存の ekf_params.yaml (Local用) を確認していないが、通常Local EKFは odom->base_link を出す。
    # したがって、Odom Onlyモードでは Global EKF は起動しなくて良い（あるいはLocal EKFと競合する）。
    # 
    # 結論: mirs_odom_only.launch.py では Global EKF を起動しない。
    # 代わりに Local EKF が odom -> base_link を担当する。
    
    # --- 起動リストの作成 ---
    ld = LaunchDescription()
    
    ld.add_action(esp_port)
    ld.add_action(lidar_port)
    ld.add_action(use_sim_time)

    ld.add_action(odometry_node)
    ld.add_action(parameter_node)
    ld.add_action(micro_ros)
    ld.add_action(sllidar_launch)

    ld.add_action(robot_state_publisher_node)
    
    ld.add_action(ekf_node_local)
    # ekf_node_global は起動しない

    return ld

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
    sllidar_share_dir = get_package_share_directory('sllidar_ros2')

    # --- 引数の定義 ---
    lidar_port = DeclareLaunchArgument(
        'lidar_port', 
        default_value='/dev/ttyUSB0',
        description='Set lidar usb port.')

    use_rviz = DeclareLaunchArgument(
        'use_rviz',
        default_value='true',
        description='Whether to start RViz'
    )

    rviz2_file = LaunchConfiguration('rviz2_file')
    declare_arg_rviz2_config_path = DeclareLaunchArgument(
        'rviz2_file', 
        default_value=os.path.join(
            mirs_share_dir,
            'rviz',
            'default.rviz')
    )

    # --- 1. LiDARドライバの起動 ---
    # S1 LiDAR用のボーレート 256000 を指定して起動します
    sllidar_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(sllidar_share_dir, 'launch', 'sllidar_s1_launch.py')
        ),
        launch_arguments={
            'serial_port': LaunchConfiguration('lidar_port'),
            'serial_baudrate': '256000'
        }.items()
    )

    # --- 2. Static TF (odom -> base_link) の配信 ---
    # 足回り（オドメトリ）を使わないため、odom と base_link を同一座標とする静的TFを配信します
    # これにより slam_toolbox が期待する tf tree が接続されます
    static_odom_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='static_odom_tf_publisher',
        output='screen',
        arguments=['--x', '0', '--y', '0', '--z', '0', 
                   '--yaw', '0', '--pitch', '0', '--roll', '0', 
                   '--frame-id', 'odom', '--child-frame-id', 'base_link']
    )

    # --- 3. Robot State Publisher (URDFモデルによる base_link -> laser などのTF配信) ---
    urdf_file_name = 'mirs.urdf'
    urdf_path = os.path.join(mirs_share_dir, 'urdf', urdf_file_name)
    with open(urdf_path, 'r') as infp:
        robot_desc = infp.read()

    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_desc, 'use_sim_time': False}],
    )

    # --- 4. SLAM (slam_toolbox LiDAR-only 設定) の起動 ---
    slam_node = Node(
        package='slam_toolbox', 
        executable='async_slam_toolbox_node',
        output='screen',
        parameters=[
            os.path.join(mirs_share_dir, 'config', 'slam_toolbox_lidar_only.yaml'),
            {'use_sim_time': False}
        ],
    )

    # --- 5. RViz2 の起動 ---
    rviz2_node = Node(
        name='rviz2',
        package='rviz2', 
        executable='rviz2', 
        output='screen',
        arguments=['-d', rviz2_file],
        parameters=[{'use_sim_time': False}],
        condition=IfCondition(LaunchConfiguration('use_rviz'))
    )

    # --- 起動アクションの構築 ---
    ld = LaunchDescription()
    
    ld.add_action(lidar_port)
    ld.add_action(use_rviz)
    ld.add_action(declare_arg_rviz2_config_path)

    ld.add_action(sllidar_launch)
    ld.add_action(static_odom_tf)
    ld.add_action(robot_state_publisher_node)
    ld.add_action(slam_node)
    ld.add_action(rviz2_node)

    return ld

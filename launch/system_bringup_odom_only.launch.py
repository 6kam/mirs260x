import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    # --- パッケージディレクトリの取得 ---
    mirs_pkg = get_package_share_directory('mirs')
    nav2_bringup_pkg = get_package_share_directory('nav2_bringup')
    bt_pkg = get_package_share_directory('bt_pkg')
    cone_detector_pkg = get_package_share_directory('cone_detector')

    # --- 引数の定義 ---
    # 1. マップファイル (使わないがNav2の引数互換のため)
    default_map_path = os.path.join(mirs_pkg, 'maps', 'my_mirs_map.yaml')
    map_yaml_file = DeclareLaunchArgument(
        'map',
        default_value=default_map_path,
        description='Full path to map file to load'
    )

    # 2. Behavior Tree XML (Odom Only版)
    default_bt_xml_path = os.path.join(bt_pkg, 'behavior_tree', 'bt_mission_odom_only.xml')
    bt_xml_arg = DeclareLaunchArgument(
        'bt_xml_path',
        default_value=default_bt_xml_path,
        description='Path to the Behavior Tree XML file'
    )

    # 3. シミュレーション時刻
    use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulated clock if true'
    )

    # 4. ログレベル
    log_level = DeclareLaunchArgument(
        'log_level',
        default_value='info',
        description='Log level for Nav2 nodes'
    )

    # 5. ポート設定
    esp_port = DeclareLaunchArgument(
        'esp_port',
        default_value='/dev/serial/by-id/usb-Silicon_Labs_CP2102N_USB_to_UART_Bridge_Controller_44dcbf303dfbeb1193273ca4c6d924ec-if00-port0',
        description='ESP32 USB port'
    )
    lidar_port = DeclareLaunchArgument(
        'lidar_port',
        default_value='/dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_947ec7a9868124459631e474f6875e54-if00-port0',
        description='LiDAR USB port'
    )

    # --- 1. ハードウェア & 基本システム (mirs.launch.py) ---
    # EKFパラメータを odom_only 版に差し替えるために、launch引数で上書きする
    # mirs.launch.py が ekf_config_file 引数を受け取るように修正が必要だが、
    # 既存ファイルを変更しない方針のため、ここでは mirs.launch.py の中身を展開するか、
    # あるいは mirs.launch.py がパラメータ引数に対応しているか確認が必要。
    # 確認したところ mirs.launch.py は ekf_config_path を受け取っていない可能性が高い。
    # そのため、mirs.launch.py を使わず、ここで個別にノードを立ち上げるか、
    # mirs.launch.py をコピーして mirs_odom_only.launch.py を作る必要がある。
    # ここでは安全のため mirs_odom_only.launch.py を作成し、それを呼び出す形にする。
    
    # ※ Implementation Plan にはなかったが、mirs.launch.py のパラメータ差し替えが必要なため、
    # mirs_odom_only.launch.py を作成するステップを追加で行う。
    
    mirs_hardware_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(mirs_pkg, 'launch', 'mirs_odom_only.launch.py')
        ),
        launch_arguments={
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'esp_port': LaunchConfiguration('esp_port'),
            'lidar_port': LaunchConfiguration('lidar_port')
        }.items()
    )

    # --- 2. ナビゲーション (Nav2) ---
    nav2_params_file = os.path.join(mirs_pkg, 'config', 'nav2_params.yaml')
    
    nav2_bringup_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav2_bringup_pkg, 'launch', 'navigation_launch.py')
        ),
        launch_arguments={
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'params_file': nav2_params_file,
            'log_level': LaunchConfiguration('log_level'),
        }.items()
    )

    # --- 3. カメラドライバ (v4l2_camera) ---
    camera_node = Node(
        package='v4l2_camera',
        executable='v4l2_camera_node',
        name='v4l2_camera',
        parameters=[{
            'video_device': '/dev/video2',
            'frame_id': 'camera',
            'io_method': 'mmap',
            'pixel_format': 'YUYV'
        }],
        remappings=[
            ('image_raw', '/camera/color/image_raw'),
            ('camera_info', '/camera/color/camera_info')
        ]
    )

    # --- 4. 認識・計画・BT (real_mission.launch.py) ---
    real_mission_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(bt_pkg, 'launch', 'real_mission.launch.py')
        ),
        launch_arguments={
            'bt_xml_path': LaunchConfiguration('bt_xml_path'),
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'use_lidar_only': 'false', # カメラフュージョンを有効化
            'use_rectangle_path': 'true' # 四角形経路を使用
        }.items()
    )

    # --- 5. Static TF (map -> odom) ---
    # オドメトリのみで動かすため、mapとodomを一致させる
    static_tf_map_odom = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='static_transform_publisher_map_odom',
        arguments=['0', '0', '0', '0', '0', '0', 'map', 'odom']
    )

    # --- 5.5 Trajectory Publisher ---
    trajectory_publisher = Node(
        package='mirs',
        executable='trajectory_publisher.py',
        name='trajectory_publisher',
        output='screen'
    )

    # --- 6. RViz2 ---
    rviz_config_file = os.path.join(mirs_pkg, 'rviz', 'system_view.rviz')
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config_file],
        output='screen'
    )

    # --- 7. Groot (v1) ---
    launch_groot_arg = DeclareLaunchArgument(
        'launch_groot',
        default_value='true',
        description='Launch Groot for behavior tree visualization'
    )

    from launch.actions import ExecuteProcess
    from launch.conditions import IfCondition

    groot_process = ExecuteProcess(
        cmd=[
            '/home/sawara/mirs_ws/Groot/build/Groot',
            '--mode', 'monitor',
            '--publisher_port', '2666',
            '--server_port', '2667',
            '--autoconnect'
        ],
        output='screen',
        condition=IfCondition(LaunchConfiguration('launch_groot'))
    )

    return LaunchDescription([
        map_yaml_file,
        bt_xml_arg,
        use_sim_time,
        log_level,
        launch_groot_arg,
        
        mirs_hardware_launch,
        nav2_bringup_launch,
        camera_node,
        real_mission_launch,
        static_tf_map_odom,
        trajectory_publisher,
        # landmark_localizer は起動しない
        rviz_node,
        groot_process
    ])

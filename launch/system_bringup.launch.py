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
    # 1. マップファイル
    default_map_path = os.path.join(mirs_pkg, 'maps', 'my_mirs_map.yaml')
    map_yaml_file = DeclareLaunchArgument(
        'map',
        default_value=default_map_path,
        description='Full path to map file to load'
    )

    # 2. Behavior Tree XML
    default_bt_xml_path = os.path.join(bt_pkg, 'behavior_tree', 'bt_mission.xml')
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

    # --- 1. ハードウェア & 基本システム (mirs.launch.py) ---
    # 含まれるもの: Micro-ROS, LiDAR, EKF(Local/Global), URDF(Robot State Publisher)
    mirs_hardware_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(mirs_pkg, 'launch', 'mirs.launch.py')
        ),
        launch_arguments={
            'use_sim_time': LaunchConfiguration('use_sim_time')
        }.items()
    )

    # --- 2. ナビゲーション (Nav2) ---
    nav2_params_file = os.path.join(mirs_pkg, 'config', 'nav2_params.yaml')
    
    # Nav2 Bringup (Navigation only - No Map Server / AMCL)
    # マップを使わないため、navigation_launch.py を使用する
    nav2_bringup_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav2_bringup_pkg, 'launch', 'navigation_launch.py')
        ),
        launch_arguments={
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'params_file': nav2_params_file,
            # 'use_robot_state_pub': 'False' # 必要に応じて有効化
        }.items()
    )

    # --- 3. カメラドライバ (v4l2_camera) ---
    # real_mission.launch.pyには含まれていないためここで起動
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
            ('image_raw', '/camera/color/image_raw'), # real_missionに合わせてリマップ
            ('camera_info', '/camera/color/camera_info')
        ]
    )

    # --- 4. 認識・計画・BT (real_mission.launch.py) ---
    # 含まれるもの: ScanToPCL, Clustering, Fusion, Area(Polygon), Zigzag, BT Executor
    # 注意: real_mission.launch.py内のCone Color Detector等は、
    # 上記カメラドライバからのトピック(/camera/color/image_raw)を期待している
    real_mission_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(bt_pkg, 'launch', 'real_mission.launch.py')
        ),
        launch_arguments={
            'bt_xml_path': LaunchConfiguration('bt_xml_path'),
            'use_sim_time': LaunchConfiguration('use_sim_time')
        }.items()
    )

    # --- 5. 自己位置補正 (Landmark Localizer) ---
    # Nav2の地図座標系(map)と、認識したコーン配置を照合して補正
    landmark_localizer_node = Node(
        package='cone_detector',
        executable='landmark_localizer',
        name='landmark_localizer',
        output='screen',
        parameters=[{'min_shared_landmarks': 1}]
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

    # Delay Landmark Localizer to wait for TF tree to be ready
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
        launch_groot_arg,
        
        mirs_hardware_launch,
        nav2_bringup_launch,
        camera_node,
        real_mission_launch,
        delayed_landmark_localizer_node,
        rviz_node,
        groot_process
    ])

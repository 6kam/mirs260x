import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    # realsense2_camera のパッケージディレクトリを取得
    realsense_share_dir = get_package_share_directory('realsense2_camera')
    
    # rtabmap_launch のパッケージディレクトリを取得
    # ROS 2 Humbleでは通常 rtabmap_launch に launch ファイルが含まれます
    try:
        rtabmap_share_dir = get_package_share_directory('rtabmap_launch')
    except Exception:
        rtabmap_share_dir = get_package_share_directory('rtabmap_ros')

    # RealSense カメラの起動設定
    realsense_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(realsense_share_dir, 'launch', 'rs_launch.py')
        ),
        launch_arguments={
            'align_depth.enable': 'true',     # デプス画像をカラー画像にアライメント
            'pointcloud.enable': 'false',     # カメラ側での点群生成を無効化（rtabmap側で生成するため）
            'enable_gyro': 'true',            # IMU対応カメラ（D435i等）のためのジャイロ有効化
            'enable_accel': 'true',           # 加速度計有効化
        }.items()
    )

    # RTAB-Map の起動設定
    rtabmap_launch_desc = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(rtabmap_share_dir, 'launch', 'rtabmap.launch.py')
        ),
        launch_arguments={
            'rtabmap_args': '--delete_db_on_start', # 起動時にデータベースを初期化
            'rgb_topic': '/camera/camera/color/image_raw',
            'depth_topic': '/camera/camera/aligned_depth_to_color/image_raw',
            'camera_info_topic': '/camera/camera/color/camera_info',
            'frame_id': 'camera_link',
            'approx_sync': 'true',             # 約同期を有効にする
            'rtabmap_viz': 'true',             # RTAB-Map可視化GUIを起動
            'rviz': 'false',                   # rtabmap_vizと両方起動しないようにRVizは無効化
        }.items()
    )

    ld = LaunchDescription()
    ld.add_action(realsense_launch)
    ld.add_action(rtabmap_launch_desc)

    return ld

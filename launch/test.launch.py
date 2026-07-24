"""
D435をステレオカメラ(左右IR画像)として使い、足回り(車輪オドメトリ/EKF)を接続せず、
RTAB-Map自身のステレオ視覚オドメトリ(stereo_odometry)でマッピングを行う。
屋外(特徴の乏しい開けた場所)向けにOdometry/ループクロージャのパラメータをチューニング済み。

構成:
    - realsense2_camera : D435のinfra1/infra2(左右IR)のみ有効化。エミッターOFF
    - rtabmap_launch     : stereo:=true, visual_odometry:=true
                            (内部でrtabmap_odom/stereo_odometryが起動し、姿勢を計算)

前提:
    - 足回り・EKFは使わないため、frame_idはカメラ自身(camera_link)を基準にする
    - map -> odom -> camera_link のTFはすべてRTAB-Map/stereo_odometryが自分で配信する

使い方:
    ros2 launch realsense_stereo_outdoor_rtabmap.launch.py
    ros2 launch realsense_stereo_outdoor_rtabmap.launch.py rtabmap_viz:=false
    ros2 launch realsense_stereo_outdoor_rtabmap.launch.py localization:=true
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression


def generate_launch_description():
    realsense_share_dir = get_package_share_directory('realsense2_camera')
    rtabmap_share_dir = get_package_share_directory('rtabmap_launch')

    camera_name = 'camera'
    frame_id = 'camera_link'

    # ---- 起動引数 ----
    use_rtabmap_viz = DeclareLaunchArgument(
        'rtabmap_viz', default_value='true',
        description='RTAB-Map可視化GUIを起動するか')

    localization = DeclareLaunchArgument(
        'localization', default_value='false',
        description='true: 既存マップ上で自己位置推定のみ行う / false: 新規マッピング')

    left_image_topic_arg = DeclareLaunchArgument(
        'left_image_topic', default_value=f'/{camera_name}/{camera_name}/infra1/image_rect_raw')
    right_image_topic_arg = DeclareLaunchArgument(
        'right_image_topic', default_value=f'/{camera_name}/{camera_name}/infra2/image_rect_raw')
    left_info_topic_arg = DeclareLaunchArgument(
        'left_camera_info_topic', default_value=f'/{camera_name}/{camera_name}/infra1/camera_info')
    right_info_topic_arg = DeclareLaunchArgument(
        'right_camera_info_topic', default_value=f'/{camera_name}/{camera_name}/infra2/camera_info')

    # 屋外(特徴の乏しい開けた場所)向けチューニング。
    # OdomF2M/GFTTは内部stereo_odometryに、Grid/Rtabmap系はRTAB-Map本体のループクロージャ・
    # マッピングに効く。localization:=trueのときはdelete_db_on_startを付けたくないので、
    # ここでは基本パラメータのみとし、DBの扱いはargs_extraで切り替える。
    rtabmap_args = DeclareLaunchArgument(
        'rtabmap_args',
        default_value=(
            '--OdomF2M/MaxSize 1000 '        # ローカルマップの特徴点保持数を増加(屋外の広さに対応)
            '--GFTT/MinDistance 10 '         # 特徴点抽出の間隔
            '--GFTT/QualityLevel 0.00001 '   # 低コントラストな地面・空でも特徴点を拾いやすく
            '--Grid/CellSize 0.1 '           # 屋外の広さに対しグリッド解像度を粗く
            '--Grid/RangeMax 8.0 '           # 検出可能距離(ステレオの信頼できる測距限界も考慮)
            '--Rtabmap/DetectionRate 1 '     # 移動が速い場合に密すぎるキーフレーム登録を抑制
            '--RGBD/OptimizeMaxError 3'
        ),
        description='RTAB-Mapとstereo_odometryに渡す追加パラメータ(DB削除フラグは含まない)',
    )

    # localization:=false(新規マッピング)のときだけ --delete_db_on_start を付与する
    rtabmap_args_effective = PythonExpression([
        "('--delete_db_on_start ' if '", LaunchConfiguration('localization'), "' == 'false' else '') + '",
        LaunchConfiguration('rtabmap_args'), "'",
    ])

    # ---- 1. RealSense D435 起動 (左右IR画像のみ有効化。カラー/深度は不使用) ----
    realsense_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(realsense_share_dir, 'launch', 'rs_launch.py')),
        launch_arguments={
            'camera_name': camera_name,
            'enable_infra1': 'true',
            'enable_infra2': 'true',
            'enable_color': 'false',
            'enable_depth': 'false',
            'depth_module.emitter_enabled': 'false',
            'depth_module.profile': '640x480x30',
        }.items(),
    )

    # ---- 2. RTAB-Map (ステレオ画像 + 内部ステレオ視覚オドメトリ) ----
    rtabmap_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(rtabmap_share_dir, 'launch', 'rtabmap.launch.py')),
        launch_arguments={
            'stereo': 'true',
            'left_image_topic': LaunchConfiguration('left_image_topic'),
            'right_image_topic': LaunchConfiguration('right_image_topic'),
            'left_camera_info_topic': LaunchConfiguration('left_camera_info_topic'),
            'right_camera_info_topic': LaunchConfiguration('right_camera_info_topic'),
            'frame_id': frame_id,
            'visual_odometry': 'true',
            'approx_sync': 'false',
            'localization': LaunchConfiguration('localization'),
            'rtabmap_viz': LaunchConfiguration('rtabmap_viz'),
            'rviz': 'false',
            'rtabmap_args': rtabmap_args_effective,
            'publish_tf': 'true',
            'subscribe_depth': 'false',
            'subscribe_scan': 'false',
            'subscribe_scan_cloud': 'false',
        }.items(),
    )

    return LaunchDescription([
        use_rtabmap_viz,
        localization,
        left_image_topic_arg,
        right_image_topic_arg,
        left_info_topic_arg,
        right_info_topic_arg,
        rtabmap_args,
        realsense_launch,
        rtabmap_launch,
    ])

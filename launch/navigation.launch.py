import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

def generate_launch_description():

    # 1. 自分のパッケージの 'share' ディレクトリへのパス
    mirs_share_dir = get_package_share_directory('mirs')

    # 2. Nav2 パッケージの 'share' ディレクトリへのパス
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')

    # --- 引数の定義 ---
    # マップファイルのデフォルトパス (パッケージ内の maps/my_mirs_map.yaml)
    default_map_path = os.path.join(mirs_share_dir, 'maps', 'my_mirs_map.yaml')
    
    map_yaml_file = DeclareLaunchArgument(
        'map',
        default_value=default_map_path,
        description='Full path to map file to load'
    )

    # 3. MIRS本体のハードウェア（odom, /scan, micro-ros, TF）を起動
    # (以前 T1 で実行していた mirs.launch.py をインクルードする)
    mirs_hardware_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(mirs_share_dir, 'launch', 'mirs.launch.py')
        )
    )

    # 5. Nav2 の設定ファイル（mirsパッケージのものを使用）
    nav2_params_file = os.path.join(
        mirs_share_dir, 'config', 'nav2_params.yaml'
    )

    # 6. Rviz の設定ファイル（Nav2標準のものを使用）
    rviz_config_file = os.path.join(
        nav2_bringup_dir, 'rviz', 'nav2_default_view.rviz'
    )

    # 7. Nav2 スタック本体の起動
    nav2_bringup_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav2_bringup_dir, 'launch', 'bringup_launch.py')
        ),
        # Nav2に渡す引数
        launch_arguments={
            'map': LaunchConfiguration('map'), # 引数で指定されたマップを使用
            'use_sim_time': 'False',           # 実機ロボットを使う
            'params_file': nav2_params_file,   # Nav2の設定ファイルを指定
        }.items()
    )

    # 8. Rviz の起動
    rviz_node = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav2_bringup_dir, 'launch', 'rviz_launch.py')
        ),
        launch_arguments={
            'rviz_config': rviz_config_file
        }.items()
    )

    # 9. 起動するものをリストにして返す
    return LaunchDescription([
        map_yaml_file,         # マップ引数
        mirs_hardware_launch,  # MIRS本体 (T1の代わり)
        nav2_bringup_launch,   # Nav2本体 (T2の代わり)
        rviz_node              # Rviz (T3の代わり)
    ])

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

def generate_launch_description():

    # 1. 自分のパッケージの 'share' ディレクトリへのパス
    mirs_share_dir = get_package_share_directory('mirs')

    # 2. Nav2 パッケージの 'share' ディレクトリへのパス
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')

    # --- 引数の定義 ---
    # マップファイルのデフォルトパス (パッケージ内の maps/my_mirs_map.yaml)
    default_map_path = os.path.join(mirs_share_dir, 'maps', 'rouka5.yaml')
    
    map_yaml_file = DeclareLaunchArgument(
        'map',
        default_value=default_map_path
    )

    use_rviz = DeclareLaunchArgument(
        'use_rviz',
        default_value='true',
        description='Whether to start RViz'
    )

    use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation (Gazebo) clock if true'
    )

    # 3. MIRS本体のハードウェア（odom, /scan, micro-ros, TF）を起動
    # (以前 T1 で実行していた mirs.launch.py をインクルードする)
    mirs_hardware_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(mirs_share_dir, 'launch', 'mirs.launch.py')
        ),
        #launch_arguments={'use_ekf_global': 'false'}.items()
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
            'use_sim_time': LaunchConfiguration('use_sim_time'),
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
        }.items(),
        condition=IfCondition(LaunchConfiguration('use_rviz'))
    )

    # 9. 起動するものをリストにして返す
    return LaunchDescription([
        map_yaml_file,         # マップ引数
        use_rviz,              # RViz起動フラグ
        use_sim_time,          # シミュレーション時間フラグ
        mirs_hardware_launch,  # MIRS本体 (T1の代わり)
        nav2_bringup_launch,   # Nav2本体 (T2の代わり)
        rviz_node,              # Rviz (T3の代わり)
    ])

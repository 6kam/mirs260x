# mirs

## 要件
### ハードウェア

- PC
- cugo v3i
- ESP32
- Cytron MD10C
- RPLiDAR S1

### ソフトウェア

- Ubuntu 22.04 または Ubuntu 24.04（WSL 可）
- それぞれのUbuntu バージョンに合わせたROS2 humble / jazzy 環境 もしくは mirs_container

docker(仮想環境)を使うか生環境を使うか選ぶことができます。

## 導入

### 1. ESP32 と LiDAR の準備

ESP32 と LiDAR を、LiDAR → ESP32 の順に PC へ接続してください。
ESP32には事前にmirs_espもしくはmirs_esp_pioを送信しておいてください。
プログラムは LiDAR が USB ポートの若い番号を取る前提で書かれています。順序を変える場合は、起動する launch ファイル内の `/dev/ttyUSB0` と `/dev/ttyUSB1` の記述を入れ替えてください。

### 2. ワークスペースの作成とリポジトリのクローン

```bash
mkdir -p mirs_workspace/src
cd mirs_workspace/src

# mirs パッケージを使う場合に必要な一式
# 使用する ROS 2 ディストリビューションに応じて jazzy/humble を適宜読み替えてください
git clone https://github.com/mirs260x/mirs.git
git clone -b jazzy https://github.com/micro-ROS/micro-ROS-Agent.git
git clone https://github.com/Slamtec/sllidar_ros2.git

cd ..
```

### 3. ビルド

```bash
# rosdep の更新
rosdep update

# 依存パッケージのインストール
rosdep install --from-path src --ignore-src -r -y

# 全パッケージのビルド
colcon build --symlink-install

# ビルド結果の読み込み
source install/setup.bash
```

### 4. 実行

まず基本的な動作を確認します。

```bash
# 基本的なシステム起動
ros2 launch mirs mirs.launch.py
```

LiDAR が回転していること、ターミナル上で ESP32 との通信が表示されていることを確認してください。

別のターミナルからコンテナに入り、エンコーダ値・オドメトリ値・走行試験などが正常か確認します。

PID 値の設定ファイル: `mirs_workspace/src/mirs/config/config.yaml`

```bash
# 前進（0.2 m/s）
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.2, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"

# 後退（0.2 m/s）
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist "{linear: {x: -0.2, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"

# 回転（0.5 rad/s）
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.5}}"

# 停止
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"
```

直進・回転のテストスクリプトも用意されています。

```bash
# 3m 直進テスト
ros2 run mirs odom_linear_test.py

# 回転テスト
ros2 run mirs odom_rotate_test.py
```

## 動作確認

```bash
# ノード一覧の表示
ros2 node list

# トピック一覧の表示
ros2 topic list

# x, y, z 軸でロボットがどこにいるかの確認
ros2 topic echo /odom

# エンコーダの値の確認（cugo v3 はクローラのため値は2つ出ます）
ros2 topic echo /encoder

# TF ツリーの確認
ros2 run tf2_tools view_frames
```

## マッピングと自律走行

### 地図作成（SLAM）

```bash
# マップ作成
ros2 launch mirs slam.launch.py
```

コントローラでロボットを動かしながら地図を作成します。移動中は RViz2 上でもロボットが動いていることを確認してください（地図作成には LiDAR だけでなくエンコーダの接続が必要です）。

地図ができたら、以下のコマンドで保存してください。`<マップ名>` は保存したいファイル名に置き換えてください。

```bash
ros2 run nav2_map_server map_saver_cli -f <保存先パス>/<マップ名>
```

作成した地図をそのまま使うと正常に動作しないことがあります。ペイントアプリ等で、点のまばらな箇所を塗りつぶす、足跡を壁として誤認識した箇所を白く塗りつぶすなどの後処理を行うとよいです。

### 自律走行（Navigation2）

保存したマップを使って、スタート地点とゴール地点を定めて自律走行させることができます。

```bash
# 起動時にデフォルトのマップパスを使う場合（launch ファイル内の default_map_path を変更）
ros2 launch mirs nav.launch.py

# コマンドラインでマップを指定する場合
ros2 launch mirs nav.launch.py map:=<保存先パス>/<マップ名>.yaml
```

nav2 は起動直後、ロボットの正確な位置を把握していないため、必ず初期位置合わせを行ってください。

1. RViz2 上部ツールバーの「2D Pose Estimate」をクリック
2. 地図上の、実際のロボットが存在する位置・向きをドラッグして指定
3. パーティクルクラウド（緑の矢印群）がロボット周辺に収束することを確認する

続けてゴール（目標地点）を指定します。

1. RViz2 上部ツールバーの「Nav2 Goal」（または「2D Nav Goal」）をクリック
2. 地図上で行きたい位置・向きをクリック＆ドラッグして指定
3. 経路（グローバルパス／ローカルパス）が表示され、ロボットが自律的に走行を開始する

実機へ書き込む前に、ピン割り当て、エンコーダ、車輪径、トレッド幅、モーター出力、非常停止、バッテリー監視の設定を確認してください。

## ライセンス

各ディレクトリの `LICENSE` および各パッケージのライセンス表記を確認してください。

## 謝辞

このプロジェクトは、以下の先行開発の成果を継承しています。

- **mirs2502** ([GitHub](https://github.com/mirs2502))
- **mirs240x** ([GitHub](https://github.com/mirs240x))

開発に携わった皆様に感謝申し上げます。

## 参考リンク

- [ROS 2 Documentation](https://docs.ros.org/en/jazzy/)
- [Navigation2](https://navigation.ros.org/)
- [SLAM Toolbox](https://github.com/SteveMacenski/slam_toolbox)
- [micro-ROS](https://micro.ros.org/)
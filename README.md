<div align="center">

# MIRS 260x
MIRS MG5 ROS2 Package with docker

</div>

---

## 概要

mirs_mg5 の標準的機能を備え、Docker に対応した ROS 2 パッケージです。
開発環境の統一、依存関係の競合の抑止、使用方法の文書作成および共有を目的に作られたパッケージです。


## 要件

### ソフトウェア

- Ubuntu 22.04 or Ubuntu 24.04 (wsl可)
- Docker（Docker Desktop 不可）
- Docker Compose
- [USBIPD-WIN](https://github.com/dorssel/usbipd-win)（Windows WSL2 環境で USB 接続する場合のみ必要）

## 導入

### ESP32とLiDAR の準備

完了後、ESP32とLiDARをLiDARから順にPCに接続してください。
プログラムはLiDARがUSBポートの若い番号をとる前提でできています。変更もできます。起動するlaunchファイルの/dev/ttyUSB0と/dev/ttyUSB1を入れ替えます。

### リポジトリのクローン

```bash
# 使用するパッケージのクローン(MicroROSやLiDARのパッケージ)
git clone -b jazzy https://github.com/micro-ROS/micro-ROS-Agent.git
git clone https://github.com/Slamtec/sllidar_ros2.git

cd ..
```

### ビルド


```bash
# rosdepの更新
rosdep update
# 依存パッケージのインストール
rosdep install --from-path src --ignore-src -r -y
# 全パッケージのビルド
colcon build --symlink-install
# ビルド結果の読み込み
source install/setup.bash
```

### 6. 実行

次に、ros2コマンドのエイリアスを使って各ノード達を起動します。

まず、基本的な動作の確認を行います。
   
```bash
# 基本的なシステム起動
ros2 launch mirs mirs.launch.py
```
LiDARの回転とターミナル上でのesp32との通信が表示されているか確認してください。

別のターミナルからコンテナに入り、下記の内容を参考にエンコーダ値・オドメトリ値・走行試験などが正常か確認します。

PID 値の設定ファイル：`your_ws/src/mirs/config/config.yaml`
   
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

```bash
# 3m 直進テスト
ros2 run mirs odom_linear_test.py

# 回転テスト
ros2 run mirs odom_rotate_test.py
```
```
# ノード一覧の表示
ros2 node list

# トピック一覧の表示
ros2 topic list
```
```bash
# トピックのデータ確認
ros2 topic echo /odom
ros2 topic echo /encoder   # cugo v3 はクローラのため値は2つ出ます

# TF ツリーの確認
ros2 run tf2_tools view_frames
```

問題なければ地図を作成します。

```
# マップ作成
slam
```

コントローラでロボットを動かしながらマップを作成します。移動中は rviz2 上でもロボットが動いていることを確認してください（マップ作成にはLiDARだけでなくエンコーダの接続が必要です）。

mapを作れたら、以下のコマンドを実行し、保存してください。<マップ名>は保存したいファイルの名称に変更してください。
   
```bash
# マップの保存コマンド（別ターミナルでコンテナに入って実行）
ros2 run nav2_map_server map_saver_cli -f /root/projects/mirsws/src/mirs_mg5/mirs/maps/<マップ名>
```

作成した地図をそのまま使うと正常に動作しないことがあります。ペイントアプリ等で点のまばらな箇所を塗りつぶす／足跡を壁として誤認識した箇所を白く塗りつぶすなどの後処理を行うとよいです。

navigation2を起動します。保存したマップと同じ場所で、スタート地点とゴール地点を定めて自律走行させることができます。

```
# 自律走行 nav.launch.pyのdefault_map_pathを保存したマップの名称に変更した場合
nav
# 自律走行 コマンドラインでマップを指定する場合
nav map:=/root/projects/mirsws/src/mirs_mg5/mirs/maps/<マップ名>.yaml
```

初期位置合わせを行います。nav2 は起動直後、ロボットの正確な位置を把握していません。必ず初期位置を指定してください。

rviz2 上部ツールバーの「2D Pose Estimate」をクリック

次に地図上の、実際のロボットが存在する位置・向きをドラッグして指定

パーティクルクラウド（緑の矢印群）がロボット周辺に収束することを確認する

ゴール（目標地点）の指定を行います。

rviz2 上部ツールバーの 「Nav2 Goal」（または「2D Nav Goal」） をクリック

次に地図上で行きたい位置・向きをクリック＆ドラッグして指定

経路（グローバルパス／ローカルパス）が表示され、ロボットが自律的に走行を開始する



## ライセンス

このプロジェクトは MIT ライセンスの下で公開されています。詳細は [LICENSE](LICENSE) を参照してください。

---

## 謝辞

このプロジェクトは、以下の先行開発の成果を継承しています。

- **mirs2502** ([GitHub](https://github.com/mirs2502))
- **mirs240x** ([GitHub](https://github.com/mirs240x))

開発に携わった皆様に感謝申し上げます。

---

## 参考リンク

- [ROS 2 Documentation](https://docs.ros.org/en/jazzy/)
- [Navigation2](https://navigation.ros.org/)
- [SLAM Toolbox](https://github.com/SteveMacenski/slam_toolbox)
- [micro-ROS](https://micro.ros.org/)

# MIRS 260x

MIRS 260x 用の ROS 2 ソフトウェア、ESP32 ファームウェア、Docker 開発環境をまとめたリポジトリです。

Docker に対応することで、開発環境の統一、依存関係の競合の抑止、使用方法の文書化および共有を目的としています。

## それぞれのリポジトリの置き場

- `mirs_workspace/src/mirs`: MIRS 本体の ROS 2 パッケージ
- `mirs_workspace/src/mirs_msgs`: 独自メッセージ・サービス
- `mirs_workspace/src/mapping_3d`: RealSense / RTAB-Map による 3D マッピング
- `mirs_workspace/mirs_container/humble`: ROS 2 Humble 用 Docker 環境
- `mirs_workspace/mirs_container/jazzy`: ROS 2 Jazzy 用 Docker 環境
- `mirs_esp`: Arduino IDE 用 ESP32 プログラム
- `mirs_esp_pio`: PlatformIO 用 ESP32 micro-ROS プログラム
- `standard`: 旧標準機用プログラム・参考コード

`build/`、`install/`、`log/` はビルド時に生成されるため、通常は編集しません。

## 要件

### ハードウェア

- PC
- cugo v3i
- ESP32
- Cytron MD10C
- RPLiDAR S1

### ソフトウェア

- Linux もしくは Windows(WSL)
- Docker（Docker Desktop 不可）、Docker Compose、Git
- ESP32 書き込み用の Arduino IDE または PlatformIO

Windows + WSL2 で USB 機器を使用する場合は、必要に応じて [usbipd-win](https://github.com/dorssel/usbipd-win) も準備してください。

Ubuntu 22.04,Ubuntu 24.04以外の環境のlinuxもしくは、生環境よごしたくないひとはdockeをつかってね

## 取得

ROS 2 パッケージを追加する場合は `mirs_workspace/src` に配置します。

ワークスペースをつくる
```bash
mkdir mirs_workspace/src
cd mirs_workspace/src/
```

つくったワークスペース内の src 下に使いたいパッケージをクローン
```bash
# これは mirs パッケージを使いたいときに必要なパッケージ群
# ros2 のディストリビューションによって適宜 humble に読み替えてください
git clone https://github.com/mirs260x/mirs.git
git clone https://github.com/mirs260x/mirs_msgs.git
git clone -b jazzy https://github.com/micro-ROS/micro-ROS-Agent.git
git clone https://github.com/Slamtec/sllidar_ros2.git
```

生環境で ROS 2 を使う場合

```bash
# 基本的な機能の起動
ros2 launch mirs mirs.launch.py
# 地図作成機能の起動
ros2 launch mirs slam.launch.py
# 作成した地図を元に自律走行機能の起動
ros2 launch mirs nav.launch.py
```

起動前に、各 launch ファイルで使用する `/dev/ttyUSB0`、`/dev/ttyUSB1` などのデバイス名が実際の接続状況と一致していることを確認してください。

## 動作確認

```bash
ros2 node list
ros2 topic list
# x y z 軸でロボットがどこにいるかの確認
ros2 topic echo /odom
# エンコーダの値の確認（cugo v3 はクローラのため値は 2 つ出ます）
ros2 topic echo /encoder
# TF ツリーの確認
ros2 run tf2_tools view_frames
```

`cmd_vel` に直接コマンドを送って動作確認することもできます。

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

PID の設定ファイルは `mirs_workspace/src/mirs/config/config.yaml` にあります。

## マッピングと自律走行

コントローラでロボットを動かしながら地図を作成します。移動中は RViz2 上でもロボットが動いていることを確認してください（地図作成には LiDAR だけでなくエンコーダの接続が必要です）。

地図ができたら、以下のコマンドで保存してください。`<マップ名>` は保存したいファイル名に置き換えてください。

```bash
ros2 run nav2_map_server map_saver_cli -f <保存先パス>/<マップ名>
```

作成した地図をそのまま使うと正常に動作しないことがあります。ペイントアプリ等で点のまばらな箇所を塗りつぶす、足跡を壁として誤認識した箇所を白く塗りつぶすなどの後処理を行うとよいです。

### 自律走行（Navigation2）

保存したマップを使って、スタート地点とゴール地点を定めて自律走行させることができます。

```bash
# コマンドラインでマップを指定する場合
nav map:=<保存先パス>/<マップ名>.yaml
```

nav2 は起動直後、ロボットの正確な位置を把握していないため、必ず初期位置合わせを行ってください。

1. RViz2 上部ツールバーの「2D Pose Estimate」をクリック
2. 地図上の、実際のロボットが存在する位置・向きをドラッグして指定
3. パーティクルクラウド（緑の矢印群）がロボット周辺に収束することを確認する

続けてゴール（目標地点）を指定します。

1. RViz2 上部ツールバーの「Nav2 Goal」（または「2D Nav Goal」）をクリック
2. 地図上で行きたい位置・向きをクリック＆ドラッグして指定
3. 経路（グローバルパス／ローカルパス）が表示され、ロボットが自律的に走行を開始する
```

実機へ書き込む前に、ピン割り当て、エンコーダ、車輪径、トレッド幅、モーター出力、非常停止、バッテリー監視の設定を確認してください。

## 主な ROS 2 インターフェース

| 名前 | 型 | 方向 |
|---|---|---|
| `/cmd_vel` | `geometry_msgs/msg/Twist` | ROS 2 → 車体 |
| `/odom` | `nav_msgs/msg/Odometry` | 車体 → ROS 2 |
| `/encoder` | パッケージ定義に依存 | 車体 → ROS 2 |

正確なトピック、ノード、パラメータは `mirs_workspace/src/mirs` と各 launch ファイルを参照してください。
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
<div align="center">

# MIRS 260x
MIRS MG5 ROS2 Package with docker

</div>

---

## 概要

mirs_mg5 の標準的機能を備え、Docker に対応した ROS 2 パッケージです。
開発環境の統一、依存関係の競合の抑止、使用方法の文書作成および共有を目的に作られたパッケージです。

---
## 目次

- [概要](#概要)
- [要件](#要件)
- [導入](#導入)
  - [1. ESP32とLiDARの準備](#1-esp32とlidarの準備)
  - [2. リポジトリのクローン](#2-リポジトリのクローン)
  - [3. Dockerイメージのビルド](#3-dockerイメージのビルド)
  - [4. コンテナの起動](#4-コンテナの起動)
  - [5. パッケージのビルド](#5-パッケージのビルド)
  - [6. 実行](#6-実行)
- [エイリアス](#エイリアス)
- [ライセンス](#ライセンス)
- [謝辞](#謝辞)
- [参考リンク](#参考リンク)

## 要件

### ハードウェア

- pc
- cugo v3i
- ESP32
- Cytron MD10C
- RPLiDAR S1

### ソフトウェア

- Docker（Docker Desktop 不可）
- Docker Compose
- [USBIPD-WIN](https://github.com/dorssel/usbipd-win)（Windows WSL2 環境で USB 接続する場合のみ必要）
- Arduino IDE（ESP32 に micro-ros-client を導入するため）

## 導入

### 1. ESP32とLiDAR の準備

まず、esp32にソースコードを送信する工程です。初回のみ行います。
Arduino IDE に以下のソースコード、ライブラリ、ボードマネージャーを導入します。(Windowsを使用している場合はWSL上ではなく、Windows上にArduinoIDEとソースコードをダウンロードしてください。)

- ESP32 用ソースコード：[mirs260x-esp](https://github.com/6kam/mirs_tanq_a_esp)（元になったコード：[mirs240x/mirs24_esp32](https://github.com/mirs240x/mirs24_esp32.git)）
- micro-ROS ライブラリ(zipでライブラリをインポートする)：[micro_ros_arduino_mirs240x](https://github.com/mirs240x/micro_ros_arduino_mirs240x)
- ボードマネージャは esp32（Espressif Systems著）バージョン 2.x 系を導入し、導入後、ボードは **ESP32 Dev Module** を選択してください。

esp32を接続し、ソースコードをコンパイル、送信してください。

完了後、ESP32とLiDARをLiDARから順にPCに接続してください。
混乱を避けるため、LiDARを先に接続するようにしてください。（プログラムはLiDARがUSBポートの若い番号をとる前提でできています。変更もできます。起動するlaunchファイルの/dev/ttyUSB0と/dev/ttyUSB1を入れ替えます。）

### 2. リポジトリのクローン

次に、ros2をメインで動かすpcにソースコードをダウンロードします。これについても初回のみ行います。

```bash
# メインのソースコードのクローン
git clone https://github.com/6kam/mirs260x.git
cd mirs260x/src

# 使用するパッケージのクローン(MicroROSやLiDARのパッケージ)
git clone -b humble https://github.com/micro-ROS/micro-ROS-Agent.git
git clone https://github.com/Slamtec/sllidar_ros2.git
git clone -b humble https://github.com/micro-ROS/micro_ros_msgs.git

cd ..
```

`src` ディレクトリ配下に micro-ROS や sllidar_ros2 が配置されていることを確認してください。

### 3. Docker イメージのビルド

次に、Dockerイメージをビルドします。初回のみ行います。Dockerfileを書き換えない限りは再ビルドは不要です。

```bash
# イメージのビルド
docker compose build
```

### 4. コンテナの起動

次にdockerコンテナを起動し、コンテナ内に入ります。ここの中でros2のコマンドを実行することになります。
二回目以降の場合はコンテナ起動前にLiDARとESP32を接続してください。

```bash
# コンテナ内からのGUI転送許可
xhost +local:      # X11転送を許可（WSLでは不要）

# コンテナをバックグラウンドで起動
docker compose up -d

# コンテナ内のターミナルに入る
docker compose exec mirs bash
```

### 5. パッケージのビルド

#### ビルド

次にコンテナ内でソースコードをビルドします。これによってインストールするパッケージやソフトウェアのバージョンが統一されます。
エイリアスを使用しているため、よく使われるros2のコマンドとは見た目が異なります。元のコマンド我みたい場合は後述のエイリアス一覧を参照。

```bash
# rosdepの更新
ru
# 依存パッケージのインストール
ri
# 全パッケージのビルド
cb
# ビルド結果の読み込み
si
```

### 6. 実行

次に、ros2コマンドのエイリアスを使って各ノード達を起動します。

まず、基本的な動作の確認を行います。
   
```bash
# 基本的なシステム起動
mirs
```
LiDARの回転とターミナル上でのesp32との通信が表示されているか確認してください。

別のターミナルからコンテナに入り、下記の内容を参考にエンコーダ値・オドメトリ値・走行試験などが正常か確認します。

PID 値の設定ファイル：`mirs260x/src/mirs_mg5/mirs/config/config.yaml`
   
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

①rviz2 上部ツールバーの「2D Pose Estimate」をクリック

②地図上の、実際のロボットが存在する位置・向きをドラッグして指定

③パーティクルクラウド（緑の矢印群）がロボット周辺に収束することを確認する

ゴール（目標地点）の指定を行います。

①rviz2 上部ツールバーの 「Nav2 Goal」（または「2D Nav Goal」） をクリック

②地図上で行きたい位置・向きをクリック＆ドラッグして指定

③経路（グローバルパス／ローカルパス）が表示され、ロボットが自律的に走行を開始する


---
## ソースコードの編集

ホストマシンの `src/` はコンテナ内にマウントされているため、ホストで編集した内容は起動中のコンテナに即座に反映されます。


## コンテナの終了方法

```bash
# コンテナから出る
exit
# コンテナを削除する(docker compose up -dで実行した分の削除)
docker compose down
```

---
### エイリアス

コンテナ内では以下のエイリアスが使用できます。

| エイリアス | 実体 | 説明 |
|---|---|---|
| `ru`  | `rosdep update` | rosdep の更新 |
| `ri`  | `rosdep install --from-path src --ignore-src -r -y` | 依存パッケージのインストール |
| `cb`  | `colcon build --symlink-install` | 全パッケージをビルド|
| `cbs` | `colcon build --symlink-install --packages-select` | 指定パッケージのみビルド |
| `cbt` | `colcon build --symlink-install --packages-up-to` | 依存関係込みでビルド |
| `si`  | `source install/setup.bash` | ビルド結果を読み込み |
| `mirs`| `ros2 launch mirs mirs.launch.py` | システム起動 |
| `slam`| `ros2 launch mirs slam.launch.py` | マップ作成 |
| `nav` | `ros2 launch mirs nav.launch.py` | 自律走行 |

```bash
# .bashrcに記述済み
source /opt/ros/humble/setup.bash
```

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

- [ROS 2 Documentation](https://docs.ros.org/en/humble/)
- [Navigation2](https://navigation.ros.org/)
- [SLAM Toolbox](https://github.com/SteveMacenski/slam_toolbox)
- [micro-ROS](https://micro.ros.org/)

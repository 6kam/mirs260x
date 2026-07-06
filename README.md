# MIRS MG5 ROS 2 Package with Docker

mirs_mg5 の標準的機能を備えた ROS 2 パッケージ（Docker 対応版）です。

---

## 概要

このリポジトリは、以下のリポジトリを継承・改変したものです。

1. **[mirs2502](https://github.com/mirs2502)** による改変版
   オリジナル（mirs240x）をクローンし、パッケージ統合などを行ったもの
2. **[mirs240x](https://github.com/mirs240x)** によるオリジナル版
   プロジェクトの基盤となる ROS 2 パッケージ群

---

## ⚠️ 既知の問題点

| 項目 | 内容 |
|---|---|
| **TF ツリー** | `base_footprint` と `base_link` の使い分け条件が未整理。現状は `base_link` を採用している。 |
| **nav2 params** | コストマップの調整が未完了。クローンしたままの環境で動作しない場合は要調整。 |
| **Map** | `pc_slam.launch.py` で作成した地図をそのまま使うと正常に動作しないことがある。計測パラメータの調整、またはペイントアプリ等で点のまばらな箇所を塗りつぶす／足跡を壁として誤認識した箇所を白く塗りつぶすなどの後処理を行うこと。 |

---

## 要件

### ハードウェア

- cugo v3i
- ESP32
- PC
- Cytron MD10C

### ソフトウェア

- Linux（Arch Linux (Hyprland)、Ubuntu 24.04、WSL2 上の Arch Linux で動作確認済み）
- Docker（Docker Desktop は不可）
- Docker Compose
- [USBIPD-WIN](https://github.com/dorssel/usbipd-win)（Windows WSL2 環境で USB 接続する場合のみ必要）
- Arduino IDE（ESP32 に micro-ros-client を導入するため）

---

## 含まれるパッケージ

### mirs

- ESP32 との通信（micro-ROS）
- オドメトリ計算と TF 配信
- ロボットモデル（URDF）
- navigation2 / SLAM

### mirs_msgs

- カスタムメッセージ定義パッケージ

---

## つかいかた

### 1. ESP32 のセットアップ

Arduino IDE に以下のソースコードとライブラリを導入します。

- ESP32 用ソースコード：[mirs260x-esp](https://github.com/6kam/mirs_tanq_a_esp)
  （元になったコード：[mirs240x/mirs24_esp32](https://github.com/mirs240x/mirs24_esp32.git)）
- micro-ROS ライブラリ：[micro_ros_arduino_mirs240x](https://github.com/mirs240x/micro_ros_arduino_mirs240x)（zip で Arduino IDE にインポート）

> ボードマネージャは ESP32 用バージョン 2.x 系を導入し、ボードは **ESP32 Dev Module** を選択してください。

### 2. リポジトリのクローン

```bash
git clone https://github.com/6kam/mirs260x.git
cd mirs260x/src

git clone -b humble https://github.com/micro-ROS/micro-ROS-Agent.git
git clone https://github.com/Slamtec/sllidar_ros2.git
git clone -b humble https://github.com/micro-ROS/micro_ros_msgs.git
```

`src` ディレクトリ以下に micro-ROS や sllidar_ros2 が配置されていることを確認してください。

### 3. Docker イメージのビルド

```bash
cd ..
docker compose build
```

### 4. コンテナの起動

```bash
xhost +local:      # X11転送を許可（WSL 環境の場合は不要）
docker compose up -d
docker compose exec mirs bash
```

### 5. ROS 2 ノードのビルドと実行

#### ビルド

コンテナ内では以下のエイリアスが使用できます。

| エイリアス | 実体 | 説明 |
|---|---|---|
| `ru`  | `rosdep update` | rosdep の更新 |
| `ri`  | `rosdep install --from-path src --ignore-src -r -y` | 依存パッケージのインストール |
| `cb`  | `colcon build --symlink-install` | 全パッケージをビルド |
| `cbs` | `colcon build --symlink-install --packages-select` | 指定パッケージのみビルド |
| `cbt` | `colcon build --symlink-install --packages-up-to` | 依存関係込みでビルド |
| `si`  | `source install/setup.bash` | ビルド結果を読み込み |
| `mirs`| `ros2 launch mirs mirs.launch.py` | システム起動 |
| `slam`| `ros2 launch mirs slam.launch.py` | マップ作成 |
| `nav` | `ros2 launch mirs nav.launch.py` | 自律走行 |

また、コンテナ起動時に以下は自動で実行されています。

```bash
source /opt/ros/humble/setup.bash
```

コンテナ内で以下を順番に実行してください。

```bash
ru
ri
cb
si
```

#### 実行

実行前に **LiDAR と ESP32 を PC に USB 接続** してください。
LiDAR を先に接続することで `/dev/ttyUSB0` が LiDAR になります（launch 時にポート指定は不要です）。

`docker-compose.yml` では接続時に以下のデバイスがマウントされます。

- `/dev/ttyUSB0`：LiDAR
- `/dev/ttyUSB1`：ESP32

```bash
mirs   # 基本的なシステム起動
slam   # マップ作成
nav    # 自律走行
```

**手順の目安：**

1. まず `mirs` を実行します。
2. 別のターミナルからコンテナに入り、下記「デバッグ」の内容を参考にエンコーダ値・オドメトリ値・走行試験などが正常か確認します。
3. 問題なければコントローラで mirs を動かしながらマップを作成します。移動中は rviz2 上でも mirs が動いていることを確認してください（マップ作成には LiDAR とエンコーダの接続が必要です）。

```bash
# マップの保存コマンド（別ターミナルでコンテナに入って実行）
ros2 run nav2_map_server map_server_cli -f /root/projects/mirsws/src/mirs_mg5/mirs/maps
```

---

## 開発方法

### ソースコードの編集

ホストマシンの `src/` はコンテナ内にマウントされているため、ホストで編集した内容は起動中のコンテナに即座に反映されます。

### デバッグ

PID 値の設定ファイル：`mirs260x/src/mirs_mg5/mirs/config/config.yaml`

```bash
# ノード一覧の表示
ros2 node list

# トピック一覧の表示
ros2 topic list
```

**走行の確認方法**

以下のコマンドを実行する前に、別のターミナルでコンテナに入り `mirs` を実行しておいてください。

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

```bash
# トピックのデータ確認
ros2 topic echo /odom
ros2 topic echo /encoder   # cugo v3 はクローラのため値は2つ出ます

# TF ツリーの確認
ros2 run tf2_tools view_frames
```

---

## コンテナの終了方法

```bash
exit
docker compose down
```

---

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

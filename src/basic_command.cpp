#include "rclcpp/rclcpp.hpp"
#include "mirs_msgs/srv/basic_command.hpp"  // 新しいサービスファイルをインクルード

#include <chrono>
#include <cstdlib>
#include <memory>

using namespace std::chrono_literals;

int main(int argc, char **argv)
{
    rclcpp::init(argc, argv);

    // ノードの作成
    auto node = rclcpp::Node::make_shared("basic_command_client");

    // サービスクライアントの作成
    auto client = node->create_client<mirs_msgs::srv::BasicCommand>("esp_cmd");

    // YAMLファイルからパラメータを読み込むための宣言
    node->declare_parameter("param1", 1.0);
    node->declare_parameter("param2", 0.0);
    node->declare_parameter("param3", 0.0);
    node->declare_parameter("param4", 0.0);

    // サービスが利用可能になるまで待機
    while (!client->wait_for_service(1s)) {
        if (!rclcpp::ok()) {
            RCLCPP_ERROR(rclcpp::get_logger("rclcpp"), "サービス待機中に中断されました。終了します。");
            return 0;
        }
        RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "サービスが利用できません。再試行します...");
    }

    // リクエストの作成
    auto request = std::make_shared<mirs_msgs::srv::BasicCommand::Request>();

    // YAMLからパラメータを取得してリクエストに設定
    request->param1 = node->get_parameter("param1").as_double();
    request->param2 = node->get_parameter("param2").as_double();
    request->param3 = node->get_parameter("param3").as_double();
    request->param4 = node->get_parameter("param4").as_double();

    // サービスを呼び出す
    auto result = client->async_send_request(request);

    // 結果を待機
    if (rclcpp::spin_until_future_complete(node, result) == rclcpp::FutureReturnCode::SUCCESS) {
        RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "リクエストの成功状態: %s", result.get()->success ? "true" : "false");
    } else {
        RCLCPP_ERROR(rclcpp::get_logger("rclcpp"), "サービス呼び出しに失敗しました。");
    }

    rclcpp::shutdown();
    return 0;
}

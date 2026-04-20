# Sprint 2 テスト

## 概要

Sprint 2の実装を検証するためのテストスイートです。以下の機能をテストします：

1. **官職間の通信網（InboxとPub/Sub）の構築**
2. **状態遷移の厳格化（バリデーション）とリトライ管理**
3. **官職（エージェント）の待機・通知受信ループ**
4. **頭弁の政務分解とアサイン処理**

## 前提条件

- Redisサーバーがlocalhost:6379で起動していること
- Pythonの依存パッケージがインストールされていること

## テスト実行方法

### すべてのテストを実行

```bash
cd tests/sprint2
python -m pytest -v
```

### 特定のテストファイルを実行

```bash
# 通信網テスト
python -m pytest test_communication.py -v

# 状態遷移テスト
python -m pytest test_state_validation.py -v

# エージェントループテスト
python -m pytest test_agent_loop.py -v

# 頭弁テスト
python -m pytest test_tonoben_decompose.py -v
```

### 特定のテストケースを実行

```bash
# Inboxの永続性テスト
python -m pytest test_communication.py::TestInboxAndPubSub::test_inbox_persistence -v

# 状態遷移バリデーションテスト
python -m pytest test_state_validation.py::TestStateValidationAndRetry::test_invalid_state_transition_blocked -v
```

## テスト内容詳細

### test_communication.py
- `test_inbox_persistence`: Inboxの確実性（システム停止後のデータ永続性）
- `test_fifo_order`: FIFO（先入れ先出し）の確認
- `test_pubsub_notification`: Pub/Subの即時性
- `test_send_message_integration`: StateManager.send_message()の統合テスト
- `test_multiple_agents_communication`: 複数エージェント間の通信

### test_state_validation.py
- `test_valid_state_transitions`: 正当な状態遷移の許可
- `test_invalid_state_transition_blocked`: 不正な状態遷移の遮断
- `test_all_invalid_transitions`: すべての不正遷移パターンのテスト
- `test_retry_count_increment_on_doing_failure`: DOING失敗時のリトライカウント加算
- `test_retry_limit_exceeded`: リトライ上限超過時の自動FAILED判定
- `test_valid_reviewing_transitions`: REVIEWING状態の正当な遷移

### test_agent_loop.py
- `test_agent_initialization`: エージェントの初期化と出仕宣言
- `test_heartbeat_update`: ハートビートの更新
- `test_message_handling_status_change`: メッセージ受信時の状態変化
- `test_message_handling_error_status`: メッセージ処理エラー時の状態変化
- `test_inbox_message_retrieval`: Inboxからのメッセージ取得
- `test_pubsub_notification_wakeup`: Pub/Sub通知による起床
- `test_multiple_concurrent_agents`: 複数エージェントの同時実行

### test_tonoben_decompose.py
- `test_tonoben_initialization`: 頭弁の初期化
- `test_order_received_processing`: 詔勅受信時の処理
- `test_task_creation_and_assignment`: タスクの作成とアサイン処理
- `test_task_dependency_resolution`: タスクの依存関係解決
- `test_unknown_message_type_handling`: 未知のメッセージタイプの処理
- `test_llm_error_handling`: LLMエラー時の処理
- `test_yaml_parsing_error_handling`: YAML解析エラー時の処理
- `test_multiple_task_assignment`: 複数タスクのアサイン処理

## モックについて

テストでは以下のモックを使用しています：

- `ollamaWrapper`: LLMの応答をモック化
- `extract_yaml`: YAML抽出処理をモック化

これにより、実際のLLM接続なしで頭弁のタスク分解ロジックをテストできます。

## 注意事項

- テスト実行前にRedisサーバーを起動してください
- テストはdb=1を使用するため、本番データには影響しません
- テスト実行後は自動的にクリーンアップされます

## カバレッジ

カバレッジレポートを生成する場合：

```bash
python -m pytest --cov=src --cov-report=html
```

レポートは`htmlcov/index.html`に生成されます。

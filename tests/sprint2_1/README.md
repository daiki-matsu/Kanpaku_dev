# Sprint 2.1 統合テスト

## 概要

Sprint 2.1では、イベントループとLLM実行の統合テストを実装します。これにより、実際のシステム環境での動作を検証します。

## 主な機能

1. **イベントループの基本動作テスト**
   - ハートビート更新の検証
   - イベントループのライフサイクル確認

2. **メッセージ処理の統合テスト**
   - Inboxからのメッセージ受信
   - イベントループ内でのメッセージ処理

3. **実際のLLM実行テスト**
   - LLM呼び出しの検証
   - タスク分解結果の確認
   - エージェントへのタスク割り当て

4. **複数エージェントの連携テスト**
   - エージェント間通信の検証
   - イベントループの連携動作

5. **エラーハンドリングテスト**
   - 例外発生時の挙動確認
   - エージェント状態の遷移検証

## 前提条件

- Redisサーバーがlocalhost:6379で起動していること
- LLM接続環境が整っていること（Ollamaなど）
- Pythonの依存パッケージがインストールされていること

## テスト実行方法

### すべてのテストを実行

```bash
cd tests/sprint2_1
python -m pytest -v
```

### 特定のテストを実行

```bash
# イベントループ基本動作テスト
python -m pytest test_event_loop_integration.py::TestEventLoopIntegration::test_event_loop_basic_operation -v

# LLM実行テスト
python -m pytest test_event_loop_integration.py::TestEventLoopIntegration::test_real_llm_execution_in_event_loop -v

# 複数エージェント連携テスト
python -m pytest test_event_loop_integration.py::TestEventLoopIntegration::test_multi_agent_event_loop_coordination -v
```

### 詳細な実行ログを表示

```bash
python -m pytest -v -s --tb=short
```

## テスト内容詳細

### test_event_loop_basic_operation
- イベントループの基本的な動作を検証
- ハートビート更新が正しく行われることを確認
- イベントループのライフサイクルをテスト

### test_message_processing_in_event_loop
- イベントループ内でのメッセージ処理を検証
- Inboxからのメッセージ受信と処理をテスト
- メッセージ処理結果の正確性を確認

### test_real_llm_execution_in_event_loop
- イベントループ内での実際のLLM実行をテスト
- LLM呼び出しの引数と戻り値を検証
- タスク分解結果とエージェント割り当てを確認

### test_multi_agent_event_loop_coordination
- 複数エージェントのイベントループ連携をテスト
- エージェント間のメッセージ交換を検証
- 連携動作の同期性を確認

### test_event_loop_error_handling
- イベントループ内でのエラーハンドリングをテスト
- 例外発生時のエージェント状態遷移を検証
- エラー回復メカニズムを確認

## 注意事項

- テストはdb=2を使用するため、本番データには影響しません
- テスト実行後は自動的にクリーンアップされます
- LLM実行テストではモックを使用しているため、実際のLLM接続は不要です
- イベントループテストでは短時間で完了するように設計されています

## 期待される結果

- すべてのテストが成功すること
- イベントループが安定して動作すること
- LLM実行が正しく統合されていること
- エージェント間の連携が正常に機能すること

## トラブルシューティング

### Redis接続エラー
```
redis.exceptions.ConnectionError: Error 10061
```
- Redisサーバーが起動していることを確認してください
- ポート6379が利用可能であることを確認してください

### LLM接続エラー
```
ConnectionError: Cannot connect to Ollama
```
- LLMサーバー（Ollamaなど）が起動していることを確認してください
- モックを使用しているため、実際の接続は不要です

### タイムアウトエラー
- イベントループのタイムアウト値（10秒）を調整してください
- システムの負荷が低い状態でテストを実行してください

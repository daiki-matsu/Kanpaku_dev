# Sprint3 テスト

Sprint3の実装要件に対する包括的なテストスイート。

## テスト対象機能

### 🔒 Redis Lock 排他制御
- 正常な取得と解放
- 競合時の弾き（アトミック性）
- 他者による不正解呪の防止
- 有効期限（TTL）機能
- 並列ロック取得試行

### 👤 舎人エージェント実装
- 正常なタスク処理（ASSIGNED → DOING → REVIEWING）
- ロックの取得と解呪
- エラー時のリトライ機構
- ファイル操作の安全性
- 並列タスク実行

### 🤝 関白-頭弁-舎人連携
- 三役揃い踏み（エージェント初期化）
- 帝の詔勅（関白→頭弁）
- 連鎖の証明（関白→頭弁→舎人→レビュー）
- 並列舎人実行

## 実行方法

### 前提条件
- Redisサーバーが起動していること
- Python 3.8+
- 必要な依存パッケージがインストール済み

### 全テスト実行
```bash
python run_tests.py
```

### 個別テスト実行
```bash
# Redis Lockテストのみ
python run_tests.py --lock

# 舎人エージェントテストのみ
python run_tests.py --toneri

# 連携テストのみ
python run_tests.py --integration
```

### 詳細出力
```bash
python run_tests.py --verbose
```

### pytest直接実行
```bash
# 全テスト
pytest tests/sprint3/ -v

# 特定ファイル
pytest tests/sprint3/test_redis_lock.py -v
```

## テスト構成

```
tests/sprint3/
├── conftest.py              # テスト共通設定・fixture
├── test_redis_lock.py       # Redis Lock排他制御テスト
├── test_toneri_agent.py     # 舎人エージェント実装テスト
├── test_integration.py      # 関白-頭弁-舎人連携テスト
├── run_tests.py             # テスト実行スクリプト
└── README.md               # このファイル
```

## Sprint3実装要件との対応

| 要素 | テスト | 状態 |
|------|------|------|
| 関白：頭弁への指示書作成 | test_integration.py | ✅ |
| 詔勅（入力欄）：関白への指示 | test_integration.py | ✅ |
| 舎人-2の追加 | test_integration.py | ✅ |
| 並列処理実装 | test_toneri_agent.py, test_integration.py | ✅ |
| 同時実行上限（舎人数で制限） | test_toneri_agent.py | ✅ |
| タスク取得時の競合防止 | test_redis_lock.py | ✅ |
| Redisでロック | test_redis_lock.py | ✅ |

## 注意事項

- テストはRedisのdb=2を使用します（本番環境と分離）
- 一時ファイルやディレクトリは自動的にクリーンアップされます
- モックを使用してLLMの呼び出しをシミュレートしています

## トラブルシューティング

### Redis接続エラー
```bash
# Redisサーバー起動
redis-server
```

### インポートエラー
```bash
# プロジェクトルートで実行
cd /path/to/Kanpaku_py
python -m pytest tests/sprint3/
```

### 権限エラー
```bash
# 実行権限付与
chmod +x tests/sprint3/run_tests.py
```


# MVP構成 実装計画
### sprint 1
- Redisへの書き込み
	- tasks
		1. assigned
		2. doing
		3. completed
	- agents
		1. idle
		2. thinking
		3. idle
	- events streem
- 履歴への書き込み
	- task
	- event
	- state
	- agent
	- lock
- Redisと履歴の整合性がとれていること
- 舎人-1
	- ファイル書き込み処理
	- Executor層
	    - safe_read  
	    - safe_write 
	    - パス制限（/project配下）
### sprint 2
- 頭弁：タスク分解 → 舎人-1にアサイン
- エージェントの通知待ちループ
- Redisへの書き込み
	- inbox：頭弁/舎人-1への通知
- Pub/Subで通知
- retryカウント管理（初期版）
	- doing失敗時：retry.count++
- status遷移バリデーション
    - created → assigned → doing → reviewing → completed のみ許可
	- 不正遷移のログ出力
### sprint 3
- 関白：頭弁への指示書作成
- 詔勅(入力欄)：関白への指示
- 舎人-2の追加
	- 並列処理実装
	- 同時実行上限（舎人数で制限）
    - タスク取得時の競合防止
        - Redisでロック
### sprint 4
- レビュー追加
	- TASK_COMPLETED → reviewing に変更
	- 機械チェック実装
		- execution.statusチェック
		- answer.statusチェック
	- 頭弁レビュー実装
		- LLMレビュー（スコア付き）
		- 80以上 → success
		- 未満 → failed
- リトライループ
	- REVIEW_REJECTED → assignedへ戻す
	- retry.count++
	- retry上限（仮で5）
### sprint 5
- STALLED検知
	- タイムアウト
		- doing > 120秒
		- thinking > 300秒
	- status → assignedへ戻す
		- retry.count++
- agent再起動ロジック
	- agent状態制御：error → retrying → idle
- ハートビート管理
	- 30秒ごと更新
	- last_heartbeat記録
### sprint 6
- 奏上（ダッシュボード）
	- FAILタスク一覧
	- retry多発タスク
	- doing数
	- 完了数
- タスク一覧UI
	- id / status / agent / priority
	- ソートのみ（フィルタは後回し）
- イベントストリーム表示：Redis streamをそのまま表示
- 簡易エージェント状態表示
	- status（色付き）
	- current_task
### sprint 7
- fail確定ロジック
	- retry.count >= 10 → failed
- lock強化
	- TTL延長
	- 所有者チェック
- ログ整備：state.logを表示
### sprint 8
- 擬似CLI導入
	- エージェント別ログ表示
	- 平安風メッセージ
- heartbeat表示
	- thinking → 思案中…    
	- doing → 作業中…
- クリック連動
	- タスククリック：エージェント強調
	- エージェントクリック：担当タスク強調
# MVP構成
## MVPのゴール定義
- 1つの指示から    
- 複数タスクに分解され    
- 舎人が実行し    
- 頭弁がレビューして    
- UIにリアルタイム反映される
## 内容
### 1. エージェント構成
| 役割  | 採用  | 理由           |
| --- | --- | ------------ |
| 関白  | ✅   | ユーザーIF必須     |
| 頭弁  | ✅   | タスク分解＋レビューの核 |
| 舎人  | ✅   | 実行主体         |
### 2. タスク処理フロー
```text
帝 → 関白 → 頭弁 → 舎人 → 頭弁レビュー → 完了
```
### 3. Redis
- tasks  
- agents   
- events:stream   
- inbox   
- lock
### 4. 状態管理
**イベント種類は削減**
- ORDER_CREATED    
- TASK_CREATED    
- TASK_ASSIGNED    
- TASK_STARTED    
- TASK_COMPLETED / FAILED    
- REVIEW_APPROVED / REJECTED    
- DASHBOARD_UPDATED
### 5. Executor層
### 6. UI
- 奏上（ダッシュボード）   
- タスク一覧   
- イベントストリーム   
- 簡易エージェント表示
### 7. 並列処理
- 舎人：2〜3体で固定    
- 頭弁：1体
### 8. タイムアウト制御
```text
doing > 120秒 → STALLED → retry
thinking > 300秒 → STALLED
```


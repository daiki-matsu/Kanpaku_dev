# テスト内容覚書
## 官職間の通信網（InboxとPub/Sub）の構築
### Inboxの確実性
StateManager.send_message() を実行後、宛先が受け取る（pop_inbox）前にシステムが停止しても、Redis内に inbox:toneri_1 のリストが残存していること。

### FIFO（先入れ先出し）の確認
複数回 send_message を行った際、pop_inbox で取り出される文が、投函した順番通りに出てくること。

### Pub/Subの即時性
redis-cli にて SUBSCRIBE notify:toneri_1 と打ち込んで待機した状態で send_message を実行した際、即座にメッセージが画面に表示されること。

## 状態遷移の厳格化（バリデーション）とリトライ管理
### 不正遷移の遮断
status="created" のタスクをいきなり status="completed" として update_task に渡した際、即座に ValueError が送出され、Redis/YAMLへの書き込みが行われないこと。

### リトライの加算
status="doing" のタスクに対し、execution.status="error" とした上で再度 update_task を呼び出した際、task.retry.count が 1 増えること。

### 限界の判定
上記を繰り返し、count が max_limit (例: 5) を超えた瞬間に、タスクのステータスが自動的に TaskStatus.FAILED へと書き換わり保存されること。

## 官職（エージェント）の待機・通知受信ループ
### ループの起動
別のターミナルからこの wait_for_orders() を実行し、「出仕」のログと共にプロセスが終了せずに待ち続けること。

### 狼煙と連動した起床
redis-cli または別のPythonスクリプトから StateManager.send_message() を呼び出した瞬間、エージェント側で即座に「狼煙検知」と「受領」のログが出力され、ステータスが working → idle へと遷移すること。

### ハートビートの確認
待機中であっても、Redis上の agents:{agent_id} の last_heartbeat の数値が毎秒更新され続けていること。

## 頭弁の政務分解とアサイン処理
### 頭弁の出仕
別のターミナルで TonobenAgent().wait_for_orders() を実行し、待機状態にします。

### 詔勅の投函
テスト用のスクリプトから、inbox:tonoben 宛に message_type="ORDER_RECEIVED", content={"instruction": "システム仕様書のひな型を作成せよ"} を持たせた Message を投函します（send_messageを使用）。

### 連鎖の確認
- 頭弁が狼煙に気づいて起床し、LLMを呼び出すログが出力されること。
- 状態遷移のバリデーションエラーが起きず、tasks に分解されたタスクが保存されること。
- inbox:toneri_1 に TASK_ASSIGNED の文が積まれていること。
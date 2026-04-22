# テスト内容覚書
## 排他制御（Redis Lock）の構築

### 正常な取得と解放
toneri_1 が try_acquire_lock("src/main.py", "toneri_1") を実行すると True が返り、【封印】のログが出ること。その後 release_lock が成功すること。

### 競合時の弾き（アトミック性の証明）
toneri_1 がロックを取得した直後、解放する前に toneri_2 が try_acquire_lock("src/main.py", "toneri_2") を実行した際、即座に False が返り、【競合】のログが出ること。

### 他者による不正解呪の防止
toneri_1 のロックを toneri_2 が release_lock しようとしても、無視（安全に失敗）されること。

## 舎人の実装とファイル操作処理
### 正常なタスク処理
頭弁からアサインされた状態のタスク（TASK_ASSIGNED）を投函した際、doing → LLM推論 → ファイルへの安全な書き込み（SafeIO使用） → reviewing という状態遷移が完璧に行われること。

### ロックの取得と解呪
書き込みの瞬間に【封印】と【解呪】のログが出力されること。

### エラー時のリトライ機構
ロック取得失敗やLLMエラー等が発生した際、タスクが強制的に failed になるのではなく、正しく assigned 状態に戻され、retry.count が加算されること（Sprint 2で組み込んだ大納言の掟の恩恵です）。

## 関白の実装とトップダウンフローの完成
### 三役揃い踏み
KanpakuAgent, TonobenAgent, ToneriAgent の3つの待機ループ（wait_for_orders()）を別々のターミナル（またはスレッド）で出仕させます。

### 帝の詔勅
テストスクリプトから、kanpaku 宛に message_type="MIKADO_ORDER", content={"order": "電卓アプリをPythonで作って"} を投函します。

### 連鎖の証明

- 【関白】が詔勅を受け取り、長文の指示書を生成して頭弁へ送る。

- 【頭弁】が指示書を受け取り、Sprint 2で組み込んだ仕組みでタスクを分解し、舎人へアサインする。

- 【舎人】がタスクを受け取り、Sprint 3で組み込んだ仕組みでファイルを生成し、完了報告を上げる。

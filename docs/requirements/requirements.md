---
codd:
  node_id: "req:kanpaku-requirements"
  type: requirement
  status: approved
  confidence: 0.95
---

# **Kanpaku(関白システム)**
## 実現したいこと
### 優先度：高
- AIに自律的かつ並列に動作してほしい 
- 各エージェントが役割を持った階層管理構造にしたい 
- AIがワチャワチャ演出付きで動くのを眺めたい 
- Thinking中の割り込みや、逆にずっと動かない状態を防止したい(将軍システムではHook) 
- 整合性駆動開発(CoDD)の導入 
- ダッシュボード(かんばんまたはタスクリストなど)のリアルタイム更新でプロジェクト状況を把握したい 
- ファイルの書き換え範囲を制限したい(特定のプロジェクトフォルダ内のみなど) 
- 戦国時代ではなく、平安時代の朝廷を模したい 
- 自己判断でのAgent Skills追加のように、自律的に精度を上げていってほしい 
### 優先度：中
- Androidからの管理 
- 判断基準のLoRA化
## アーキテクチャ全体像
| 将軍システム | 関白システム       | 説明                                                                                              | 使用モデル                                          |
| ------ | ------------ | ----------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| 上様     | 帝(Mikado)    | - ユーザー                                                                                          | - 人間                                           |
| 将軍     | 関白(Kanpaku)  | - ユーザーとの唯一のインターフェース<br>- ゴール設定<br>- 侍従への指示書作成<br>- Skill作成判断                                    | - gemma4-26B-A4B                               |
| 家老     | 侍従(Jiju)     | - 指示書からタスク分解<br>- 舎人/陰陽師のアサイン<br>- 実行結果のレビュー<br>- ダッシュボード更新<br>- エージェントの監視<br>- 内部的には複数プロセスでまわす | - gemma4-E2B                                   |
| 足軽     | 舎人(Toneri)   | - bloom_level:L1～L3を担当<br>- 並列実行<br>- ファイル操作(sandbox必須)                                         | - Bonsai-8B<br>- DeepSeek 6.7B<br>- gemma4-E2B |
| 軍師     | 陰陽師(Onmyoji) | - bloom_level:L4～L6を担当<br>- 思考専用(実行禁止)<br>- Skill用パターン抽出                                        | - gemma4-26B-A4B                               |
### 分岐基準
[引用：70年前の教育理論でAI部下を分類したら、家老が自分の降格を提案してきた上に、後任を初日から陥れていた](https://zenn.dev/shio_shoppaize/articles/shogun-bloom-routing)

| レベル | 英語         | 日本語 | 認知活動         | 例             |
| --- | ---------- | --- | ------------ | ------------- |
| L1  | Remember   | 記憶  | 検索する、一覧を出す   | 「このファイル探して」   |
| L2  | Understand | 理解  | 要約する、説明する    | 「このコード説明して」   |
| L3  | Apply      | 応用  | テンプレートに沿って作る | 「READMEを書いて」  |
| L4  | Analyze    | 分析  | 構造を調べる、原因を探る | 「なぜこのバグが起きた？」 |
| L5  | Evaluate   | 評価  | 比較する、判断する    | 「AとBどっちがいい？」  |
| L6  | Create     | 創造  | 設計する、新しく作る   | 「アーキテクチャ設計して」 |
### 呼び名
- エージェント → **官職**
- タスク → **政務**
## フロー対応表
"-"は状態変更なし

| Event              | task：状態変更      | Agent：状態変更      | 内容                      |
| ------------------ | -------------- | --------------- | ----------------------- |
| (ユーザー入力)           | -              | 帝               | チャットで指示                 |
| ORDER_CREATING     | -              | 関白：thinking     | 指示書作成開始                 |
| ORDER_CREATED      | -              | 関白：idle         | 指示書作成完了                 |
| TASK_CREATING      | -              | 侍従：thinking     | タスク作成開始                 |
| TASK_CREATED       | task：created   | 侍従：thinking     | タスク作成完了                 |
| TASK_ASSIGNED      | task：assigned  | 侍従：-            | タスク割り当て                 |
| TASK_STARTED       | task：doing     | 舎人/陰陽師：thinking | タスク実行開始                 |
| TASK_COMPLETED     | task：reviewing | 舎人/陰陽師：idle     | タスク目的達成                 |
| TASK_FAILED        | task：reviewing | 舎人/陰陽師：idle     | タスク要件未達                 |
| TASK_STALLED       | task：assigned  | 舎人/陰陽師：error    | タイムアウト<br>retry.count++ |
| REVIEW_STARTED     | -              | 侍従：working      | レビュー開始                  |
| REVIEW_APPROVED    | -              | 侍従：idle         | レビュー承認                  |
| REVIEW_REJECTED    | task：assigned  | 侍従：idle         | レビュー否認<br>retry.count++ |
| REVIEW_STALLED     | task：reviewing | 侍従：error        | タイムアウト<br>retry.count++ |
| DASHBOARD_UPDATING | -              | 侍従：thinking     | ダッシュボード更新開始             |
| DASHBOARD_UPDATED  | task：completed | 侍従：idle         | ダッシュボード更新完了             |
| (ユーザー確認)           | -              | 帝               | ダッシュボード確認               |
| ANALYZE_CREATING   | -              | 関白：thinking     | 分析開始                    |
| ANALYZE_CREATED    | -              | 関白：idle         | 分析完了+報告                 |
## 時間モデル
- thinking：
    - LLM待ちなので長くても正常
- doing：
    - I/Oなので止まったら異常
- heartbeat_interval：30秒 → 「書簡を作成中・・・」のようなメッセージ(スピナーもどき)を表示
- まとめ
```yaml
AgentTimePolicy:
  thinking:
    timeout: 300
  doing:
    timeout: 120
  idle:
    timeout: null
```
## Redis設計
### 1. tasks
- 型：Hash
- キー：tasks:{task_id}
#### 構成
- setting：タスク作成時の設定項目
	- type：research | review | analysis | file_write | file_move | file_delete ※今後も追加
	- priority：優先度を`1(低)～100(高)`で50を基準としてつける	
 - assingned：タスクアサイン時の設定項目
- answer：言語での回答と結果(success/failed)
- execution：ファイル操作時の対象ファイルと操作結果(success/failed)
- review：レビュー内容と点数と結果(PASS/FAIL)
	- 'execution'と'answer'両方の`success`を必須とする
- retry：リトライの回数と理由を記録
#### status一覧
1. created：作成後の状態、侍従(LLM)が担当
	```yaml
	id: T4
	status: created
	setting:
	  bloom_level: 3
	  depends_on:
	    - T2
	    - T3
	  priority: 1
	  goal: 主な気象用語の語源について調べ、まとめた内容をfile1.mdに保存する
	  command: 台風の語源を調べ、file1.mdに書き込んでください。
	  type: file_write
	assigned:
	  to: ''
	  echo_message: ''
	answer:
	  status: ''
	  summary: ''
	  details: ''
	execution:
	  status: ''
	  action: ''
	  path: ''
	  logs: ''
	review:
	  status: ''
	  score: 0
	  feedback: ''
	retry:
	  count: 0
	  reason: []
	timing:
	  created_at: 123456
	  updated_at: 123456
	```
2. doing：タスク実行中、review.feedbackに内容がある場合は反映する、タイムアウトの場合は`assigned`へ、舎人/陰陽師が担当
	```yaml
	id: T4
	status: doing
	setting:
	  bloom_level: 3
	  depends_on:
	    - T2
	    - T3
	  priority: 1
	  goal: 主な気象用語の語源について調べ、まとめた内容をfile1.mdに保存する
	  command: 台風の語源を調べ、file1.mdに書き込んでください。
	  type: file_write
	assigned:
	  to: toneri-2
	  echo_message: 歌を詠みに参りまする！
	answer:
	  status: ''
	  summary: ''
	  details: ''
	execution:
	  status: ''
	  action: ''
	  path: ''
	  logs: ''
	review:
	  status: ''
	  score: 0
	  feedback: ''
	retry:
	  count: 0
	  reason: []
	timing:
	  created_at: 123456
	  updated_at: 123458
	```
3. reviewing：舎人/陰陽師の実行内容をレビュー待ちまたはレビュー中、タイムアウトの場合はもう一度`reviewing`へ、侍従(CoDDコマンド)が担当
	- `codd validate`(整合性検証): フロントマターの記述形式、依存グラフの不整合、AIが「TODO」などで作業をサボっていないかといった形式的な不備を検査
	- `codd review`(品質レビュー): ドキュメントの種類に応じた意味的な品質を評価。
	- レビュー結果は数値化され、80点以上で「PASS」、問題がある場合「FAIL」
	```yaml
	id: T4
	status: reviewing
	setting:
	  bloom_level: 3
	  depends_on:
	    - T2
	    - T3
	  priority: 1
	  goal: 主な気象用語の語源について調べ、まとめた内容をfile1.mdに保存する
	  command: 台風の語源を調べ、file1.mdに書き込んでください。
	  type: file_write
	assigned:
	  to: toneri-2
	  echo_message: 歌を詠みに参りまする！
	answer:
	  status: success
	  summary: 語源は英語の'Typhoon'
	  details: 台風の語源は英語の'Typhoon'だと言われていますが、諸説あります。
	execution:
	  status: success
	  action: write
	  path: file1.md
	  logs: 書き込みに成功しました。
	review:
	  status: ''
	  score: 0
	  feedback: ''
	retry:
	  count: 1
	  reason:
	    - doing_timeout
	timing:
	  created_at: 123456
	  updated_at: 123465
	```
4. completed：レビュー承認(PASS)およびダッシュボードの更新をもってタスク終了、否認(FAIL)の場合は`assigned`へ、侍従(LLM)が担当
	```yaml
	id: T4
	status: completed
	setting:
	  bloom_level: 3
	  depends_on:
	    - T2
	    - T3
	  priority: 1
	  goal: 主な気象用語の語源について調べ、まとめた内容をfile1.mdに保存する
	  command: 台風の語源を調べ、file1.mdに書き込んでください。
	  type: file_write
	assigned:
	  to: toneri-2
	  echo_message: 歌を詠みに参りまする！
	answer:
	  status: success
	  summary: 語源は英語の'Typhoon'
	  details: 台風の語源は英語の'Typhoon'だと言われていますが、諸説あります。
	execution:
	  status: success
	  action: write
	  path: file1.md
	  logs: 書き込みに成功しました。
	review:
	  status: PASS
	  score: 82
	  feedback: 曖昧ですが内容は正しいです。ファイル書き込み成功です。
	retry:
	  count: 2
	  reason:
	    - doing_timeout
	    - reviewing_failed
	timing:
	  created_at: 123456
	  updated_at: 123470
	```
5. failed：retry.countが10回目の場合、そのタスクを処理ループからはずす。ユーザーがダッシュボードで確認できるようにする(赤字など強調表示)。
### 2. agents
- 型：Hash
- キー：agents:{agent_id}
- 構成
```yaml
status: working
current_task: T1
last_heartbeat: 123456
```
#### status一覧
- idle：待機状態
- thinking：LLM推論中、長くても正常
- working：ツール実行中(I/O、ファイル操作)、フリーズしたら異常
- error：再起動をかける対象
- retrying：再起動中
- stopped：停止中(わざと止めてる場合)
### 3. events streem
- 型：Streems
- キー：events:stream
- ストリーム処理
```bash
XADD events:stream * type TASK_STARTED task_id T1 agent toneri-1
```
### 4. inbox
- 型：Streams
- キー：inbox:{agent_id}
- データフロー
```
処理
↓
Event → stream(inbox:{agent_id})
↓
Pub/Subで通知(ナッジ)
↓
エージェント起動
↓
Streamからイベント取得
↓
処理
```
### 5. lock
- 型：Hash
- キー：lock:{filepath}
- ファイルの同時操作を防ぐ
- lock処理
```bash
SET lock:file1.md {by: toneri-2} EX 300 NX
```
- ロック所有者チェック
```python
if lock.by != self:
    deny()
```
- 解放時の安全確認
```lua
if redis.call("GET", key).by == my_id then
  return redis.call("DEL", key)
end
```
- ハートビート延長
長時間処理でTTL切れ防止
```bash
EXPIRE lock:file1.md 300
```
## 履歴設計
### 方針
- Redis = 現在状態
- YAML / log = 永続履歴
### 1. Task履歴(YAML)
- 保存パス
```text
/history/tasks/T1.yaml
```
- 構成
```yaml
task_id: T1
history:
  - status: created
    timestamp: 123456
  - status: assigned
    timestamp: 123457
  - status: doing
    timestamp: 123458
  - status: reviewing
    timestamp: 123459
  - status: completed
```
### 2. Event履歴(YAML)
- 保存パス
```text
/history/events/2026-04-09.yaml
```
- 構成
```yaml
- event: TASK_STALLED  
  task_id": T4
  by": system
  meta: 
    - retry: true
      reason: timeout
  timestamp: 123456
```
### 3. State履歴(ログ)
- 保存パス
```text
/logs/state.log
```
- 構成
```text
[TASK] T1 assigned → doing
[AGENT] toneri-1 idle → working
```
### 4. Agent履歴
- 保存パス
```text
/history/agents/toneri-1.yaml
```
- 構成
```yaml
agent_id: toneri-1
history:
  - task: T1
    status: working
    duration: 12s
```
### 5. skill適用履歴
- 保存パス
```text
/logs/skill_accepted.log
```
- 構成
```yaml
task_id: T4
skill_id: S-001
result: success
```
## Executor層
LLMによるファイル操作を実行するための層
### 実装イメージ
- 呼び出し側
```python
if cmd["type"] == "file_write":
    safe_write(cmd["path"], cmd["content"])
```
- sandbox制御
```python
def safe_write(path):
    if not path.startswith("/project/"):
        raise Exception("Forbidden")
```
## Skill自己進化
- Skillは「命令」ではなく「傾向」
- プロンプト補助として使う
### 登録フロー
1. TASK_COMPLETED (review: PASS, score >= 80)
2. ANALYZE_CREATING(関白)
3. パターン抽出(陰陽師)
4. Skill化(構造化)
5. VectorDBへ保存
### 検索フロー
1. TASK_CREATED/REVIEW_REJECTED
2. 類似タスク検索
	検索の優先順位
	1. success_rate
	2. 類似度
	3. usage_count
3. 上位3件取得
4. プロンプトに注入
5. TASK_ASSIGNED
### Skill進化(自己強化ループ)
```yaml
loop:
  success:
    - usage_count++
    - success_rate更新

  failure:
    - failure_pattern追加
    - success_rate低下

  定期処理:
    - 低スコアskill削除
    - 類似skill統合
```
### Skillデータ構造
```yaml
skill_id: S-001
name: 調査→要約→ファイル保存
description: 調査系タスクを安全に完了する手順
conditions:
  type: research
  bloom_level:
    - 1
    - 2
    - 3
  includes_file_write: true
steps:
  - 情報収集
  - 信頼性確認
  - 要約生成
  - ファイル書き込み
prompt_template: '以下の手順で実行してください: ...'
success_pattern:
  execution: success
  answer: success
  review_score: '>=80'
failure_pattern:
  - 情報不足
  - ファイル書き込み失敗
embedding_text: 調査 タスク 要約 ファイル書き込み 成功パターン
```
### VectorDB
Chromaを使用
#### コレクション構成
```python
collection: skills
```

```python
{
  id: skill_id,
  embedding: embedding_text,
  metadata: {
    type: "research",
    bloom_level: [1,2,3],
    success_rate: 0.92,
    usage_count: 12
  },
  document: JSON.stringify(skill)
}
```
## UI
- 疑似マルチエージェント：実際はログを1か所に吐き出すだけ
- tmux + 擬似CLI：ログをエージェントごとに別枠で表示
- ダッシュボード：Markdownプレビュー
## LLM実行環境
Ollamaとllama.cppの併用
### 使用候補モデル
- Bonsai-8B(llama.cpp)
- gemma4-26B-A4B(Ollama)
- gemma4-E2B(Ollama)
- llm-jp-4-8B(llama.cpp)
- llm-jp-4-32B(llama.cpp)
- DeepSeek Coder 6.7B(llama.cpp)
### PCスペック
| 項目 | 内容 |
| GPU (VRAM) | NVIDIA RTX 2070 SUPER (8GB) |
| システムメモリ (RAM) | 64GB DDR4-3200 |
| CPU | Core i5-13600KF (14C/20T) |

# **Kanpaku(関白システム)** 仕様書
## 実現したいこと
### 優先度：高
- AIに自律的かつ並列に動作してほしい 
- 各エージェントが役割を持った階層管理構造にしたい 
- AIがワチャワチャ演出付きで動くのを眺めたい 
- Thinking中の割り込みや、逆にずっと動かない状態を防止したい(将軍システムではHook) 
- ダッシュボード(かんばんまたはタスクリストなど)のリアルタイム更新でプロジェクト状況を把握したい 
- ファイルの書き換え範囲を制限したい(特定のプロジェクトフォルダ内のみなど) 
- 戦国時代ではなく、平安時代の朝廷を模したい 
- 自己判断でのagent Skills追加のように、自律的に精度を上げていってほしい
### 優先度：中
- Androidからの管理 
- 判断基準のLoRA化
## アーキテクチャ全体像
| 将軍システム | 関白システム       | 説明                                                                                              | 使用モデル                                          |
| ------ | ------------ | ----------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| 上様     | 帝(Mikado)    | - ユーザー                                                                                          | - 人間                                           |
| 将軍     | 関白(Kanpaku)  | - ユーザーとの唯一のインターフェース<br>- ゴール設定<br>- 頭弁への指示書作成<br>- Skill作成判断                                    | - gemma4-26B-A4B                               |
| 家老     | 頭弁(Tonoben)  | - 指示書からタスク分解<br>- 舎人/陰陽師のアサイン<br>- 実行結果のレビュー<br>- ダッシュボード更新<br>- エージェントの監視<br>- 内部的には複数プロセスでまわす | - gemma4-E2B                                   |
| 足軽     | 舎人(Toneri)   | - bloom_level:L1～L3を担当<br>- 並列実行<br>- ファイル操作(sandbox必須)                                         | - Bonsai-8B<br>- DeepSeek 6.7B<br>- gemma4-E2B |
| 軍師     | 陰陽師(Onmyoji) | - bloom_level:L4～L6を担当<br>- 思考専用(実行禁止)<br>- Skill用パターン抽出                                        | - gemma4-26B-A4B                               |
### 分岐基準
[引用：70年前の教育理論でAI部下を分類したら、家老が自分の降格を提案してきた上に、後任を初日から陥れていた](https://zenn.dev/shio_shoppaize/articles/shogun-bloom-routing)
- **Bloom's Taxonomy(ブルームの分類学)** に従った処理分岐

| レベル | 英語         | 日本語 | 認知活動         | 例             | 担当エージェント |
| --- | ---------- | --- | ------------ | ------------- | -------- |
| L1  | Remember   | 記憶  | 検索する、一覧を出す   | 「このファイル探して」   | 舎人       |
| L2  | Understand | 理解  | 要約する、説明する    | 「このコード説明して」   | 舎人       |
| L3  | Apply      | 応用  | テンプレートに沿って作る | 「READMEを書いて」  | 舎人       |
| L4  | Analyze    | 分析  | 構造を調べる、原因を探る | 「なぜこのバグが起きた？」 | 陰陽師      |
| L5  | Evaluate   | 評価  | 比較する、判断する    | 「AとBどっちがいい？」  | 陰陽師      |
| L6  | Create     | 創造  | 設計する、新しく作る   | 「アーキテクチャ設計して」 | 陰陽師      |
### 呼び名
- エージェント → **官職**
- タスク → **政務**
- ログ → **日記**
- ダッシュボード(ユーザーへの報告) → **奏上**
- プロジェクトチーム → **行事所**
- skill → **抄**
- サンドボックス → **結界**
## フロー対応表
- "-"は状態変更なし

| event              | task：状態変更      | agent：状態変更      | 内容                      |
| ------------------ | -------------- | --------------- | ----------------------- |
| (ユーザー入力)           | -              | 帝               | チャットで指示                 |
| ORDER_CREATING     | -              | 関白：thinking     | 指示書作成開始                 |
| ORDER_CREATED      | -              | 関白：idle         | 指示書作成完了                 |
| TASK_CREATING      | -              | 頭弁：thinking     | タスク作成開始                 |
| TASK_CREATED       | task：created   | 頭弁：thinking     | タスク作成完了                 |
| TASK_ASSIGNED      | task：assigned  | 頭弁：-            | タスク割り当て                 |
| TASK_STARTED       | task：doing     | 舎人/陰陽師：thinking | タスク実行開始                 |
| TASK_COMPLETED     | task：reviewing | 舎人/陰陽師：idle     | タスク目的達成                 |
| TASK_FAILED        | task：reviewing | 舎人/陰陽師：idle     | タスク要件未達                 |
| TASK_STALLED       | task：assigned  | 舎人/陰陽師：error    | タイムアウト<br>retry.count++ |
| REVIEW_STARTED     | -              | 頭弁：working      | レビュー開始                  |
| REVIEW_APPROVED    | -              | 頭弁：idle         | レビュー承認                  |
| REVIEW_REJECTED    | task：assigned  | 頭弁：idle         | レビュー否認<br>retry.count++ |
| REVIEW_STALLED     | task：reviewing | 頭弁：error        | タイムアウト<br>retry.count++ |
| DASHBOARD_UPDATING | -              | 頭弁：thinking     | ダッシュボード更新開始             |
| DASHBOARD_UPDATED  | task：completed | 頭弁：idle         | ダッシュボード更新完了             |
| (ユーザー確認)           | -              | 帝               | ダッシュボード確認               |
| ANALYZE_CREATING   | -              | 関白：thinking     | 分析開始                    |
| ANALYZE_CREATED    | -              | 関白：idle         | 分析完了+報告                 |
## Redis設計
- シリアライズにはJSONを仕様
### 1. tasks
- 型：hash
- キー：tasks:{task_id}
#### 構成(completed時点の例)
```json
{
  "id": "2_4",
  "status": "completed",
  "setting": {
	"bloom_level": 3,
	"depends_on": [
	  "2_2",
	  "2_3"
	],
	"priority": 1,
	"goal": "主な気象用語の語源について調べ、まとめた内容をfile1.mdに保存する",
	"command": "台風の語源を調べ、file1.mdに書き込んでください。",
	"type": "file_write"
  },
  "assigned": {
	"to": "toneri-2",
	"echo_message": "歌を詠んで参りました！"
  },
  "answer": {
	"status": "success",
	"summary": "語源は英語の'Typhoon'",
	"details": "台風の語源は英語の'Typhoon'だと言われていますが、諸説あります。"
  },
  "execution": {
	"status": "success",
	"action": "write",
	"path": "file1.md",
	"logs": "書き込みに成功しました。"
  },
  "review": {
	"status": "success",
	"score": 82,
	"feedback": "曖昧ですが内容は正しいです。ファイル書き込み成功です。"
  },
  "retry": {
	"count": 2,
	"reason": [
	  "doing_timeout",
	  "reviewing_failed"
	]
  },
  "timing": {
	"created_at": 123456,
	"updated_at": 123470
  }
}
```
#### status一覧(内容遷移)
1. created：作成後の状態、頭弁(LLM)が担当
	- id：タスクID({タスク分割の実行回数連番} _ {その分割内の連番})で表す
	- status："created"
	- setting：タスク作成時の設定項目
		- bloom_level：1(L1)～6(L6)
		- depends_on：依存先タスク、配列で複数設定可
		- priority：優先度を`1(低)～100(高)`で50を基準としてつける	
		- goal：指示書に設定されたタスク全体の最終目標
		- command：エージェントへの指示内容
		- type：research | review | analysis | file_write | file_move | file_delete | etc...
	- timing：
		- created_at：作成日時
		- updated_at：更新日時
2. assigned：エージェントを設定時に状態変更、条件は認知レベル(L1〜L6) + 役割 + 空き状況、頭弁(コード )が担当
	- status："assigned"
	- assingned：タスクアサイン時の設定項目
		- to：割り当てられたエージェント
		- echo_message：エージェントのタスク完了時のメッセージ
	- timing.updated_at：更新日時
3. doing：タスク実行時に状態変更、review.feedbackに内容がある場合はプロンプトに反映する、タイムアウトの場合は`assigned`へ、舎人/陰陽師が担当
	- status："doing"
	- timing.updated_at：更新日時
4. reviewing：タスク実行後に状態変更、舎人/陰陽師の実行内容のレビュー待ち/レビュー中を表す、タイムアウトの場合はもう一度`reviewing`へ、頭弁(LLM)が担当
	- status："reviewing"
	- answer：
		- status：タスク結果(success/failed)
		- summary：タスク概要
		- details：タスク詳細
	- execution：
		- status：処理実行結果(success/failed)
		- action：処理実行内容
		- path：処理実行対象パス
		- logs：処理実行結果詳細
	- timing.updated_at：更新日時
5. completed：レビュー承認(success)およびダッシュボードの更新後に状態変更、'execution'と'answer'両方の`success`を必須とする、否認(failed)の場合は`assigned`へ、頭弁(LLM)が担当
	- status："completed"
	- review：
		- status：レビュー結果(success/failed)
		- score：レビュー点数
		- feedback：レビュー内容
	- timing.updated_at：更新日時
6. failed：retry.countが10回目の場合、そのタスクを処理ループからはずす。ユーザーがダッシュボードで確認できるようにする(赤字など強調表示)。
	- status："failed"
	- retry：
		- count：リトライ回数
		- reason：失敗ごとの理由、配列で設定
### 2. dag
- 型：set
- キー：
	- dag:dependents:{task_id}：影響先リスト = 自分が完了したら通知すべきタスクのSet
	- dag:dependencies:{task_id}：依存先リスト = まだ完了を待っているタスクのSet
- タスクの依存関係をまとめている
- タスクが完了したら、dependencies(依存先リスト)から値を削除する
	- dependenciesが空(依存なし)のタスクはアサイン対象となる
#### 例
- 依存関係図
```text
task:2_2 ─┬─ task:2_4
task:2_3 ─┘
```
- dag:dependents:2_2 = [ "2_4" ]
- dag:dependents:2_3 = [ "2_4" ]
- dag:dependencies:2_4 = [ "2_2", "2_3" ]
### 3. agents
- 型：hash
- キー：agents:{agent_id}
- 構成
```json
{
  "id": "toneri_1",
  "role": "舎人",
  "status": "idle",
  "current_task_id": null,
  "last_heartbeat": 1713355200.0
}
```
#### status一覧
- idle：待機状態
- thinking：LLM推論中、長くても正常
- working：ツール実行中(I/O、ファイル操作)、フリーズしたら異常
- error：再起動をかける対象
- retrying：再起動中
- stopped：停止中(わざと止めてる場合)
#### 状態監視
- 頭弁が定期的に全エージェントの`status`をチェックし、条件に沿って下記の処理を行う
- idle：何もしない
- thinking：300秒経過でタイムアウト(LLM待ちなので長くても正常)
- working：120秒経過でタイムアウト(I/Oなので止まったら異常)
- error：発見次第即時処理
- retrying：処理中のため何もしない
- stopped：何もしない
### 4. inbox
- 型：stream
- キー：inbox:{agent_id}, inbox:{agent_id} _ {種類}
- データフロー
```
処理
↓
event → stream(inbox:{agent_id})
↓
Pub/Subで通知(ナッジ)
↓
エージェント起動
↓
Streamからイベント取得
↓
処理
```
#### 種類
- 関白：inbox:kanpaku
	- 帝からのメッセージ
- 頭弁：
	- inbox:tonoben_order：関白からの指示書
	- inbox:tonoben_pending：依存関係を満たしていないタスク
		- タスク完了時、新しく依存関係を満たしたタスクがないかチェックする
	- inbox:tonoben_review：舎人/陰陽師の完了タスク
- 舎人：inbox:toneri
	- 舎人で共通 (Consumer Group)
	- Redis側でタスクの分配を行う
	- 将来、舎人ごとの役割/ペルソナ/モデルが分かれるようになったら、複数作成する
- 陰陽師：inbox:onmyoji
### 5. channel
- 型：stream
- キー：channel:{agent_id}
- 疑似CLIの各枠の表示内容
	- 関白のみ、チャットボットのように帝の入力も表示する
### 6. event_stream
- 型：streem
- キー：events:stream
- ストリーム追加
```bash
XADD events:stream * type {YYYY-MM-DD HH:MM:DD} {event} task:{task_id} agent:{agent_id}
```
### 7. lock
- 型：string
- キー：lock:{filepath}
- ファイルの同時操作を防ぐ、キーが存在したらロックされている
- 値にはどのエージェントによってロックされているかを入れる
- エージェントが`error`になったら強制解除する
- lock処理
```bash
SET lock:file1.md {agent_id} EX 300 NX
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
### 8. system_state
- 型：hash
- キー：system:state
- システム全体の状態を表す
- ダッシュボードの表示内容などに使用予定
```json
{
  "active_agents": 2,
  "tasks_doing": 1,
  "tasks_completed": 5,
  "last_updated": 1713355230.0
}
```
## 履歴設計
- yamlを使用
### 方針
- Redis = 現在状態
- YAML = 永続履歴
### 1. task履歴(YAML)
- 保存パス
```text
/history/tasks/T1.yaml
```
- 構成
```yaml
task_id: 1_1
history:
  - status: created
    timestamp: '2026-04-09 13:12:10'
  - status: assigned
    timestamp: '2026-04-09 13:12:20'
  - status: doing
    timestamp: '2026-04-09 13:12:30'
  - status: reviewing
    timestamp: '2026-04-09 13:12:40'
  - status: completed
    timestamp: '2026-04-09 13:12:50'
```
### 2. event履歴(YAML)
- 保存パス
```text
/history/events/2026-04-09.yaml
```
- 構成
```yaml
- event: TASK_STALLED  
  task_id: 1_4
  by: system
  meta: 
    - retry: true
      reason: timeout
  timestamp: '2026-04-09 13:12:35'
```
### 3. state履歴(YAML)
- 保存パス
```text
/logs/states/2026-04-09.yaml
```
- 構成
```yaml
- type: task
  id: 1_1
  from: assigned
  to: doing
  changed_at: '2026-04-09 13:12:20'
- type: agent
  id: toneri-1
  from: idle
  to: working
  changed_at: '2026-04-09 13:12:20'
```
### 4. agent履歴
- 保存パス
```text
/history/agents/toneri-1.yaml
```
- 構成
```yaml
agent_id: toneri-1
history:
  - task: 1_1
    status: working
    duration: 12s
    finished_at: '2026-04-09 13:12:40'
```
### 5. order履歴
- 保存パス
```text
/history/orders/2026-04-09.yaml
```
- 構成
	- input：ユーザー入力
	- type：required | analysis | etc...
	- goal：目標
	- order：頭弁に送る指示書
```yaml
- id: 1
  input: '...'
  type: required
  goal: '...'
  order: '...'
  created_at: '2026-04-09 13:10:00'
  updated_at: '2026-04-09 13:11:00'
```
### 6. skill適用履歴
- 保存パス
```text
/logs/skill_accepted.log
```
- 構成
```yaml
task_id: 1_4
skill_id: S_1
result: success
accepted_at: '2026-04-09 13:20:40'
```
## レビュー処理
### 2段階レビュー構造
1. 機械チェック：
	 - `execution.status` == success or null チェック
		 - failedの場合、`review.feedback`に`execution.log`
	 - `answer.status` == success チェック
		 - failedの場合、`review.feedback`に`answer.summary`
 2. LLMレビュー
	- 目的：{goal}
	- 実行結果：{answer.details}
	- 評価基準：
		- 要件を満たしているか
		- 明らかな誤りがないか
		- 不完全ではないか
### 出力内容
- status: success({score}>=80) or failed({score}<80)
- score: 1 ～ 100
- feedback: {理由}
## Executor層
- LLMによるファイル操作を実行するための層
	- safe_write
	- safe_read
- MCPの`CallTool` 仕様に寄せて作成
- I/Oはyamlで管理
### input(エージェント → Executor層)

```yaml
method: tools/call
params:
  name: file_write
  arguments:
    path: src/main.py
    content: |
      def hello():
          print('Hello, Kanpaku!')
```
### output(Executor層 → エージェント)
- OK時
```yaml
content:
  - type: text
    text: File successfully written to src/main.py
isError: false
```
- NG時
```yaml
content:
  - type: text
    text: Permission denied: Cannot write outside of /project workspace.
isError: true
```
### プリプロセッサ
- IN/OUTが正しい書式で行われるようにする
- 「Markdown装飾」を外す
- yamlの書式に整える
### 実装イメージ
- 呼び出し側 
```python
import yaml
import os
from pathlib import Path

# --- サンドボックス制御 ---
PROJECT_ROOT = Path("/project").resolve()

def safe_write(path_str: str, content: str) -> str:
    """指定されたパスに書き込む(サンドボックス制限付き)"""
    target_path = (PROJECT_ROOT / path_str).resolve()
    
    # セキュリティチェック: PROJECT_ROOT配下か確認 (ディレクトリトラバーサル対策)
    if not str(target_path).startswith(str(PROJECT_ROOT)):
        raise PermissionError(f"Forbidden: Cannot write outside of {PROJECT_ROOT}")
    
    # ディレクトリが存在しない場合は作成
    target_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    return f"Success: File written to {path_str}"

# --- Executor (ディスパッチャ) ---
def execute_tool(yaml_input: str) -> str:
    """エージェントからのYAML出力を受け取り、ツールを実行してYAMLで返す"""
    try:
        cmd = yaml.safe_load(yaml_input)
        
        # フォーマット検証
        if cmd.get("method") != "tools/call":
            raise ValueError("Invalid method. Expected 'tools/call'")
            
        tool_name = cmd["params"]["name"]
        args = cmd["params"]["arguments"]
        
        # 実行と分岐
        if tool_name == "file_write":
            result_text = safe_write(args["path"], args["content"])
        else:
            raise NotImplementedError(f"Tool '{tool_name}' not found.")
            
        # 成功時のレスポンス(MCP風)
        response = {
            "content": [{"type": "text", "text": result_text}],
            "isError": False
        }
        
    except Exception as e:
        # 失敗時のレスポンス
        response = {
            "content": [{"type": "text", "text": f"Error: {str(e)}"}],
            "isError": True
        }
        
    return yaml.dump(response, allow_unicode=True, sort_keys=False)
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
- yamlで管理
```yaml
skill_id: S-1
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
- Chromaを使用
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
- Streamlitで開発
```
+-----------------------------------------------------------------------+
|                              [ プロジェクト名 ]                         |
+---------------------------+-----------------------+-------------------+
| 関白                      | 奏上                  | 政務(タスク)詳細  |
| +-----------------------+ | (ダッシュボード)      |                   |
| | 詔勅(入力欄)           | |                       |                   |
| +-----------------------+ |                       |                   |
+-------------+-------------+                       |                   |
| 頭弁        | 陰陽師      |                       |                   |
|             |             |                       |                   |
+---+---+---+---+-----------+-----------------------+-------------------|
|舎1|舎2|舎3|舎4|           | イベントストリーム                        |
+---+---+---+---+-----------+-------------------------------------------+
```
### 奏上(ダッシュボード)
- Markdownプレビュー
```Markdown
# 📜 奏上

## 🚨 要対応
- FAILタスク
	  - {task_id}🔥 {FAILタイムスタンプ}
- retry多発タスク
	  - {task_id}🔁 x{retry数}

## ⚙️ 進行中
- doingタスク数
- reviewingタスク数

## ✅ 完了
- 今日の完了数
- 成功率
```
### 擬似CLI
- エージェントごとに別枠で表示
- 各エージェント枠の上部に現在のステータスを表示："{指定色の丸}   {ステータス}"で表示
	- idle：グレー
	- thinking：青
	- working：緑
	- error：赤
	- retrying：オレンジ
- イベントを平安貴族風のメッセージで表示
- スピナーもどき
	- thinking/workingの場合、30秒間隔で平安貴族風の作業中メッセージを表示する
		- 別スレッドでタイムカウントを行う
		- 例：thinking → "書簡を作成中…(30秒)"
		- 例：working → "裏山で狩り中…(retry 3 : 60秒)"
- クリック → 対応タスクハイライト
### 政務(タスク)詳細
- 全タスクをプルダウンを閉じた状態で一覧表示
	- | id | status | priority | command | agent(未割当時は空欄) |
- タスクをクリックするとプルダウンを開いて詳細情報を表示
	- tasksの項目の内、値があるものをすべて表示
- idの昇順
- status(チェックボックス)/priority(範囲)/agent(チェックボックス)でフィルタ
- クリック → 担当エージェント強調
### 詔勅(ユーザーメッセージ) 入力欄
- ユーザーが関白に向けたメッセージを入力できる
### イベントストリーム
- 生のイベントログを表示
## LLM実行環境
- Ollamaとllama.cppの併用
### 使用候補モデル
- Bonsai-8B(llama.cpp)
- gemma4-26B-A4B(Ollama)
- gemma4-E2B(Ollama)
- llm-jp-4-8B(llama.cpp)
- llm-jp-4-32B(llama.cpp)
- DeepSeek Coder 6.7B(llama.cpp)

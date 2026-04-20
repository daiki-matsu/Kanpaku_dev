import yaml
import uuid
import time
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from typing import List, Dict, Any
from agents.base_agent import BaseAgent
from models.message import Message
from models.tasks import Task, TaskStatus, SettingInfo, AssignedInfo, TimingInfo

# 献上された connect_llm 側のラッパーとYAMLフィルターを読み込む
from connect_llm.ollama_wrapper import ollamaWrapper 
from connect_llm.yaml_filter import filter_yaml_document # ※yaml文字列を抽出・整形する関数

class TonobenAgent(BaseAgent):
    """朝廷の実務を取り仕切る"""
    
    # ※システム側で保持するタスク分割の実行回数（実際の運用ではRedis等で永続化・カウントアップを推奨します）
    execution_count = 1 

    def __init__(self):
        super().__init__(agent_id="tonoben", role="頭弁")
        self.llm = ollamaWrapper()

    def process_message(self, message: Message) -> None:
        if message.message_type == "ORDER_RECEIVED":
            self._decompose_and_assign(message)
        else:
            print(f"【頭弁】承知できぬ用件ゆえ、静観いたしまする。({message.message_type})")


    def _decompose_and_assign(self, message: Message) -> None:
        instruction = message.content.get("instruction", "")
        print(f"【頭弁】関白殿下より詔勅を賜りました。「{instruction}」...これより政務を分解いたしまする。")

        # 1. 高精度化されたタスク分解プロンプト（Chain of Thought 導入）
        prompt = f"""
        あなたはシステム開発プロジェクトを指揮する優秀なマネージャーです。
        与えられた「指示」を分析し、自律AIエージェントが実行可能な粒度のサブタスクに分解してください。

        指示: {instruction}

        【思考プロセス（必ずこの順序で思考すること）】
        1. 指示の全体目標を正確に把握する。
        2. 目標達成に必要な具体的な手順をステップ順に洗い出す。
        3. 各手順の依存関係（どのタスクが完了しないと次が始まらないか）を整理する。
        4. 各手順に対し、以下の定義に従って適切な属性（bloom_level, type, priority）を割り当てる。

        【属性の定義】
        * bloom_level (1〜6の整数):
        1: 記憶 (検索する、一覧を出す)
        2: 理解 (要約する、説明する)
        3: 応用 (テンプレートに沿って作る)
        4: 分析 (構造を調べる、原因を探る)
        5: 評価 (比較する、判断する)
        6: 創造 (設計する、新しく作る)
        * priority (1〜100の整数):
        1が最低、100が最高。標準的な優先度は50とする。
        * type (以下から選択):
        research, review, analysis, planning, file_write, file_read, file_edit, file_move, file_delete, code_execution, web_search, communication, etc...

        【出力フォーマット要件】
        以下のYAML形式のリストのみを出力してください。例文に引っ張られないよう、goalとcommandには「今回の指示」に基づいた具体的な内容を記述すること。

        ```yaml
        - step_id: "step_1"
          depends_on: []
          bloom_level: <1〜6の整数>
          priority: <1〜100の整数>
          goal: "<指示書に設定されたタスク全体の最終目標>"
          command: "<エージェントが実行すべき具体的なアクション>"
          type: "<指定リストから選択>"
          target_agent: "toneri_1"
        - step_id: "step_2"
          depends_on: ["step_1"]
          bloom_level: <1〜6の整数>
          # 以降、必要な手順の数だけ繰り返す
        """
        
        try:
            llm_response = self.llm.generate(prompt) 
            yaml_str = filter_yaml_document(llm_response)
            sub_tasks_data: List[Dict[str, Any]] = yaml.safe_load(yaml_str)
            
            print(f"【頭弁】思考完了。政務を {len(sub_tasks_data)} つのタスクに分解いたしました。")

            # 2. タスクIDの採番と依存関係の解決
            # 実行回数の連番 (X) _ その分割内の連番 (Y) を生成
            id_map = {}
            for index, data in enumerate(sub_tasks_data, start=1):
                if "step_id" in data:
                    # 例: "1_1", "1_2" というIDを生成
                    id_map[data["step_id"]] = f"{self.execution_count}_{index}"

            current_time = int(time.time())
            
            # 3. 分解されたタスクの登録とアサイン
            for data in sub_tasks_data:
                real_task_id = id_map.get(data.get("step_id"))
                if not real_task_id:
                    continue
                
                # 依存関係（depends_on）の解決（step_X を 1_X に変換）
                real_depends_on = [
                    id_map[dep_step] for dep_step in data.get("depends_on", [])
                    if dep_step in id_map
                ]
                
                # タスクのインスタンス化
                new_task = Task(
                    id=real_task_id,
                    status=TaskStatus.CREATED,
                    setting=SettingInfo(
                        bloom_level=data.get("bloom_level", 1),
                        depends_on=real_depends_on,
                        priority=data.get("priority", 50), # 基準値50
                        goal=data.get("goal"),
                        command=data.get("command"),
                        type=data.get("type", "general")
                    ),
                    timing=TimingInfo(created_at=current_time)
                )
                self.state_manager.update_task(new_task, event_type="TASK_CREATED")
                
                # アサイン処理と通信
                new_task.status = TaskStatus.ASSIGNED
                new_task.timing.updated_at = int(time.time())
                new_task.assigned = AssignedInfo(
                    to=data.get("target_agent", "toneri_1"),
                    echo_message="頭弁より舎人へ、速やかなる実行を命ず。"
                )
                self.state_manager.update_task(new_task, event_type="TASK_ASSIGNED")
                
                assign_msg = Message(
                    sender_id=self.agent_id,
                    receiver_id=new_task.assigned.to,
                    message_type="TASK_ASSIGNED",
                    task_id=real_task_id,
                    content={"instruction": new_task.setting.command}
                )
                self.state_manager.send_message(assign_msg)
                
            print(f"【頭弁】すべての舎人への割り振りが完了いたしました。（実行ID: {self.execution_count}）")
            self.execution_count += 1 # 次回の分解に備えてカウントアップ

        except Exception as e:
            print(f"【頭弁エラー】政務の分解中に不測の事態が発生いたしました。: {e}")
            raise e
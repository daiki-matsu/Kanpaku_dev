import yaml
import uuid
import time
import sys
import os
import importlib
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from typing import List, Dict, Any
from agents.base_agent import BaseAgent
from models.message import Message
from models.tasks import Task, TaskStatus, SettingInfo, AssignedInfo, TimingInfo
from utility.messages import HeianMessages
from utility.prompts import SystemPrompts

# グローバル変数としてPROMPTSを設定
PROMPTS = SystemPrompts()

# connect_llm  import with reload
import connect_llm.ollama_wrapper
from connect_llm.ollama_wrapper import ollamaWrapper 
from connect_llm.yaml_filter import filter_yaml_document # ※yaml文字列を抽出・整形する関数
from connect_llm.env_loader import get_env_var

class TonobenAgent(BaseAgent):
    """朝廷の実務を取り仕切る"""
    
    # ※システム側で保持するタスク分割の実行回数（実際の運用ではRedis等で永続化・カウントアップを推奨します）
    execution_count = 1 

    def __init__(self):
        super().__init__(agent_id="tonoben", role="頭弁")
        host = get_env_var("OLLAMA_HOST_2", None)
        self.llm = ollamaWrapper(model_name="gemma4:e2b", host=host)

    def process_message(self, message: Message) -> None:
        if message.message_type == "ORDER_RECEIVED":
            self._decompose_and_assign(message)
        else:
            print(HeianMessages.TONOBEN_IGNORE.format(msg_type=message.message_type))


    def _decompose_and_assign(self, message: Message) -> None:
        instruction = message.content.get("instruction", "")
        print(HeianMessages.TONOBEN_ORDER_RECEIVED.format(instruction=instruction))

        # 1. 高精度化されたタスク分解プロンプト（Chain of Thought 導入）
        prompt = PROMPTS.TONOBEN_TASK_DECOMPOSITION.format(instruction=instruction)
        
        try:
            llm_response = self.llm(prompt) 
            yaml_str = filter_yaml_document(llm_response, priority_keys=['step_id'])
            sub_tasks_data: List[Dict[str, Any]] = yaml.safe_load(yaml_str)
            
            print(HeianMessages.TONOBEN_DECOMPOSED.format(count=len(sub_tasks_data)))

            # 2. タスクIDの採番と依存関係の解決
            # 実行回数の連番 (X) _ その分割内の連番 (Y) を生成
            id_map = {}
            for index, data in enumerate(sub_tasks_data, start=1):
                if "step_id" in data:
                    # 例: "1_1", "1_2" というIDを生成
                    id_map[data["step_id"]] = f"{self.execution_count}_{index}"

            current_time = int(time.time())
            
            # 3. 分解されたタスクの登録とアサイン
            for index, data in enumerate(sub_tasks_data):
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
                # tneri-1とtoneri-2に交互に割り当てる
                target_agent = "toneri_1" if index % 2 == 0 else "toneri_2"
                new_task.assigned = AssignedInfo(
                    to=data.get("target_agent", target_agent),
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
                
            print(HeianMessages.TONOBEN_ASSIGN_COMPLETE.format(execution_id=self.execution_count))
            self.execution_count += 1 # 次回の分解に備えてカウントアップ

        except Exception as e:
            print(HeianMessages.TONOBEN_ERROR.format(error=e))
            raise e
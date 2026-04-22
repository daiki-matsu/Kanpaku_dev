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

# YAML filter utility
def filter_yaml_document(text: str, priority_keys: list = None) -> str:
    """Filter and extract YAML document from text"""
    import yaml
    import json
    
    # Try to parse as JSON first (for structured outputs)
    try:
        if '{' in text and '}' in text:
            start = text.find('{')
            end = text.rfind('}') + 1
            json_content = text[start:end]
            data = json.loads(json_content)
            return yaml.dump(data, default_flow_style=False, allow_unicode=True)
    except:
        pass
    
    # Fallback to YAML extraction
    lines = text.split('\n')
    yaml_lines = []
    in_yaml_block = False
    
    for line in lines:
        if line.strip().startswith('```yaml'):
            in_yaml_block = True
            continue
        elif line.strip() == '```' and in_yaml_block:
            in_yaml_block = False
            continue
        elif in_yaml_block or line.strip().startswith('-') or ':' in line:
            yaml_lines.append(line)
    
    return '\n'.join(yaml_lines)

# Environment variable loader
def get_env_var(var_name: str) -> str:
    """Get environment variable value"""
    import os
    return os.getenv(var_name, "")

from agents.llm_client import LLMClient
from src.infrastructure.llm_server_manager import GlobalServerManager

class TonobenAgent(BaseAgent):
    """朝廷の実務を取り仕切る"""
    
    # ※システム側で保持するタスク分割の実行回数（実際の運用ではRedis等で永続化・カウントアップを推奨します）
    execution_count = 1 

    def __init__(self):
        super().__init__(agent_id="tonoben", role="function")
        # サーバーマネージャーからサーバーURLを取得
        server_manager = GlobalServerManager.get_server("tonoben", "deepseek_coder_6_7b")
        server_url = server_manager.get_server_url()
        self.llm = LLMClient(agent_id="tonoben", model_name="deepseek_coder_6_7b", server_url=server_url)

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
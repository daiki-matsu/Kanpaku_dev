import time
import yaml
from typing import Dict, Any
from agents.base_agent import BaseAgent
from models.message import Message
from models.tasks import TaskStatus
from executor.safe_io import SafeIO
from connect_llm.ollama_wrapper import ollamaWrapper
from connect_llm.yaml_filter import extract_yaml_blocks
from connect_llm.env_loader import get_env_var
from utility.messages import HeianMessages
from utility.prompts import SystemPrompts

# グローバル変数としてPROMPTSを設定
PROMPTS = SystemPrompts()

class ToneriAgent(BaseAgent):
    """朝廷の実務（ファイルの読み書き等）を担う"""
    
    def __init__(self, agent_id: str = "toneri_1"):
        # 引数で agent_id を受け取ることで、toneri_2 等も簡単に生成可能に
        super().__init__(agent_id=agent_id, role="舎人")
        host = get_env_var("OLLAMA_HOST_3", None)
        self.llm = ollamaWrapper(model_name="gemma4:e2b", host=host)
        self.safe_io = SafeIO(base_project_dir="temp_project")

    def process_message(self, message: Message) -> None:
        """受け取った文（用件）に応じた政務を行う"""
        if message.message_type == "TASK_ASSIGNED":
            self._execute_task(message)
        else:
            print(HeianMessages.TONERI_UNAUTHORIZED.format(agent_id=self.agent_id, message=message))

    def _execute_task(self, message: Message) -> None:
        task_id = message.task_id
        if not task_id:
            return

        # 蔵からタスクの最新状態を取得
        task = self.redis.get_task(task_id)
        if not task or task.status != TaskStatus.ASSIGNED:
            return

        # 1. 掟に従い、政務を 'doing'（作業中）へと進める
        task.status = TaskStatus.DOING
        task.execution.status = "running"
        task.timing.updated_at = int(time.time())
        self.state_manager.update_task(task, event_type="TASK_DOING")

        try:
            print(HeianMessages.TONERI_START_TASK.format(agent_id=self.agent_id, task_id=task_id, command=task.setting.command))

            # 2. LLMによる成果物（ファイル内容）の生成
            prompt = PROMPTS.TONERI_FILE_GENERATION.format(command=task.setting.command)
            
            llm_response = self.llm.generate(prompt)
            yaml_blocks = extract_yaml_blocks(llm_response)
            yaml_str = yaml_blocks[0] if yaml_blocks else llm_response
            file_operations = yaml.safe_load(yaml_str)

            # 3. 排他制御（Lock）を伴う SafeIO による書き込み
            logs = []
            for op in file_operations:
                target_path = op.get("path")
                content = op.get("content")
                
                if not target_path or content is None:
                    continue

                # 封印（ロック）の取得を試みる
                if self.state_manager.try_acquire_lock(target_path, self.agent_id):
                    try:
                        # 結界（SafeIO）を通した安全な書き込み
                        result = self.safe_io.safe_write(target_path, content)
                        logs.append(f"{target_path}: {result.get('logs', '操作完了')}")
                    finally:
                        # 確実な解呪（ロック解放）
                        self.state_manager.release_lock(target_path, self.agent_id)
                else:
                    # 他者が触っている場合は例外を投げ、リトライ処理に回す
                    raise Exception(HeianMessages.LOCK_FAILED.format(target=target_path))

            # 4. 完了報告（REVIEWING）へ遷移
            task.status = TaskStatus.REVIEWING
            task.execution.status = "success"
            task.timing.updated_at = int(time.time())
            task.execution.logs = "\n".join(logs)
            task.answer.status = "success"
            task.answer.summary = HeianMessages.TONERI_COMPLETE_TASK.format(file_count=len(file_operations))
            
            self.state_manager.update_task(task, event_type="TASK_REVIEWING")

            # 頭弁へ完了（査閲依頼）の文を投函する
            reply_msg = Message(
                sender_id=self.agent_id,
                receiver_id="tonoben",
                message_type="REVIEW_REQUEST",
                task_id=task.id,
                content={"summary": task.answer.summary}
            )
            self.state_manager.send_message(reply_msg)
            
            print(HeianMessages.TONERI_REVIEW_REQUEST.format(agent_id=self.agent_id, task_id=task_id))

        except Exception as e:
            # 失敗時は掟に基づき ASSIGNED に戻してやり直し（リトライ）を誘発する
            # ※ StateManager 側で retry.count が自動で加算されます
            print(HeianMessages.AGENT_ERROR.format(agent_id=self.agent_id, error=str(e)))
            
            # 例外処理：task変数はスコープ内で利用可能
            task.status = TaskStatus.ASSIGNED
            task.execution.status = "error"
            task.execution.last_error = str(e)
            task.timing.updated_at = int(time.time())
            self.state_manager.update_task(task, event_type="TASK_RETRYING")
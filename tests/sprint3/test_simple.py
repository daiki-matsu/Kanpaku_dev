import pytest
import time
import tempfile
import shutil
from unittest.mock import Mock, patch
from pathlib import Path

from agents.toneri import ToneriAgent
from models.message import Message
from models.tasks import Task, TaskStatus, SettingInfo, AssignedInfo, TimingInfo
from models.lock import FileLock
from executor.safe_io import SafeIO

class TestSimple:
    """シンプルなテストで問題を特定"""
    
    @pytest.fixture
    def temp_project_dir(self):
        """テスト用の一時プロジェクトディレクトリ"""
        temp_dir = tempfile.mkdtemp(prefix="kanpaku_simple_test_")
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_toneri_agent(self, state_manager, temp_project_dir):
        """モック付きの舎人エージェント"""
        with patch('agents.toneri.LLMAgentWrapper') as mock_llm:
            mock_llm_instance = Mock()
            mock_llm.return_value = mock_llm_instance
            # シンプルなyamlレスポンス
            mock_llm_instance.generate.return_value = """operations:
  - path: "src/simple.py"
    content: "print('simple test')"
"""
            
            agent = ToneriAgent(agent_id="toneri_1")
            agent.redis = state_manager.redis
            agent.state_manager = state_manager
            agent.safe_io = SafeIO(base_project_dir=temp_project_dir)
            yield agent, mock_llm_instance
    
    def test_simple_yaml_parsing(self, mock_toneri_agent, state_manager, temp_project_dir):
        """シンプルなyamlパーシングテスト"""
        agent, mock_llm = mock_toneri_agent
        
        # 準備：シンプルなタスク
        current_time = int(time.time())
        task = Task(
            id="simple_task",
            status=TaskStatus.ASSIGNED,
            setting=SettingInfo(
                bloom_level=2,
                depends_on=[],
                priority=50,
                goal="シンプルテスト",
                command="write_file('src/simple.py', 'print('test')')",
                type="file_write"
            ),
            timing=TimingInfo(created_at=current_time, updated_at=current_time)
        )
        state_manager.redis.save_task(task)
        
        # 準備：メッセージ
        message = Message(
            sender_id="tonoben",
            receiver_id="toneri_1",
            message_type="TASK_ASSIGNED",
            task_id="simple_task",
            content={"instruction": "シンプルテスト"}
        )
        
        # モック：extract_yaml_blocksが正しく動作することを確認
        with patch('agents.toneri.extract_yaml_blocks') as mock_extract:
            mock_extract.return_value = ["""operations:
  - path: "src/simple.py"
    content: "print('simple test')"
"""]
            
            # 実行
            agent.process_message(message)
            
            # 検証
            updated_task = state_manager.redis.get_task("simple_task")
            print(f"タスク状態: {updated_task.status}")
            print(f"実行ステータス: {updated_task.execution.status}")
            
            # 成功していればOK
            if updated_task.status == TaskStatus.REVIEWING:
                print("✅ テスト成功：タスクがREVIEWING状態")
                assert True
            else:
                print(f"❌ テスト失敗：タスク状態={updated_task.status}")
                # 失敗の詳細を表示
                print(f"実行ステータス: {updated_task.execution.status}")
                print(f"エラー: {updated_task.execution.last_error}")
                assert False, "タスクがREVIEWING状態になっていること"

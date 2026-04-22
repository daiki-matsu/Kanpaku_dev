import pytest
import time
import tempfile
import shutil
import yaml
import threading
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from agents.toneri import ToneriAgent
from models.message import Message
from models.tasks import Task, TaskStatus, SettingInfo, AssignedInfo, TimingInfo
from models.lock import FileLock
from executor.safe_io import SafeIO

class TestToneriAgent:
    """舎人エージェントの実装テスト"""
    
    @pytest.fixture
    def temp_project_dir(self):
        """テスト用の一時プロジェクトディレクトリ"""
        temp_dir = tempfile.mkdtemp(prefix="kanpaku_toneri_test_")
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_toneri_agent(self, state_manager, temp_project_dir):
        """モック付きの舎人エージェント"""
        with patch('agents.toneri.LLMAgentWrapper') as mock_llm:
            mock_llm_instance = Mock()
            mock_llm.return_value = mock_llm_instance
            mock_llm_instance.generate.return_value = """operations:
  - path: "src/test_app.py"
    content: |
      def hello():
          print("Hello from Toneri!")
      
      if __name__ == "__main__":
          hello()
"""
            
            agent = ToneriAgent(agent_id="toneri_1")
            agent.redis = state_manager.redis
            agent.state_manager = state_manager
            agent.safe_io = SafeIO(base_project_dir=temp_project_dir)
            yield agent, mock_llm_instance
    
    def test_normal_task_processing(self, mock_toneri_agent, state_manager, sample_task_for_lock):
        """正常なタスク処理テスト"""
        agent, mock_llm = mock_toneri_agent
        
        # 準備：タスクをRedisに保存
        state_manager.redis.save_task(sample_task_for_lock)
        
        # 準備：タスク割り当てメッセージ
        message = Message(
            sender_id="tonoben",
            receiver_id="toneri_1",
            message_type="TASK_ASSIGNED",
            task_id=sample_task_for_lock.id,
            content={"instruction": "テスト用ファイルを作成"}
        )
        
        # 実行：タスク処理
        agent.process_message(message)
        
        # 検証：タスクがDOING→REVIEWINGに遷移していること
        updated_task = state_manager.redis.get_task(sample_task_for_lock.id)
        assert updated_task.status == TaskStatus.REVIEWING, "タスクがREVIEWING状態になっていること"
        assert updated_task.execution.status == "success", "実行ステータスが成功になっていること"
        
        # 検証：ファイルが作成されていること
        file_path = Path(agent.safe_io.base_dir) / "src" / "test_app.py"
        assert file_path.exists(), "ファイルが作成されていること"
        
        # 検証：レビューリクエストメッセージが送信されていること
        inbox_message = state_manager.redis.pop_inbox("tonoben")
        assert inbox_message is not None, "頭弁へのレビューリクエストが送信されていること"
        assert inbox_message.task_id == sample_task_for_lock.id, "タスクIDが正しいこと"

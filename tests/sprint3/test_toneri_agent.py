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
            # 正しいyaml形式のレスポンス
            mock_llm_instance.generate.return_value = """
operations:
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
    
    def test_lock_acquisition_and_release(self, mock_toneri_agent, state_manager, sample_task_for_lock):
        """ロックの取得と解呪テスト"""
        agent, mock_llm = mock_toneri_agent
        
        # 準備：タスクをRedisに保存
        state_manager.redis.save_task(sample_task_for_lock)
        
        # 準備：メッセージ
        message = Message(
            sender_id="tonoben",
            receiver_id="toneri_1",
            message_type="TASK_ASSIGNED",
            task_id=sample_task_for_lock.id,
            content={"instruction": "ロックテスト"}
        )
        
        # 実行：タスク処理（ロック取得を含む）
        with patch('agents.toneri.extract_yaml_blocks') as mock_extract:
            mock_extract.return_value = ["""
operations:
  - path: "src/lock_test.py"
    content: "print('lock test')"
"""]
            agent.process_message(message)
        
        # 検証：【封印】ログが出力されていること（※実際にはprintされるので確認は困難だが、処理が成功することで確認）
        updated_task = state_manager.redis.get_task(sample_task_for_lock.id)
        assert updated_task.status == TaskStatus.REVIEWING, "ロック取得を含む処理が成功していること"
        
        # 検証：【解呪】が実行されていること（ロックが残っていないこと）
        lock_status = state_manager.redis.get_lock("src/lock_test.py")
        assert lock_status is None, "処理完了後にロックが解放されていること"
    
    def test_lock_failure_retry(self, mock_toneri_agent, state_manager, sample_task_for_lock):
        """ロック取得失敗時のリトライ機構テスト"""
        agent, mock_llm = mock_toneri_agent
        
        # 準備：タスクをRedisに保存
        state_manager.redis.save_task(sample_task_for_lock)
        
        # 準備：先にロックを取得しておく
        current_time = time.time()
        existing_lock = FileLock(
            target_path="src/main.py",
            locked_by="toneri_2",
            locked_at=current_time,
            expires_at=current_time + 60
        )
        state_manager.redis.acquire_lock(existing_lock, ttl=60)
        
        # 準備：メッセージ
        message = Message(
            sender_id="tonoben",
            receiver_id="toneri_1",
            message_type="TASK_ASSIGNED",
            task_id=sample_task_for_lock.id,
            content={"instruction": "ロック競合テスト"}
        )
        
        # 準備：LLMレスポンスのモック
        with patch('agents.toneri.extract_yaml_blocks') as mock_extract:
            mock_extract.return_value = ["""
operations:
  - path: "src/main.py"
    content: "print('competing access')"
"""]
            # 実行：タスク処理（ロック取得失敗を想定）
            agent.process_message(message)
        
        # 検証：タスクがASSIGNEDに戻されていること（リトライのため）
        updated_task = state_manager.redis.get_task(sample_task_for_lock.id)
        assert updated_task.status == TaskStatus.ASSIGNED, "ロック失敗時にタスクがASSIGNEDに戻されていること"
        assert updated_task.execution.status == "error", "実行ステータスがエラーになっていること"
        assert updated_task.retry.count == 1, "リトライカウントが増加していること"
        
        # 検証：エラーメッセージが設定されていること
        assert "結界" in updated_task.execution.last_error, "ロック失敗エラーが記録されていること"
    
    def test_unauthorized_message_handling(self, mock_toneri_agent):
        """不正なメッセージタイプの処理テスト"""
        agent, mock_llm = mock_toneri_agent
        
        # 準備：不正なメッセージタイプ
        message = Message(
            sender_id="unknown",
            receiver_id="toneri_1",
            message_type="UNAUTHORIZED_TYPE",
            task_id="test_task",
            content={"instruction": "不正な指示"}
        )
        
        # 実行：メッセージ処理
        with patch('builtins.print') as mock_print:
            agent.process_message(message)
        
        # 検証：適切なエラーメッセージが出力されていること
        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        assert "UNAUTHORIZED_TYPE" in call_args, "不正なメッセージタイプが処理されていること"
    
    def test_file_operation_safety(self, temp_project_dir):
        """ファイル操作の安全性テスト"""
        safe_io = SafeIO(base_project_dir=temp_project_dir)
        
        # 検証：安全なパスでの書き込み成功
        result = safe_io.safe_write("src/safe_file.py", "print('safe')")
        assert result["status"] == "success", "安全なパスでの書き込みが成功すること"
        
        # 検証：危険なパスでの書き込み失敗
        dangerous_result = safe_io.safe_write("../../../etc/passwd", "malicious")
        assert dangerous_result["status"] == "error", "危険なパスでの書き込みが失敗すること"
        assert "不敬なる越権行為" in dangerous_result["logs"], "違反ログが出力されていること"
        
        # 検証：ホームディレクトリへのアクセス失敗
        home_result = safe_io.safe_write("~/.ssh/authorized_keys", "ssh key")
        assert home_result["status"] == "error", "ホームディレクトリへのアクセスが失敗すること"
    
    def test_parallel_task_execution(self, state_manager, parallel_execution_context, temp_project_dir):
        """並列タスク実行テスト"""
        
        def execute_toneri_task(agent_id, task_id, file_path):
            """舎人タスクを並列実行"""
            try:
                # 準備：エージェントとタスク
                with patch('agents.toneri.LLMAgentWrapper') as mock_llm:
                    mock_llm_instance = Mock()
                    mock_llm.return_value = mock_llm_instance
                    mock_llm_instance.generate.return_value = f"""
operations:
  - path: "{file_path}"
    content: "print('from {agent_id}')"
"""
                    
                    agent = ToneriAgent(agent_id=agent_id)
                    agent.redis = state_manager.redis
                    agent.state_manager = state_manager
                    agent.safe_io = SafeIO(base_project_dir=temp_project_dir)
                    
                    # 準備：タスク
                    current_time = int(time.time())
                    task = Task(
                        id=task_id,
                        status=TaskStatus.ASSIGNED,
                        setting=SettingInfo(
                            bloom_level=2,
                            depends_on=[],
                            priority=50,
                            goal=f"並列テストタスク{agent_id}",
                            command=f"write_file('{file_path}', 'content')",
                            type="file_write"
                        ),
                        timing=TimingInfo(created_at=current_time, updated_at=current_time)
                    )
                    state_manager.redis.save_task(task)
                    
                    # 準備：メッセージ
                    message = Message(
                        sender_id="tonoben",
                        receiver_id=agent_id,
                        message_type="TASK_ASSIGNED",
                        task_id=task_id,
                        content={"instruction": f"並列テスト{agent_id}"}
                    )
                    
                    with patch('agents.toneri.extract_yaml_blocks') as mock_extract:
                        mock_extract.return_value = [f"""
operations:
  - path: "{file_path}"
    content: "print('from {agent_id}')"
"""]
                        # 実行
                        agent.process_message(message)
                        
                        # 結果記録
                        final_task = state_manager.redis.get_task(task_id)
                        parallel_execution_context["add_result"]({
                            "agent": agent_id,
                            "task_id": task_id,
                            "status": final_task.status.value if final_task else "NOT_FOUND",
                            "file_path": file_path
                        })
                        
            except Exception as e:
                # エラーが発生しても結果を記録してテスト続行
                parallel_execution_context["add_result"]({
                    "agent": agent_id,
                    "task_id": task_id,
                    "status": "ERROR",
                    "file_path": file_path,
                    "error": str(e)
                })
        
        # 実行：2つの舎人で並列にタスク実行
        threads = []
        for i, (agent_id, task_id, file_path) in enumerate([
            ("toneri_1", "parallel_task_1", "src/parallel1.py"),
            ("toneri_2", "parallel_task_2", "src/parallel2.py")
        ]):
            thread = threading.Thread(
                target=execute_toneri_task,
                args=(agent_id, task_id, file_path)
            )
            threads.append(thread)
            thread.start()
        
        # 待機
        for thread in threads:
            thread.join()
        
        # 検証：両方のタスクが処理されていること
        assert len(parallel_execution_context["results"]) == 2, "両方のタスクが処理されていること"
        
        for result in parallel_execution_context["results"]:
            assert result["status"] == "reviewing", f"タスク{result['task_id']}がREVIEWING状態になっていること"
            
            # 検証：ファイルが作成されていること
            file_full_path = Path(temp_project_dir) / result["file_path"]
            assert file_full_path.exists(), f"ファイル{result['file_path']}が作成されていること"

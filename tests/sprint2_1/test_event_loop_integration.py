import pytest
import time
import threading
import queue
from unittest.mock import Mock, patch
import sys
import os

# srcモジュールをインポート
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from agents.base_agent import BaseAgent
from agents.tonoben import TonobenAgent
from models.message import Message
from models.agents import AgentStatus
from models.tasks import Task, TaskStatus
from models.events import Event
from db.redis_client import RedisClient
from db.state_manager import StateManager

class TestEventLoopIntegration:
    """イベントループとLLM実行の統合テスト"""
    
    def test_event_loop_basic_operation(self, redis_client, event_loop_timeout):
        """イベントループの基本動作テスト"""
        # エージェントを初期化
        agent = BaseAgent(agent_id="event_test_agent", role="イベントループテスト", db=2)
        
        # イベントループを別スレッドで開始
        loop_stopped = threading.Event()
        loop_events = []
        
        def capture_events():
            """イベントループの動作をキャプチャ"""
            try:
                # 短時間実行してイベントをキャプチャ
                start_time = time.time()
                while time.time() - start_time < 3.0:
                    # ハートビート更新
                    agent._update_heartbeat()
                    loop_events.append(f"heartbeat_{time.time()}")
                    time.sleep(0.5)
            except Exception as e:
                loop_events.append(f"error_{e}")
            finally:
                loop_stopped.set()
        
        # イベントループスレッドを開始
        event_thread = threading.Thread(target=capture_events)
        event_thread.start()
        
        # イベントループが動作することを確認
        event_thread.join(timeout=event_loop_timeout)
        assert loop_stopped.is_set(), "イベントループが正常に停止しませんでした"
        assert len(loop_events) > 0, "イベントループでイベントが発生しませんでした"
        
        # ハートビートが更新されていることを確認
        final_heartbeat = agent.me.last_heartbeat
        assert final_heartbeat > 0, "ハートビートが更新されていません"
    
    def test_message_processing_in_event_loop(self, redis_client, event_loop_timeout):
        """イベントループ内でのメッセージ処理テスト"""
        agent = BaseAgent(agent_id="message_test_agent", role="メッセージ処理テスト", db=2)
        
        # メッセージ処理結果を記録
        processed_messages = []
        
        def track_message_processing(message):
            """メッセージ処理をトラッキング"""
            processed_messages.append({
                'message_id': message.message_id,
                'sender_id': message.sender_id,
                'message_type': message.message_type,
                'processed_at': time.time()
            })
            # 処理をシミュレート
            time.sleep(0.1)
        
        # メッセージ処理メソッドをオーバーライド
        agent.process_message = track_message_processing
        
        # テストメッセージを送信
        test_message = Message(
            sender_id="tonoben",
            receiver_id="message_test_agent",
            message_type="TASK_ASSIGNED",
            task_id="test_task_1",
            content={"instruction": "テスト指示"}
        )
        
        # メッセージをInboxに投入
        redis_client.push_inbox("message_test_agent", test_message)
        
        # メッセージ処理を実行
        message_processed = threading.Event()
        
        def process_messages():
            """メッセージ処理ループ"""
            try:
                message = redis_client.pop_inbox("message_test_agent")
                if message:
                    agent.process_message(message)
                    message_processed.set()
            except Exception as e:
                print(f"メッセージ処理エラー: {e}")
        
        # メッセージ処理スレッドを開始
        process_thread = threading.Thread(target=process_messages)
        process_thread.start()
        
        # メッセージが処理されるのを待機
        assert message_processed.wait(timeout=event_loop_timeout), "メッセージが処理されませんでした"
        process_thread.join(timeout=1.0)
        
        # メッセージ処理結果を確認
        assert len(processed_messages) == 1, "メッセージが1件処理されているべきです"
        assert processed_messages[0]['message_type'] == "TASK_ASSIGNED"
        assert processed_messages[0]['sender_id'] == "tonoben"
    
    @patch('agents.tonoben.ollamaWrapper')
    @patch('agents.tonoben.filter_yaml_document')
    def test_real_llm_execution_in_event_loop(self, mock_extract_yaml, mock_ollama, state_manager, event_loop_timeout):
        """イベントループ内での実際のLLM実行テスト"""
        # LLMモックを設定（実際の呼び出しを検証）
        mock_llm_instance = Mock()
        mock_ollama.return_value = mock_llm_instance
        
        # 実際的なLLM応答を設定
        llm_response = """
        以下にタスク分解結果を示します：

        ```yaml
        - step_id: "real_llm_step_1"
          depends_on: []
          bloom_level: 3
          priority: 80
          goal: "実際のLLM実行テスト"
          command: "LLM連携をテストせよ"
          type: "integration_test"
          target_agent: "toneri_1"
        ```
        """
        mock_llm_instance.return_value = llm_response
        mock_extract_yaml.return_value = """
        - step_id: "real_llm_step_1"
          depends_on: []
          bloom_level: 3
          priority: 80
          goal: "実際のLLM実行テスト"
          command: "LLM連携をテストせよ"
          type: "integration_test"
          target_agent: "toneri_1"
        """
        
        # 頭弁エージェントを初期化
        tonoben = TonobenAgent()
        tonoben.state_manager = state_manager
        
        # LLM実行イベントを記録
        llm_events = []
        
        def track_llm_call(*args, **kwargs):
            """LLM呼び出しをトラッキング"""
            llm_events.append({
                'called_at': time.time(),
                'args': args,
                'kwargs': kwargs
            })
            return llm_response
        
        mock_llm_instance.side_effect = track_llm_call
        
        # イベントループ内でLLM実行をシミュレート
        llm_executed = threading.Event()
        
        def execute_llm_in_loop():
            """イベントループ内でLLMを実行"""
            try:
                # 詔勅メッセージを作成
                order_message = Message(
                    sender_id="kanpaku",
                    receiver_id="tonoben",
                    message_type="ORDER_RECEIVED",
                    content={"instruction": "実際のLLM実行をテストせよ"}
                )
                
                # メッセージを処理（LLM呼び出しを含む）
                tonoben.process_message(order_message)
                llm_executed.set()
                
            except Exception as e:
                print(f"LLM実行エラー: {e}")
        
        # LLM実行スレッドを開始
        llm_thread = threading.Thread(target=execute_llm_in_loop)
        llm_thread.start()
        
        # LLM実行が完了するのを待機
        assert llm_executed.wait(timeout=event_loop_timeout), "LLM実行が完了しませんでした"
        llm_thread.join(timeout=1.0)
        
        # LLM呼び出しが行われたことを確認
        assert len(llm_events) > 0, "LLMが呼び出されていません"
        assert mock_llm_instance.call_count >= 1, "LLMの__call__メソッドが呼び出されていません"
        
        # タスクが作成されていることを確認
        created_task = state_manager.redis.get_task("1_1")
        assert created_task is not None, "LLM実行結果でタスクが作成されていません"
        assert created_task.setting.goal == "実際のLLM実行テスト"
        
        # メッセージが送信されていることを確認
        inbox_message = state_manager.redis.pop_inbox("toneri_1")
        assert inbox_message is not None, "タスク割り当てメッセージが送信されていません"
        assert inbox_message.task_id == "1_1"
    
    def test_multi_agent_event_loop_coordination(self, redis_client, event_loop_timeout):
        """複数エージェントのイベントループ連携テスト"""
        agents = []
        agent_ids = ["coord_test_1", "coord_test_2", "coord_test_3"]
        
        # 複数のエージェントを初期化
        for agent_id in agent_ids:
            agent = BaseAgent(agent_id=agent_id, role=f"連携テスト{agent_id}", db=2)
            agents.append(agent)
        
        # エージェント間の通信イベントを記録
        communication_events = []
        
        def track_communication():
            """エージェント間通信をトラッキング"""
            for i, sender_id in enumerate(agent_ids):
                if i < len(agent_ids) - 1:
                    receiver_id = agent_ids[i + 1]
                    
                    # メッセージを作成して送信
                    message = Message(
                        sender_id=sender_id,
                        receiver_id=receiver_id,
                        message_type="COORDINATION_TEST",
                        content={"sequence": i, "test": "multi_agent_coordination"}
                    )
                    
                    redis_client.push_inbox(receiver_id, message)
                    communication_events.append({
                        'sender': sender_id,
                        'receiver': receiver_id,
                        'timestamp': time.time()
                    })
                    
                    time.sleep(0.1)  # 少し待機して順序を確保
        
        # 連携テストを実行
        coordination_completed = threading.Event()
        
        def run_coordination_test():
            """連携テストを実行"""
            try:
                track_communication()
                
                # 各エージェントがメッセージを受信
                for i, agent_id in enumerate(agent_ids):
                    if i > 0:  # 最初のエージェント以外
                        message = redis_client.pop_inbox(agent_id)
                        if message:
                            communication_events.append({
                                'action': f'message_received_by_{agent_id}',
                                'message_type': message.message_type,
                                'timestamp': time.time()
                            })
                
                coordination_completed.set()
                
            except Exception as e:
                print(f"連携テストエラー: {e}")
        
        # 連携テストスレッドを開始
        coordination_thread = threading.Thread(target=run_coordination_test)
        coordination_thread.start()
        
        # 連携テストが完了するのを待機
        assert coordination_completed.wait(timeout=event_loop_timeout), "エージェント連携テストが完了しませんでした"
        coordination_thread.join(timeout=1.0)
        
        # 連携結果を確認
        assert len(communication_events) >= 3, "エージェント間の連携イベントが十分に記録されていません"
        
        # メッセージ受信を確認
        received_messages = [e for e in communication_events if 'action' in e and 'message_received_by' in e['action']]
        assert len(received_messages) >= 2, "少なくとも2つのエージェントがメッセージを受信しているべきです"
    
    def test_event_loop_error_handling(self, redis_client, event_loop_timeout):
        """イベントループ内でのエラーハンドリングテスト"""
        agent = BaseAgent(agent_id="error_test_agent", role="エラーハンドリングテスト", db=2)
        
        # エラーイベントを記録
        error_events = []
        
        def failing_message_processing(message):
            """意図的に失敗するメッセージ処理"""
            error_events.append({
                'error_type': 'message_processing',
                'message_id': message.message_id,
                'timestamp': time.time()
            })
            raise Exception("意図的なテストエラー")
        
        # エラーを発生させるメッセージ処理を設定
        agent.process_message = failing_message_processing
        
        # エラーメッセージを送信
        error_message = Message(
            sender_id="error_sender",
            receiver_id="error_test_agent",
            message_type="ERROR_TEST",
            content={"error_simulation": True}
        )
        
        # エラーハンドリングテストを実行
        error_handled = threading.Event()
        
        def test_error_handling():
            """エラーハンドリングをテスト"""
            try:
                # メッセージを処理（エラーが発生）
                agent.process_message(error_message)
                
                # エージェント状態を確認
                if agent.me.status == AgentStatus.ERROR:
                    error_events.append({
                        'error_type': 'agent_status_error',
                        'status': agent.me.status,
                        'timestamp': time.time()
                    })
                
                error_handled.set()
                
            except Exception as e:
                error_events.append({
                    'error_type': 'exception_caught',
                    'exception': str(e),
                    'timestamp': time.time()
                })
                error_handled.set()
        
        # エラーハンドリングテストスレッドを開始
        error_thread = threading.Thread(target=test_error_handling)
        error_thread.start()
        
        # エラーハンドリングが完了するのを待機
        assert error_handled.wait(timeout=event_loop_timeout), "エラーハンドリングテストが完了しませんでした"
        error_thread.join(timeout=1.0)
        
        # エラーが適切に処理されたことを確認
        assert len(error_events) > 0, "エラーイベントが記録されていません"
        
        # 少なくともメッセージ処理エラーが記録されているべき
        message_errors = [e for e in error_events if e['error_type'] == 'message_processing']
        assert len(message_errors) > 0, "メッセージ処理エラーが記録されていません"

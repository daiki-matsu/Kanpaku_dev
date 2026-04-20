import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from agents.tonoben import TonobenAgent
from models.message import Message
from models.tasks import Task, TaskStatus
from models.agents import AgentStatus

class TestTonobenDecompose:
    """頭弁の政務分解とアサイン処理のテスト"""
    
    def test_tonoben_initialization(self):
        """頭弁の初期化"""
        tonoben = TonobenAgent()
        
        assert tonoben.agent_id == "tonoben"
        assert tonoben.role == "頭弁"
        assert tonoben.me.status == AgentStatus.IDLE
        assert tonoben.execution_count == 1
    
    @patch('agents.tonoben.ollamaWrapper')
    @patch('agents.tonoben.filter_yaml_document')
    def test_order_received_processing(self, mock_extract_yaml, mock_ollama, state_manager):
        # Reset execution_count for consistent test results
        TonobenAgent.execution_count = 1
        """詔勅受信時の処理"""
        # モックの設定
        mock_llm_instance = Mock()
        mock_ollama.return_value = mock_llm_instance
        
        # LLMの応答をモック
        mock_llm_response = """
        ```yaml
        - step_id: "step_1"
          depends_on: []
          bloom_level: 3
          priority: 80
          goal: "システム仕様書のひな型を作成する"
          command: "README.mdのテンプレートを作成せよ"
          type: "file_write"
          target_agent: "toneri_1"
        - step_id: "step_2"
          depends_on: ["step_1"]
          bloom_level: 2
          priority: 70
          goal: "仕様書の内容を確認する"
          command: "README.mdの内容をレビューせよ"
          type: "file_read"
          target_agent: "toneri_1"
        ```
        """
        mock_llm_instance.generate.return_value = mock_llm_response
        
        # YAML抽出をモック
        mock_extract_yaml.return_value = """
        - step_id: "step_1"
          depends_on: []
          bloom_level: 3
          priority: 80
          goal: "システム仕様書のひな型を作成する"
          command: "README.mdのテンプレートを作成せよ"
          type: "file_write"
          target_agent: "toneri_1"
        - step_id: "step_2"
          depends_on: ["step_1"]
          bloom_level: 2
          priority: 70
          goal: "仕様書の内容を確認する"
          command: "README.mdの内容をレビューせよ"
          type: "file_read"
          target_agent: "toneri_1"
        """
        
        # 頭弁エージェントを初期化
        tonoben = TonobenAgent()
        tonoben.state_manager = state_manager
        
        # テスト用メッセージ
        order_message = Message(
            sender_id="kanpaku",
            receiver_id="tonoben",
            message_type="ORDER_RECEIVED",
            content={"instruction": "システム仕様書のひな型を作成せよ"}
        )
        
        # メッセージを処理
        tonoben.process_message(order_message)
        
        # LLMが呼ばれたことを確認
        mock_llm_instance.generate.assert_called_once()
        
        # YAML抽出が呼ばれたことを確認
        mock_extract_yaml.assert_called_once()
        
        # 実行カウントが増加したことを確認
        assert tonoben.execution_count == 2
    
    @patch('agents.tonoben.ollamaWrapper')
    @patch('agents.tonoben.filter_yaml_document')
    def test_task_creation_and_assignment(self, mock_extract_yaml, mock_ollama, state_manager):
        """タスクの作成とアサイン処理"""
        # モックの設定
        mock_llm_instance = Mock()
        mock_ollama.return_value = mock_llm_instance
        
        mock_llm_response = """
        ```yaml
        - step_id: "step_1"
          depends_on: []
          bloom_level: 4
          priority: 90
          goal: "プロジェクト構造を分析する"
          command: "srcディレクトリの構造を調査せよ"
          type: "analysis"
          target_agent: "toneri_1"
        ```
        """
        mock_llm_instance.generate.return_value = mock_llm_response
        mock_extract_yaml.return_value = """
        - step_id: "step_1"
          depends_on: []
          bloom_level: 4
          priority: 90
          goal: "プロジェクト構造を分析する"
          command: "srcディレクトリの構造を調査せよ"
          type: "analysis"
          target_agent: "toneri_1"
        """
        
        # Reset execution_count for consistent test results
        TonobenAgent.execution_count = 1
        tonoben = TonobenAgent()
        tonoben.state_manager = state_manager
        
        order_message = Message(
            sender_id="kanpaku",
            receiver_id="tonoben",
            message_type="ORDER_RECEIVED",
            content={"instruction": "プロジェクト構造を分析せよ"}
        )
        
        # メッセージを処理
        tonoben.process_message(order_message)
        
        # タスクが作成されていることを確認
        created_task = state_manager.redis.get_task("1_1")
        assert created_task is not None
        assert created_task.id == "1_1"
        assert created_task.status == TaskStatus.ASSIGNED
        assert created_task.setting.bloom_level == 4
        assert created_task.setting.priority == 90
        assert created_task.setting.goal == "プロジェクト構造を分析する"
        assert created_task.setting.command == "srcディレクトリの構造を調査せよ"
        assert created_task.setting.type == "analysis"
        assert created_task.assigned.to == "toneri_1"
        
        # Inboxにメッセージが送信されていることを確認
        inbox_message = state_manager.redis.pop_inbox("toneri_1")
        assert inbox_message is not None
        assert inbox_message.sender_id == "tonoben"
        assert inbox_message.receiver_id == "toneri_1"
        assert inbox_message.message_type == "TASK_ASSIGNED"
        assert inbox_message.task_id == "1_1"
        assert inbox_message.content["instruction"] == "srcディレクトリの構造を調査せよ"
            
    @patch('agents.tonoben.ollamaWrapper')
    @patch('agents.tonoben.filter_yaml_document')
    def test_task_dependency_resolution(self, mock_extract_yaml, mock_ollama, state_manager):
        # Reset execution_count for consistent test results
        TonobenAgent.execution_count = 1
        """タスクの依存関係解決"""
        mock_llm_instance = Mock()
        mock_ollama.return_value = mock_llm_instance
        
        mock_llm_response = """
        ```yaml
        - step_id: "step_1"
          depends_on: []
          bloom_level: 3
          priority: 80
          goal: "基礎設計を行う"
          command: "基本設計書を作成せよ"
          type: "planning"
          target_agent: "toneri_1"
        - step_id: "step_2"
          depends_on: ["step_1"]
          bloom_level: 4
          priority: 75
          goal: "詳細設計を行う"
          command: "詳細設計書を作成せよ"
          type: "planning"
          target_agent: "toneri_2"
        - step_id: "step_3"
          depends_on: ["step_1", "step_2"]
          bloom_level: 5
          priority: 70
          goal: "実装を行う"
          command: "コードを実装せよ"
          type: "code_execution"
          target_agent: "toneri_1"
        ```
        """
        mock_llm_instance.generate.return_value = mock_llm_response
        mock_extract_yaml.return_value = """
        - step_id: "step_1"
          depends_on: []
          bloom_level: 3
          priority: 80
          goal: "基礎設計を行う"
          command: "基本設計書を作成せよ"
          type: "planning"
          target_agent: "toneri_1"
        - step_id: "step_2"
          depends_on: ["step_1"]
          bloom_level: 4
          priority: 75
          goal: "詳細設計を行う"
          command: "詳細設計書を作成せよ"
          type: "planning"
          target_agent: "toneri_2"
        - step_id: "step_3"
          depends_on: ["step_1", "step_2"]
          bloom_level: 5
          priority: 70
          goal: "実装を行う"
          command: "コードを実装せよ"
          type: "code_execution"
          target_agent: "toneri_1"
        """
        
        tonoben = TonobenAgent()
        tonoben.state_manager = state_manager
        
        order_message = Message(
            sender_id="kanpaku",
            receiver_id="tonoben",
            message_type="ORDER_RECEIVED",
            content={"instruction": "システムを開発せよ"}
        )
        
        tonoben.process_message(order_message)
        
        # 依存関係が正しく解決されていることを確認
        task_1 = state_manager.redis.get_task("1_1")
        task_2 = state_manager.redis.get_task("1_2")
        task_3 = state_manager.redis.get_task("1_3")
        
        assert task_1 is not None
        assert task_2 is not None
        assert task_3 is not None
        
        # step_1は依存関係なし
        assert task_1.setting.depends_on == []
        
        # step_2はstep_1に依存
        assert task_2.setting.depends_on == ["1_1"]
        
        # step_3はstep_1とstep_2に依存
        assert task_3.setting.depends_on == ["1_1", "1_2"]
    
    def test_unknown_message_type_handling(self):
        """未知のメッセージタイプの処理"""
        tonoben = TonobenAgent()
        
        unknown_message = Message(
            sender_id="unknown",
            receiver_id="tonoben",
            message_type="UNKNOWN_TYPE",
            content={"test": "data"}
        )
        
        # 例外が発生しないこと
        tonoben.process_message(unknown_message)
    
    @patch('agents.tonoben.ollamaWrapper')
    @patch('agents.tonoben.filter_yaml_document')
    def test_llm_error_handling(self, mock_extract_yaml, mock_ollama, state_manager):
        # Reset execution_count for consistent test results
        TonobenAgent.execution_count = 1
        """LLMエラー時の処理"""
        mock_llm_instance = Mock()
        mock_ollama.return_value = mock_llm_instance
        
        # LLMでエラーを発生させる
        mock_llm_instance.generate.side_effect = Exception("LLM接続エラー")
        
        tonoben = TonobenAgent()
        tonoben.state_manager = state_manager
        
        order_message = Message(
            sender_id="kanpaku",
            receiver_id="tonoben",
            message_type="ORDER_RECEIVED",
            content={"instruction": "テスト指示"}
        )
        
        # エラーが伝播すること
        with pytest.raises(Exception, match="LLM接続エラー"):
            tonoben.process_message(order_message)
    
    @patch('agents.tonoben.ollamaWrapper')
    @patch('agents.tonoben.filter_yaml_document')
    def test_yaml_parsing_error_handling(self, mock_extract_yaml, mock_ollama, state_manager):
        # Reset execution_count for consistent test results
        TonobenAgent.execution_count = 1
        """YAML解析エラー時の処理"""
        mock_llm_instance = Mock()
        mock_ollama.return_value = mock_llm_instance
        
        mock_llm_instance.generate.return_value = "Invalid YAML response"
        mock_extract_yaml.side_effect = Exception("YAML解析エラー")
        
        tonoben = TonobenAgent()
        tonoben.state_manager = state_manager
        
        order_message = Message(
            sender_id="kanpaku",
            receiver_id="tonoben",
            message_type="ORDER_RECEIVED",
            content={"instruction": "テスト指示"}
        )
        
        # エラーが伝播すること
        with pytest.raises(Exception, match="YAML解析エラー"):
            tonoben.process_message(order_message)
    
    @patch('agents.tonoben.ollamaWrapper')
    @patch('agents.tonoben.filter_yaml_document')
    def test_multiple_task_assignment(self, mock_extract_yaml, mock_ollama, state_manager):
        """複数タスクのアサイン処理"""
        mock_llm_instance = Mock()
        mock_ollama.return_value = mock_llm_instance
        
        mock_llm_response = """
        ```yaml
        - step_id: "step_1"
          depends_on: []
          bloom_level: 3
          priority: 80
          goal: "ファイルを作成する"
          command: "test.txtを作成せよ"
          type: "file_write"
          target_agent: "toneri_1"
        - step_id: "step_2"
          depends_on: []
          bloom_level: 2
          priority: 70
          goal: "ファイルを読み込む"
          command: "test.txtを読み込め"
          type: "file_read"
          target_agent: "toneri_2"
        ```
        """
        mock_llm_instance.generate.return_value = mock_llm_response
        mock_extract_yaml.return_value = """
        - step_id: "step_1"
          depends_on: []
          bloom_level: 3
          priority: 80
          goal: "ファイルを作成する"
          command: "test.txtを作成せよ"
          type: "file_write"
          target_agent: "toneri_1"
        - step_id: "step_2"
          depends_on: []
          bloom_level: 2
          priority: 70
          goal: "ファイルを読み込む"
          command: "test.txtを読み込め"
          type: "file_read"
          target_agent: "toneri_2"
        """
        
        # Reset execution_count for consistent test results
        TonobenAgent.execution_count = 1
        tonoben = TonobenAgent()
        tonoben.state_manager = state_manager
        
        order_message = Message(
            sender_id="kanpaku",
            receiver_id="tonoben",
            message_type="ORDER_RECEIVED",
            content={"instruction": "ファイル操作を行え"}
        )
        
        tonoben.process_message(order_message)
        
        # 両方のエージェントにメッセージが送信されていることを確認
        message_1 = state_manager.redis.pop_inbox("toneri_1")
        message_2 = state_manager.redis.pop_inbox("toneri_2")
        
        assert message_1 is not None
        assert message_1.task_id == "1_1"
        assert message_1.receiver_id == "toneri_1"
        
        assert message_2 is not None
        assert message_2.task_id == "1_2"
        assert message_2.receiver_id == "toneri_2"
        
        # 両方のタスクが作成されていることを確認
        task_1 = state_manager.redis.get_task("1_1")
        task_2 = state_manager.redis.get_task("1_2")
        
        assert task_1 is not None
        assert task_2 is not None
        assert task_1.assigned.to == "toneri_1"
        assert task_2.assigned.to == "toneri_2"

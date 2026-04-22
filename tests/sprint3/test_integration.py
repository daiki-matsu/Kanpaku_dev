import pytest
import time
import threading
from unittest.mock import Mock, patch

from agents.kanpaku import KanpakuAgent
from agents.tonoben import TonobenAgent
from agents.toneri import ToneriAgent
from models.message import Message

class TestIntegration:
    """関白-頭弁-舎人の連携テスト"""
    
    @pytest.fixture
    def integrated_agents(self, state_manager, temp_project_dir):
        """統合テスト用の3エージェント"""
        with patch('agents.kanpaku.LLMAgentWrapper') as mock_kanpaku_llm, \
             patch('agents.tonoben.LLMAgentWrapper') as mock_tonoben_llm, \
             patch('agents.toneri.GeminiWrapper') as mock_toneri_llm:
            
            # 関白のLLMモック
            mock_kanpaku_llm_instance = Mock()
            mock_kanpaku_llm.return_value = mock_kanpaku_llm_instance
            mock_kanpaku_llm_instance.generate.return_value = """
電卓アプリをPythonで作成する詳細指示：
1. メイン関数を持つcalculator.pyを作成
2. 基本的な四則演算機能を実装
3. ユーザー入力を受け付けるCLIインターフェース
"""
            
            # 頭弁のLLMモック
            mock_tonoben_llm_instance = Mock()
            mock_tonoben_llm.return_value = mock_tonoben_llm_instance
            mock_tonoben_llm_instance.generate.return_value = """
steps:
  - step_id: "1"
    goal: "電卓の基本構造を作成"
    command: "create_file('src/calculator.py', 四則演算クラス)"
    target_agent: "toneri_1"
    priority: 80
  - step_id: "2"
    goal: "CLIインターフェースを実装"
    command: "create_file('src/main.py', メイン処理)"
    target_agent: "toneri_2"
    priority: 70
"""
            
            # 舎人のLLMモック
            mock_toneri_llm_instance = Mock()
            mock_toneri_llm.return_value = mock_toneri_llm_instance
            mock_toneri_llm_instance.generate.return_value = """
operations:
  - path: "src/calculator.py"
    content: |
      class Calculator:
          def add(self, a, b): return a + b
          def subtract(self, a, b): return a - b
          def multiply(self, a, b): return a * b
          def divide(self, a, b): return a / b
"""
            
            # エージェント初期化
            kanpaku = KanpakuAgent()
            kanpaku.state_manager = state_manager
            
            tonoben = TonobenAgent()
            tonoben.state_manager = state_manager
            
            toneri_1 = ToneriAgent(agent_id="toneri_1")
            toneri_1.state_manager = state_manager
            toneri_1.safe_io = SafeIO(base_project_dir=temp_project_dir)
            
            toneri_2 = ToneriAgent(agent_id="toneri_2")
            toneri_2.state_manager = state_manager
            toneri_2.safe_io = SafeIO(base_project_dir=temp_project_dir)
            
            yield {
                "kanpaku": kanpaku,
                "tonoben": tonoben,
                "toneri_1": toneri_1,
                "toneri_2": toneri_2
            }
    
    def test_three_agents_standby(self, integrated_agents):
        """三役揃い踏みテスト"""
        agents = integrated_agents
        
        # 検証：全エージェントが正しく初期化されていること
        assert agents["kanpaku"].agent_id == "kanpaku", "関白が正しく初期化されていること"
        assert agents["kanpaku"].role == "関白", "関白の役職が正しいこと"
        
        assert agents["tonoben"].agent_id == "tonoben", "頭弁が正しく初期化されていること"
        assert agents["tonoben"].role == "頭弁", "頭弁の役職が正しいこと"
        
        assert agents["toneri_1"].agent_id == "toneri_1", "舎人1が正しく初期化されていること"
        assert agents["toneri_1"].role == "舎人", "舎人1の役職が正しいこと"
        
        assert agents["toneri_2"].agent_id == "toneri_2", "舎人2が正しく初期化されていること"
        assert agents["toneri_2"].role == "舎人", "舎人2の役職が正しいこと"
    
    def test_mikado_order_flow(self, integrated_agents, state_manager):
        """帝の詔勅テスト"""
        agents = integrated_agents
        
        # 準備：帝からの詔勅メッセージ
        mikado_order = Message(
            sender_id="mikado",
            receiver_id="kanpaku",
            message_type="MIKADO_ORDER",
            content={"order": "電卓アプリをPythonで作って"}
        )
        
        # 実行：関白が詔勅を受信
        agents["kanpaku"].process_message(mikado_order)
        
        # 検証：頭弁への指示書が送信されていること
        tonoben_message = state_manager.redis.pop_inbox("tonoben")
        assert tonoben_message is not None, "頭弁へのメッセージが送信されていること"
        assert tonoben_message.message_type == "ORDER_RECEIVED", "メッセージタイプが正しいこと"
        assert "電卓アプリ" in tonoben_message.content["instruction"], "指示書に電卓の内容が含まれていること"
    
    def test_chain_reaction(self, integrated_agents, state_manager, temp_project_dir):
        """連鎖の証明テスト"""
        agents = integrated_agents
        
        # ステップ1：帝の詔勅
        mikado_order = Message(
            sender_id="mikado",
            receiver_id="kanpaku",
            message_type="MIKADO_ORDER",
            content={"order": "電卓アプリをPythonで作って"}
        )
        
        with patch('agents.toneri.extract_yaml') as mock_extract:
            mock_extract.return_value = """
operations:
  - path: "src/calculator.py"
    content: "class Calculator: pass"
"""
            
            # 実行1：関白→頭弁
            agents["kanpaku"].process_message(mikado_order)
            
            # 検証1：頭弁が指示を受信
            tonoben_msg = state_manager.redis.pop_inbox("tonoben")
            assert tonoben_msg is not None, "【関白】指示書が頭弁へ送信されていること"
            
            # 実行2：頭弁→舎人
            agents["tonoben"].process_message(tonoben_msg)
            
            # 検証2：舎人へのタスク割り当て
            toneri_1_msg = state_manager.redis.pop_inbox("toneri_1")
            toneri_2_msg = state_manager.redis.pop_inbox("toneri_2")
            
            assert toneri_1_msg is not None, "舎人1へのタスク割り当てがあること"
            assert toneri_2_msg is not None, "舎人2へのタスク割り当てがあること"
            assert toneri_1_msg.message_type == "TASK_ASSIGNED", "タスク割り当てメッセージであること"
            
            # 実行3：舎人→レビュー依頼
            agents["toneri_1"].process_message(toneri_1_msg)
            agents["toneri_2"].process_message(toneri_2_msg)
            
            # 検証3：頭弁へのレビューリクエスト
            review_msg_1 = state_manager.redis.pop_inbox("tonoben")
            review_msg_2 = state_manager.redis.pop_inbox("tonoben")
            
            assert review_msg_1 is not None, "【舎人1】レビューリクエストが送信されていること"
            assert review_msg_1.message_type == "REVIEW_REQUEST", "レビューリクエストであること"
            
            # 検証4：ファイルが作成されていること
            from pathlib import Path
            calc_file = Path(temp_project_dir) / "src" / "calculator.py"
            assert calc_file.exists(), "【舎人】ファイルが作成されていること"
    
    def test_parallel_toneri_execution(self, integrated_agents, state_manager, temp_project_dir):
        """並列舎人実行テスト"""
        agents = integrated_agents
        
        # 準備：2つのタスクを同時に割り当て
        with patch('agents.toneri.extract_yaml') as mock_extract:
            mock_extract.return_value = """
operations:
  - path: "src/parallel_test.py"
    content: "print('parallel execution')"
"""
            
            # タスク1作成
            task1_msg = Message(
                sender_id="tonoben",
                receiver_id="toneri_1",
                message_type="TASK_ASSIGNED",
                task_id="parallel_task_1",
                content={"instruction": "並列タスク1"}
            )
            
            # タスク2作成
            task2_msg = Message(
                sender_id="tonoben",
                receiver_id="toneri_2", 
                message_type="TASK_ASSIGNED",
                task_id="parallel_task_2",
                content={"instruction": "並列タスク2"}
            )
            
            # 並列実行
            def execute_task(agent, message):
                agent.process_message(message)
            
            thread1 = threading.Thread(target=execute_task, args=(agents["toneri_1"], task1_msg))
            thread2 = threading.Thread(target=execute_task, args=(agents["toneri_2"], task2_msg))
            
            thread1.start()
            thread2.start()
            
            thread1.join()
            thread2.join()
            
            # 検証：両方のタスクが完了していること
            from pathlib import Path
            test_file = Path(temp_project_dir) / "src" / "parallel_test.py"
            assert test_file.exists(), "並列実行でファイルが作成されていること"
            
            # 検証：レビューリクエストが2つ送信されていること
            review1 = state_manager.redis.pop_inbox("tonoben")
            review2 = state_manager.redis.pop_inbox("tonoben")
            
            assert review1 is not None, "最初のレビューリクエストがあること"
            assert review2 is not None, "2番目のレビューリクエストがあること"

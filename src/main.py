#!/usr/bin/env python3
"""
Kanpakuシステムのメインエントリーポイント
"""

import sys
import os
import time
import threading
from pathlib import Path

# srcディレクトリをパスに追加
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from agents.tonoben import TonobenAgent
from agents.base_agent import BaseAgent
from db.state_manager import StateManager
from db.redis_client import RedisClient
from db.yaml_store import YamlStore
from models.message import Message
from models.agents import AgentStatus
from utility.messages import HeianMessages

def main():
    """Kanpakuシステムを起動"""
    print(HeianMessages.SYSTEM_STARTUP)
    
    try:
        # Redis接続を確認
        print(HeianMessages.REDIS_CHECK)
        redis_client = RedisClient(host='localhost', port=6379, db=0)
        
        # StateManagerを初期化
        print(HeianMessages.STATE_MANAGER_INIT)
        yaml_store = YamlStore(base_dir="history")
        state_manager = StateManager()
        state_manager.redis = redis_client
        state_manager.yaml = yaml_store
        
        # 頭弁エージェントを起動
        print(HeianMessages.TONOBEN_STARTUP)
        tonoben = TonobenAgent()
        tonoben.state_manager = state_manager
        
        # 頭弁の出仕宣言
        print(HeianMessages.TONOBEN_ATTENDANCE)
        tonoben._update_heartbeat()
        
        # サンプルエージェントを起動（テスト用）
        print(HeianMessages.SAMPLE_AGENT_STARTUP)
        sample_agents = []
        for i in range(1, 4):
            agent = BaseAgent(agent_id=f"toneri_{i}", role=f"殿人{i}", db=0)
            sample_agents.append(agent)
            print(f"  - {agent.agent_id} ({agent.role}) を起動しました")
        
        # イベントループを開始
        print(HeianMessages.EVENT_LOOP_START)
        print("Ctrl+Cで停止できます")
        
        def event_loop():
            """メインイベントループ"""
            try:
                while True:
                    # 頭弁のハートビートを更新
                    tonoben._update_heartbeat()
                    
                    # 各エージェントのハートビートを更新
                    for agent in sample_agents:
                        agent._update_heartbeat()
                    
                    # メッセージ処理（ここではダミー）
                    time.sleep(5)  # 5秒間隔
                    
            except KeyboardInterrupt:
                print("\n" + HeianMessages.EVENT_LOOP_STOP)
        
        # イベントループを別スレッドで開始
        event_thread = threading.Thread(target=event_loop)
        event_thread.daemon = True
        event_thread.start()
        
        # メインスレッドで対話的な処理
        try:
            while True:
                command = input("\nコマンドを入力してください (help/exit/order): ").strip()
                
                if command == "exit":
                    break
                elif command == "help":
                    print_help()
                elif command == "order":
                    send_test_order(tonoben)
                elif command.startswith("order "):
                    instruction = command[6:]  # "order " を除去
                    send_custom_order(tonoben, instruction)
                else:
                    print(HeianMessages.UNKNOWN_COMMAND)
                    
        except KeyboardInterrupt:
            pass
        
        print(HeianMessages.SYSTEM_STOP)
        
    except Exception as e:
        print(HeianMessages.SYSTEM_STARTUP_ERROR.format(error=e))
        sys.exit(1)

def print_help():
    """ヘルプを表示"""
    print(HeianMessages.HELP_COMMANDS)

def send_test_order(tonoben):
    """テスト用の注文を送信"""
    message = Message(
        sender_id="kanpaku",
        receiver_id="tonoben",
        message_type="ORDER_RECEIVED",
        content={"instruction": "プロジェクトの基本構造を分析し、報告書を作成せよ"}
    )
    
    print("\n" + HeianMessages.HEAD_WITH_ORDER.format(instruction=message.content['instruction']))
    try:
        tonoben.process_message(message)
        print(HeianMessages.ORDER_PROCESSING_COMPLETE)
    except Exception as e:
        print(HeianMessages.ORDER_PROCESSING_ERROR.format(error=e))
        import traceback
        traceback.print_exc()

def send_custom_order(tonoben, instruction):
    """カスタム指示を送信"""
    message = Message(
        sender_id="kanpaku",
        receiver_id="tonoben",
        message_type="ORDER_RECEIVED",
        content={"instruction": instruction}
    )
    
    print("\n" + HeianMessages.CUSTOM_ORDER_SENT.format(instruction=instruction))
    tonoben.process_message(message)
    print(HeianMessages.ORDER_PROCESSING_DONE)

if __name__ == "__main__":
    main()

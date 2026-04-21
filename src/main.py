#!/usr/bin/env python3
"""
Kanpakuシステムのメインエントリーポイント（並列稼働版）
"""

import sys
import os
import time
import threading

# プロジェクトルートディレクトリをパスに追加
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.append(project_root)
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from agents.kanpaku import KanpakuAgent
from agents.tonoben import TonobenAgent
from agents.toneri import ToneriAgent
from db.state_manager import StateManager
from models.message import Message
from utility.messages import HeianMessages

def main():
    """Kanpakuシステムを起動し、朝廷の全官職を出仕させる"""
    print(HeianMessages.SYSTEM_STARTUP)
    
    try:
        state_manager = StateManager()
        
        # 1. 官職（エージェント）たちの任命と出仕準備
        # それぞれが独立した思考を持つAIとして初期化されます
        kanpaku = KanpakuAgent()
        tonoben = TonobenAgent()
        toneri_1 = ToneriAgent(agent_id="toneri_1")
        toneri_2 = ToneriAgent(agent_id="toneri_2")
        
        agents = [kanpaku, tonoben, toneri_1, toneri_2]
        
        # 2. 並列処理（マルチスレッド）による常駐ループの開始
        # 各エージェントの wait_for_orders (待機・通知受信ループ) を別々のスレッドで動かします
        threads = []
        for agent in agents:
            # daemon=True にすることで、メインプロセス終了時に共に退朝（終了）します
            t = threading.Thread(target=agent.wait_for_orders, daemon=True)
            t.start()
            threads.append(t)
            
        print(HeianMessages.KANPAKU_ATTENDANCE)
        print(HeianMessages.COMMAND_HELP)
        
        # 3. 帝（ユーザー）からの入力を受け付けるメインスレッド
        try:
            while True:
                command = input("\n> ").strip()
                
                if command == "exit":
                    break
                elif command.startswith("order "):
                    instruction = command[6:] # "order " を除去
                    send_mikado_order(state_manager, instruction)
                elif command:
                    print(HeianMessages.KANPAKU_INVALID_COMMAND)
                    
                # ログが流れるのを待つための小休止
                time.sleep(1)
                    
        except KeyboardInterrupt:
            pass
        
        print(HeianMessages.SYSTEM_SHUTDOWN)
        
    except Exception as e:
        print(HeianMessages.KANPAKU_STARTUP_ERROR.format(e=e))
        sys.exit(1)

def send_mikado_order(state_manager: StateManager, instruction: str):
    """帝（ユーザー）からの大号令を関白へ下賜する"""
    # 帝の言葉は、最高責任者である関白（Kanpaku）の文箱へ届けられます
    message = Message(
        sender_id="mikado",
        receiver_id="kanpaku",
        message_type="MIKADO_ORDER",
        content={"order": instruction}
    )
    
    # 通信網（InboxとPub/Sub）を使って正規のルートで投函
    state_manager.send_message(message)

if __name__ == "__main__":
    main()
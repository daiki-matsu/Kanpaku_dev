import time
from typing import Optional
from models.agents import Agent, AgentStatus
from models.message import Message
from db.state_manager import StateManager
from db.redis_client import RedisClient  # Added import statement
from utility.messages import HeianMessages
from src.infrastructure.llm_server_manager import GlobalServerManager

class BaseAgent:
    """朝廷に仕える全官職（エージェント）の礎となる振る舞い"""
    
    def __init__(self, agent_id: str, role: str, db=0):
        self.agent_id = agent_id
        self.role = role
        self.state_manager = StateManager()
        # RedisClient to use the specified database
        self.redis = RedisClient(host='localhost', port=6379, db=db)
        self.state_manager.redis = self.redis
        
        # 己の姿（ステータス）を定義し、蔵（Redis）に登録して出仕を宣言
        self.me = Agent(
            id=self.agent_id, 
            role=self.role, 
            status=AgentStatus.IDLE,
            last_heartbeat=time.time()
        )
        self.redis.save_agent(self.me)
        
        # 狼煙（Pub/Sub）を見張るための準備
        self.pubsub = self.redis.get_pubsub()
        self.channel = f"notify:{self.agent_id}"
        self.pubsub.subscribe(self.channel)
        
        # llama.cppサーバーの起動（管理対象の場合）
        self._start_llm_server()

    def wait_for_orders(self) -> None:
        """政務が下るのを待つ、無限の待機ループ"""
        print(HeianMessages.AGENT_ATTENDANCE.format(
            role=self.role,
            agent_id=self.agent_id
        ))
        
        try:
            while True:
                # 1. 文箱（Inbox）に溜まった文を確認
                message = self.redis.pop_inbox(self.agent_id)
                
                if message:
                    # 文があれば政務を開始
                    self._handle_message(message)
                else:
                    # 2. 文箱が空であれば、狼煙（Pub/Sub）を待ちながら小休止
                    # timeout=1.0 とすることで、1秒ごとに生存報告（ハートビート）を行えるようにする
                    notification = self.pubsub.get_message(timeout=1.0)
                    
                    if notification and notification['type'] == 'message':
                        event_type = notification['data']
                        print(HeianMessages.AGENT_WAKEUP.format(
                            agent_id=self.agent_id,
                            event_type=event_type
                        ))
                        # 次のループですぐに pop_inbox が呼ばれ、文を取り出します
                
                # 3. 生存報告（ハートビート）の更新
                self._update_heartbeat()

        except KeyboardInterrupt:
            print(HeianMessages.AGENT_RETIRE.format(agent_id=self.agent_id))

    def _handle_message(self, message: Message) -> None:
        """文を受け取った際の共通の振る舞い"""
        print(HeianMessages.AGENT_RECEIVED.format(
            agent_id=self.agent_id,
            sender_id=message.sender_id,
            msg_type=message.message_type
        ))
        self._change_status(AgentStatus.WORKING)
        
        try:
            # ------------------------------------------------
            # ここで実際の政務（LLM思考やファイル操作）を行う
            # （※ 各官職のクラスで process_message をオーバーライドさせます）
            # ------------------------------------------------
            self.process_message(message)
            
        except Exception as e:
            print(HeianMessages.AGENT_ERROR.format(
                agent_id=self.agent_id,
                error=e
            ))
            self._change_status(AgentStatus.ERROR)
            # エラーからの復帰ロジック（Sprint 5以降）までは、ひとまずログのみ残す
        finally:
            # 任務完了後、再び待機状態へ
            if self.me.status != AgentStatus.ERROR:
                self._change_status(AgentStatus.IDLE)

    def process_message(self, message: Message) -> None:
        """各官職（頭弁や舎人）が独自の知恵（処理）を実装する部分"""
        raise NotImplementedError("この官職には、文を解読する術（process_message）が備わっておりませぬ。")

    def _change_status(self, new_status: AgentStatus) -> None:
        """己の状態を更新し、蔵へ記す"""
        if self.me.status != new_status:
            self.me.status = new_status
            self.redis.save_agent(self.me)
            print(HeianMessages.AGENT_STATUS_CHANGE.format(
                agent_id=self.agent_id,
                status=new_status.value
            ))

    def _update_heartbeat(self) -> None:
        """生存していることを蔵へ知らせる"""
        self.me.last_heartbeat = time.time()
        self.redis.save_agent(self.me)
    
    def _start_llm_server(self) -> None:
        """このエージェント用のllama.cppサーバーを起動"""
        try:
            # エージェントごとのモデル名を取得
            model_name = self._get_model_name()
            
            # サーバーを起動
            success = GlobalServerManager.start_server(self.agent_id, model_name)
            if success:
                print(f" {self.agent_id}用のllama.cppサーバーを起動しました")
            else:
                print(f" {self.agent_id}用のllama.cppサーバーの起動に失敗しました")
        except Exception as e:
            print(f" {self.agent_id}用のサーバー起動エラー: {e}")
    
    def _stop_llm_server(self) -> None:
        """このエージェント用のllama.cppサーバーを停止"""
        try:
            GlobalServerManager.stop_server(self.agent_id)
            print(f" {self.agent_id}用のllama.cppサーバーを停止しました")
        except Exception as e:
            print(f" {self.agent_id}用のサーバー停止エラー: {e}")
    
    def _get_model_name(self) -> str:
        """エージェントごとのモデル名を取得"""
        model_mapping = {
            'kanpaku': 'gemma4_e2b',
            'tonoben': 'deepseek_coder_6_7b',
            'toneri_1': 'gemma4_e2b',
            'toneri_2': 'gemma4_e2b'
        }
        return model_mapping.get(self.agent_id, 'gemma4_e2b')
    
    def __del__(self):
        """デストラクタでサーバーを停止"""
        try:
            self._stop_llm_server()
        except:
            pass
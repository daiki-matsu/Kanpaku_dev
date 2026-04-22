from agents.base_agent import BaseAgent
from models.message import Message
from agents.llm_client import LLMClient
from src.infrastructure.llm_server_manager import GlobalServerManager

# Environment variable loader
def get_env_var(var_name: str) -> str:
    """Get environment variable value"""
    import os
    return os.getenv(var_name, "")

from utility.messages import HeianMessages
from utility.prompts import SystemPrompts

# グローバル変数としてPROMPTSを設定
PROMPTS = SystemPrompts()

class KanpakuAgent(BaseAgent):
    """帝の御心を汲み取り、朝廷全体を導く最高権力者（関白）"""
    
    def __init__(self):
        super().__init__(agent_id="kanpaku", role="function")
        # サーバーマネージャーからサーバーURLを取得
        server_manager = GlobalServerManager.get_server("kanpaku", "gemma4_e2b")
        server_url = server_manager.get_server_url()
        self.llm = LLMClient(agent_id="kanpaku", model_name="gemma4_e2b", server_url=server_url)

    def process_message(self, message: Message) -> None:
        """受け取った文（用件）に応じた政務を行う"""
        # 関白は帝（mikado や test_script）からの直接の詔勅のみを処理する
        if message.message_type == "MIKADO_ORDER":
            self._create_instruction(message)
        else:
            print(HeianMessages.KANPAKU_IGNORE.format(msg_type=message.message_type))

    def _create_instruction(self, message: Message) -> None:
        """帝の短い言葉を、頭弁が動ける詳細な指示書へと変換する"""
        order = message.content.get("order", "")
        print(HeianMessages.KANPAKU_RECEIVED.format(order=order))
        print(HeianMessages.KANPAKU_THINKING)

        # LLMへのプロンプト作成（構想の拡張）
        prompt = PROMPTS.KANPAKU_INSTRUCTION_GENERATION.format(order=order)
                
        try:
            # LLMによる指示書の生成（文字列）
            detailed_instruction = self.llm.generate(prompt)
            
            # 頭弁（tonoben）の文箱へ、生成した指示書を添えて文を投函する
            msg_to_tonoben = Message(
                sender_id=self.agent_id,
                receiver_id="tonoben",
                message_type="ORDER_RECEIVED",
                content={"instruction": detailed_instruction}
            )
            self.state_manager.send_message(msg_to_tonoben)
            
            print(HeianMessages.KANPAKU_SENT)

        except Exception as e:
            print(HeianMessages.AGENT_ERROR.format(agent_id=self.agent_id, error=str(e)))
            raise e
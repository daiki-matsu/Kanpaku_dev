#!/usr/bin/env python3
"""
Google Gemini API用のラッパー
gemini-3-flash-preview,gemini-3.1-flash-lite-previewモデルを使用
"""

import argparse
import sys
import os
from typing import Optional
import logging

try:
    from google import genai
except ImportError:
    raise ImportError("google-genaiパッケージがインストールされていません。'pip install google-genai'を実行してください。")

# モジュールとして実行される場合とインポートされる場合の両方に対応
try:
    from .env_loader import get_env_var
except ImportError:
    # モジュールとして直接実行される場合
    try:
        from connect_llm.env_loader import get_env_var
    except ImportError:
        # プロジェクトルートにパスを追加
        import sys
        import os
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        from connect_llm.env_loader import get_env_var


class GeminiWrapper:
    """Google Gemini APIのラッパークラス"""
    
    def __init__(self, model_name: str = "gemini-3.1-flash-lite-preview", api_key: Optional[str] = None):
        """
        GeminiWrapperを初期化
        
        Args:
            model_name: 使用するモデル名（デフォルト: gemini-3.1-flash-lite-preview）
            api_key: Google APIキー（指定がない場合は.envファイルから取得）
        """
        self.model_name = model_name
        
        # APIキーを設定（.envファイルから取得）
        if api_key is None:
            api_key = get_env_var("GOOGLE_API_KEY")
        
        if not api_key:
            raise ValueError("GOOGLE_API_KEYが.envファイルまたは環境変数に設定されていません")
        
        # 新しいGoogle GenAI SDKでクライアントを作成
        self.client = genai.Client(api_key=api_key)
    
    def __call__(self, prompt: str) -> str:
        """
        プロンプトを送信して応答を取得
        
        Args:
            prompt: 送信するプロンプト
            
        Returns:
            モデルの応答テキスト
        """
        try:
            # デバッグ用に入力をマスキングして表示
            logger = logging.getLogger(__name__)
            if logger.isEnabledFor(logging.DEBUG):
                masked_prompt = prompt[:50] + "..." if len(prompt) > 50 else prompt
                logger.debug(f"Geminiへの入力（マスキング済み）: {masked_prompt}")
            
            # 新しいGoogle GenAI SDKでAPIリクエストを送信
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            result = response.text
            
            # デバッグ用に出力をマスキングして表示
            if logger.isEnabledFor(logging.DEBUG):
                masked_result = result[:100] + "..." if len(result) > 100 else result
                logger.debug(f"Geminiからの出力（マスキング済み）: {masked_result}")
            
            return result
            
        except Exception as e:
            error_msg = f"Gemini APIエラー: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)


def main():
    """コマンドラインインターフェース"""
    parser = argparse.ArgumentParser(description="Google Gemini APIラッパー")
    parser.add_argument("prompt", nargs="?", help="送信するプロンプト（指定がない場合はstdinから読み込み）")
    parser.add_argument("--model", default="gemini-3.1-flash-lite-preview", 
                       help="使用するモデル名（デフォルト: gemini-3.1-flash-lite-preview）")
    parser.add_argument("--api-key", help="Google APIキー（指定がない場合は.envファイルから取得）")
    parser.add_argument("--print", action="store_true", 
                       help="結果を標準出力に表示（claude --printのように使用）")
    
    args = parser.parse_args()
    
    try:
        # ラッパーを初期化
        wrapper = GeminiWrapper(model_name=args.model, api_key=args.api_key)
        
        # プロンプトを取得
        if args.prompt:
            prompt = args.prompt
        else:
            # stdinから読み込み
            prompt = sys.stdin.read().strip()
        
        if not prompt:
            print("エラー: プロンプトが指定されていません", file=sys.stderr)
            sys.exit(1)
        
        # APIを呼び出し
        result = wrapper(prompt)
        
        # 結果を出力
        print(result)
            
    except Exception as e:
        logger.error(f"エラー: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()

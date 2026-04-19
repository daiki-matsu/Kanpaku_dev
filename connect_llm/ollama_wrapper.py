#!/usr/bin/env python3
"""
Ollama用のラッパー
qwen3-coder:30bとgemma4:26b-a4bに対応
"""

import argparse
import sys
import subprocess
import json
import requests
from typing import Optional, List, Dict, Any
import logging
import os

# モジュールとして実行される場合とインポートされる場合の両方に対応
try:
    from .env_loader import get_env_var
    from .debug_logger import DebugLogger
except ImportError:
    # モジュールとして直接実行される場合
    try:
        from connect_llm.env_loader import get_env_var
        from connect_llm.debug_logger import DebugLogger
    except ImportError:
        # プロジェクトルートにパスを追加
        import sys
        import os
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        from connect_llm.env_loader import get_env_var
        from connect_llm.debug_logger import DebugLogger


class OllamaWrapper:
    """Ollamaモデルのラッパークラス"""
    
    def __init__(self, model_name: str = "qwen3-coder:30b", 
                 host: Optional[str] = None):
        """
        OllamaWrapperを初期化
        
        Args:
            model_name: 使用するモデル名（デフォルト: qwen3-coder:30b）
            host: Ollamaサーバーのホスト（指定がない場合は.envファイルから取得）
        """
        self.model_name = model_name
        
        # ホストを設定（.envファイルから取得）
        if host is None:
            host = get_env_var("OLLAMA_HOST", "http://localhost:11434")
        
        self.host = host
        self.api_url = f"{host}/api/generate"
        self.tags_url = f"{host}/api/tags"
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.timeout = 60
        self.debug_logger = DebugLogger()
    
    def _check_connection(self) -> bool:
        """
        Ollamaサーバーへの接続を確認
        
        Returns:
            接続できている場合はTrue
        """
        try:
            response = self.session.get(self.tags_url, timeout=5)
            return response.status_code == 200
        except Exception as e:
            self.logger.debug(f"接続チェックエラー: {str(e)}")
            return False
    
    def _get_available_models(self) -> List[str]:
        """
        利用可能なモデルリストを取得
        
        Returns:
            モデル名のリスト
        """
        try:
            response = self.session.get(self.tags_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [model["name"] for model in data.get("models", [])]
        except Exception as e:
            self.logger.debug(f"モデル取得エラー: {str(e)}")
        return []
    
    def _call_api(self, prompt: str) -> str:
        """
        Ollama APIを直接呼び出し
        
        Args:
            prompt: 送信するプロンプト
            
        Returns:
            モデルの応答テキスト
        """
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False
        }
        
        try:
            response = self.session.post(self.api_url, json=payload)
            if response.status_code == 200:
                data = response.json()
                return data.get("response", "")
            else:
                raise Exception(f"APIエラー: {response.status_code}")
        except Exception as e:
            raise Exception(f"Ollama API呼び出しエラー: {str(e)}")
    
    def _call_cli(self, prompt: str) -> str:
        """
        Ollama CLIを呼び出し（APIフォールバック用）
        
        Args:
            prompt: 送信するプロンプト
            
        Returns:
            モデルの応答テキスト
        """
        try:
            cmd = ["ollama", "run", self.model_name, prompt]
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=60,
                input=prompt,
                encoding='utf-8'
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                raise Exception(f"CLIエラー: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            raise Exception("Ollama CLIがタイムアウトしました")
        except FileNotFoundError:
            raise Exception("Ollamaがインストールされていません")
        except Exception as e:
            raise Exception(f"Ollama CLI呼び出しエラー: {str(e)}")
    
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
            if self.logger.isEnabledFor(logging.DEBUG):
                masked_prompt = prompt[:50] + "..." if len(prompt) > 50 else prompt
                self.logger.debug(f"Ollamaへの入力 ({self.model_name})（マスキング済み）: {masked_prompt}")
            
            # まずAPIを試す
            if self._check_connection():
                result = self._call_api(prompt)
            else:
                # APIが使えない場合はCLIにフォールバック
                self.logger.debug("APIに接続できません。CLIを使用します。")
                result = self._call_cli(prompt)
            
            # フィルタリングせずに結果をそのまま使用
            filtered_result = result
            
            # デバッグログを保存
            self.debug_logger.save_log(self.model_name, prompt, result, filtered_result)
            
            # デバッグ用に出力をマスキングして表示
            if self.logger.isEnabledFor(logging.DEBUG):
                masked_result = filtered_result[:100] + "..." if len(filtered_result) > 100 else filtered_result
                self.logger.debug(f"Ollamaからの出力（マスキング済み）: {masked_result}")
            
            return filtered_result
            
        except Exception as e:
            error_msg = f"Ollamaエラー: {str(e)}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def list_models(self) -> List[str]:
        """
        利用可能なモデルを一覧表示
        
        Returns:
            モデル名のリスト
        """
        return self._get_available_models()


def main():
    """コマンドラインインターフェース"""
    parser = argparse.ArgumentParser(description="Ollamaモデル用ラッパー")
    parser.add_argument("prompt", nargs="?", help="送信するプロンプト（指定がない場合はstdinから読み込み）")
    parser.add_argument("--model", default="qwen3-coder:30b",
                       help="使用するモデル名（デフォルト: qwen3-coder:30b）")
    parser.add_argument("--host", help="Ollamaサーバーのホスト（指定がない場合は.envファイルから取得）")
    parser.add_argument("--list-models", action="store_true",
                       help="利用可能なモデルを一覧表示")
    parser.add_argument("--print", action="store_true",
                       help="結果を標準出力に表示（claude --printのように使用）")
    parser.add_argument("--debug-log", action="store_true",
                       help="デバッグログを表示")
    parser.add_argument("--clear-debug", action="store_true",
                       help="デバッグログをクリア")
    
    args = parser.parse_args()
    
    try:
        # ラッパーを初期化
        wrapper = OllamaWrapper(model_name=args.model, host=args.host)
        
        # デバッグログ表示
        if args.debug_log:
            wrapper.debug_logger.display_logs(limit=5)
            return
        
        # デバッグログクリア
        if args.clear_debug:
            wrapper.debug_logger.clear_logs()
            return
        
        # モデル一覧表示
        if args.list_models:
            models = wrapper.list_models()
            if models:
                print("利用可能なモデル:")
                for model in models:
                    print(f"  - {model}")
            else:
                print("利用可能なモデルが見つかりません")
            return
        
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
        logger = logging.getLogger(__name__)
        logger.error(f"エラー: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()

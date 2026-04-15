#!/usr/bin/env python3
"""
デバッグログ機能
AIモデルとの入出力を記録・管理する
"""

import os
import yaml
import logging
from datetime import datetime
from typing import List, Dict, Optional
from collections import OrderedDict


class DebugLogger:
    """デバッグログを管理するクラス"""
    
    def __init__(self, debug_file: Optional[str] = None):
        """
        DebugLoggerを初期化
        
        Args:
            debug_file: デバッグログファイルのパス（指定がない場合はデフォルトを使用）
        """
        if debug_file is None:
            # デフォルトのデバッグファイルパス
            current_dir = os.path.dirname(__file__)
            debug_file = os.path.join(current_dir, "debug", "debug.yaml")
        
        self.debug_file = debug_file
        self.logger = logging.getLogger(__name__)
    
    def save_log(self, model_name: str, prompt: str, raw_response: str, filtered_response: str):
        """
        デバッグログを保存
        
        Args:
            model_name: 使用したモデル名
            prompt: 入力プロンプト
            raw_response: 生の応答
            filtered_response: フィルタリング後の応答
        """
        try:
            # debugディレクトリがなければ作成
            os.makedirs(os.path.dirname(self.debug_file), exist_ok=True)
            
            # 既存のログを読み込む
            logs = self.load_logs()
            
            # 新しいログエントリを作成（順序を保証）
            log_entry = OrderedDict([
                ('timestamp', datetime.now().isoformat()),
                ('model', model_name),
                ('input', prompt),
                ('raw_output', raw_response),
                ('filtered_output', filtered_response)
            ])
            
            logs.append(log_entry)
            
            # ログを保存
            with open(self.debug_file, 'w', encoding='utf-8') as f:
                yaml.dump(logs, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
                
        except Exception as e:
            self.logger.warning(f"デバッグログの保存に失敗しました: {str(e)}")
    
    def load_logs(self) -> List[Dict]:
        """
        デバッグログを読み込む
        
        Returns:
            ログエントリのリスト
        """
        try:
            if os.path.exists(self.debug_file):
                with open(self.debug_file, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or []
            return []
        except Exception as e:
            self.logger.warning(f"デバッグログの読み込みに失敗しました: {str(e)}")
            return []
    
    def display_logs(self, limit: int = 5):
        """
        デバッグログを表示
        
        Args:
            limit: 表示するログの件数（最新から）
        """
        logs = self.load_logs()
        if logs:
            print(f"デバッグログ（最新{limit}件）:")
            for i, log in enumerate(logs[-limit:], 1):
                print(f"\n--- ログ {i} ---")
                print(f"タイムスタンプ: {log.get('timestamp', 'N/A')}")
                print(f"モデル: {log.get('model', 'N/A')}")
                print(f"入力: {log.get('input', 'N/A')[:100]}...")
                print(f"生の出力: {log.get('raw_output', 'N/A')[:200]}...")
                print(f"フィルタリング後の出力: {log.get('filtered_output', 'N/A')[:200]}...")
        else:
            print("デバッグログがありません")
    
    def clear_logs(self):
        """デバッグログをクリア"""
        try:
            if os.path.exists(self.debug_file):
                os.remove(self.debug_file)
                print("デバッグログをクリアしました")
            else:
                print("デバッグログがありません")
        except Exception as e:
            self.logger.error(f"デバッグログのクリアに失敗しました: {str(e)}")
    
    def get_latest_log(self) -> Optional[Dict]:
        """
        最新のログを取得
        
        Returns:
            最新のログエントリ、存在しない場合はNone
        """
        logs = self.load_logs()
        return logs[-1] if logs else None

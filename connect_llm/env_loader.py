#!/usr/bin/env python3
"""
CoDD LLMラッパー用環境変数ローダー
プロジェクトルートから.envファイルを読み込み
"""

import os
from pathlib import Path
from typing import Optional


def load_env_file(project_root: Optional[str] = None) -> None:
    """
    プロジェクトルートから.envファイルを読み込み
    
    Args:
        project_root: プロジェクトルートパス（指定がない場合は自動検出）
    """
    if project_root is None:
        # プロジェクトルートを自動検出（現在の作業ディレクトリ）
        project_root = Path.cwd()
    else:
        project_root = Path(project_root)
    
    env_file = project_root / ".env"
    
    if not env_file.exists():
        return
    
    # .envファイルを読み込み
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            
            # 引用符があれば削除
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            
            # 環境変数が未設定の場合のみ設定
            if key not in os.environ:
                os.environ[key] = value


def get_env_var(key: str, default: Optional[str] = None, project_root: Optional[str] = None) -> Optional[str]:
    """
    環境変数を取得（必要に応じて.envから読み込み）
    
    Args:
        key: 環境変数キー
        default: 見つからない場合のデフォルト値
        project_root: プロジェクトルートパス（オプション）
    
    Returns:
        環境変数の値またはデフォルト値
    """
    # .envファイルが未読み込みの場合は読み込み
    if key not in os.environ:
        load_env_file(project_root)
    
    return os.environ.get(key, default)


# モジュールインポート時に.envを自動読み込み
load_env_file()

import os
from typing import Dict, Any

class SafeIO:
    """
    舎人（Toneri）が外界（ファイルシステム）へ触れる際の
    絶対的な結界（サンドボックス）となる層
    """
    def __init__(self, base_project_dir: str = "/project"):
        # 許容される最上位の行事所（基準ディレクトリ）
        # ※実際の環境に合わせて初期化時に指定可能とします
        self.base_dir = os.path.abspath(base_project_dir)
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir, exist_ok=True)

    def _is_safe_path(self, target_path: str) -> bool:
        """指定されたパスが許可された領土（base_dir）の配下にあるか検分する"""
        # ホームディレクトリ展開をブロック
        if target_path.startswith('~'):
            return False
        
        # Windowsスタイルのバックスラッシュを処理（フォワードスラッシュに変換）
        normalized_path = target_path.replace('\\', '/')
        
        # より確実な絶対パス検出
        is_absolute = (os.path.isabs(target_path) or 
                       target_path.startswith('/') or 
                       target_path.startswith('\\') or
                       normalized_path.startswith('/') or
                       (len(target_path) > 1 and target_path[1] == ':'))
        
        # 相対パスでのディレクトリトラバーサル試行をチェック
        if not is_absolute:
            # 元のパスと正規化されたパスの両方で..をチェック
            if (".." in target_path.split(os.sep) or 
                ".." in target_path.split("/") or 
                ".." in normalized_path.split("/")):
                return False
        
        # 絶対パスの場合、base_dirの配下にあるかチェック
        if is_absolute:
            abs_target_path = os.path.abspath(target_path)
            return abs_target_path.startswith(self.base_dir)
        else:
            # 相対パスの場合、base_dirに対して解決してチェック
            abs_target_path = os.path.abspath(os.path.join(self.base_dir, target_path))
            return abs_target_path.startswith(self.base_dir)

    def safe_read(self, file_path: str) -> Dict[str, Any]:
        """安全を担保した上で巻物（ファイル）を読み込む"""
        if not self._is_safe_path(file_path):
            return {
                "status": "error",
                "action": "read",
                "path": file_path,
                "logs": "不敬なる越権行為（許可されていない領域へのアクセス）を検知いたしました。"
            }
        
        abs_path = os.path.abspath(os.path.join(self.base_dir, file_path))
        if not os.path.exists(abs_path):
            return {
                "status": "error",
                "action": "read",
                "path": file_path,
                "logs": "ご指定の巻物（ファイル）が見つかりませぬ。"
            }
        
        try:
            with open(abs_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return {
                "status": "success",
                "action": "read",
                "path": file_path,
                "logs": "読み込みに成功いたしました。",
                "content": content
            }
        except Exception as e:
            return {
                "status": "error",
                "action": "read",
                "path": file_path,
                "logs": f"読み込み中に不測の事態が発生: {str(e)}"
            }

    def safe_write(self, file_path: str, content: str) -> Dict[str, Any]:
        """安全を担保した上で巻物（ファイル）に書き込む"""
        if not self._is_safe_path(file_path):
            return {
                "status": "error",
                "action": "write",
                "path": file_path,
                "logs": "不敬なる越権行為（許可されていない領域へのアクセス）を検知いたしました。"
            }
        
        abs_path = os.path.abspath(os.path.join(self.base_dir, file_path))
        
        # 途中のディレクトリが存在しなければ自動で作成
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        
        try:
            with open(abs_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return {
                "status": "success", 
                "action": "write",
                "path": file_path,
                "logs": "書き込みに成功いたしました。"
            }
        except Exception as e:
            return {
                "status": "error", 
                "action": "write",
                "path": file_path,
                "logs": f"書き込み中に不測の事態が発生: {str(e)}"
            }
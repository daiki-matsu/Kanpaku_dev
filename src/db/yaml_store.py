import yaml
import os
from datetime import datetime

class YamlStore:
    """事の次第を絵巻（YAML）に書き留める書記官"""
    def __init__(self, base_dir="docs/history"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def save_history(self, entity_type: str, entity_id: str, data: dict) -> None:
        """
        指定されたエンティティ（task, agent等）の履歴をYAMLに追記する
        例: docs/history/tasks/1_1.yaml
        """
        dir_path = os.path.join(self.base_dir, f"{entity_type}s")
        os.makedirs(dir_path, exist_ok=True)
        file_path = os.path.join(dir_path, f"{entity_id}.yaml")

        # 追記用にタイムスタンプを付与してリスト形式で保存
        record = {
            "recorded_at": datetime.now().isoformat(),
            "state": data
        }
        
        # 既存の履歴があれば読み込み、なければ新規リスト
        history = []
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                history = yaml.safe_load(f) or []
        
        history.append(record)

        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(history, f, allow_unicode=True, default_flow_style=False)
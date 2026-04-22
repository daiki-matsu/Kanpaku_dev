import pytest
import redis
import time
import tempfile
import shutil
from pathlib import Path
import sys
import os
import threading
from unittest.mock import Mock

# テスト対象のモジュールをパスに追加
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from models.tasks import Task, TaskStatus, SettingInfo, AssignedInfo, TimingInfo
from models.agents import Agent, AgentStatus
from models.message import Message
from models.events import Event
from models.state import SystemState
from models.lock import FileLock
from db.state_manager import StateManager
from db.redis_client import RedisClient
from db.yaml_store import YamlStore
from agents.base_agent import BaseAgent

@pytest.fixture(scope="session")
def test_redis():
    """テスト用のRedis接続を提供"""
    # テスト用Redisデータベース（db=2）を使用
    client = redis.Redis(host='localhost', port=6379, db=2, decode_responses=True)
    
    # テスト前にクリーンアップ
    client.flushdb()
    
    yield client
    
    # テスト後にクリーンアップ
    client.flushdb()
    client.close()

@pytest.fixture
def redis_client(test_redis):
    """RedisClient's test instance with clean Redis"""
    return RedisClient(host='localhost', port=6379, db=2)

@pytest.fixture
def temp_history_dir():
    """一時的な履歴保存ディレクトリ"""
    temp_dir = tempfile.mkdtemp(prefix="kanpaku_sprint3_test_")
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def yaml_store(temp_history_dir):
    """YamlStoreのテスト用インスタンス"""
    return YamlStore(base_dir=temp_history_dir)

@pytest.fixture
def clean_redis(test_redis):
    """Clean Redis before each test"""
    test_redis.flushdb()
    yield test_redis

@pytest.fixture
def state_manager(clean_redis, yaml_store):
    """StateManager's test instance with clean Redis"""
    sm = StateManager()
    sm.redis = RedisClient(host='localhost', port=6379, db=2)
    sm.yaml = yaml_store
    return sm

@pytest.fixture
def mock_toneri_agents():
    """モックの舎人エージェントを2体作成"""
    toneri_1 = Mock(spec=BaseAgent)
    toneri_1.agent_id = "toneri_1"
    toneri_1.role = "舎人"
    toneri_1.status = AgentStatus.IDLE
    
    toneri_2 = Mock(spec=BaseAgent)
    toneri_2.agent_id = "toneri_2"
    toneri_2.role = "舎人"
    toneri_2.status = AgentStatus.IDLE
    
    return {"toneri_1": toneri_1, "toneri_2": toneri_2}

@pytest.fixture
def sample_task_for_lock():
    """ロックテスト用のサンプルタスク"""
    current_time = int(time.time())
    return Task(
        id="lock_test_task",
        status=TaskStatus.ASSIGNED,
        setting=SettingInfo(
            bloom_level=2,
            depends_on=[],
            priority=50,
            goal="ロックテスト用タスク",
            command="write_file('src/main.py', 'print(\"hello\")')",
            type="file_write"
        ),
        timing=TimingInfo(created_at=current_time, updated_at=current_time),
        assigned=AssignedInfo(to="toneri_1", echo_message="テスト用指示")
    )

@pytest.fixture
def parallel_execution_context():
    """並列実行テスト用のコンテキスト"""
    results = []
    errors = []
    lock = threading.Lock()
    
    def add_result(result):
        with lock:
            results.append(result)
    
    def add_error(error):
        with lock:
            errors.append(error)
    
    return {
        "results": results,
        "errors": errors,
        "add_result": add_result,
        "add_error": add_error,
        "lock": lock
    }

# テスト実行前のセットアップ
def pytest_sessionstart(session):
    """テストセッション開始時のセットアップ"""
    print("\n=== Sprint 3 テスト開始 ===")
    print("Redisサーバーが起動していることを確認してください")
    print("排他制御と並列処理のテストを実施します")

def pytest_sessionfinish(session, exitstatus):
    """テストセッション終了時のクリーンアップ"""
    print("\n=== Sprint 3 テスト完了 ===")

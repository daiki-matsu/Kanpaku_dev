import pytest
import redis
import time
import tempfile
import shutil
import threading
from pathlib import Path
import sys
import os

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
    """RedisClient's test instance with test Redis"""
    return RedisClient(host='localhost', port=6379, db=2)

@pytest.fixture
def temp_history_dir():
    """一時的な履歴保存ディレクトリ"""
    temp_dir = tempfile.mkdtemp(prefix="kanpaku_test_")
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def yaml_store(temp_history_dir):
    """YamlStoreのテスト用インスタンス"""
    return YamlStore(base_dir=temp_history_dir)

@pytest.fixture
def state_manager(redis_client, yaml_store):
    """StateManager's test instance"""
    sm = StateManager()
    sm.redis = redis_client
    sm.yaml = yaml_store
    return sm

@pytest.fixture
def sample_task():
    """テスト用のサンプルタスク"""
    current_time = int(time.time())
    return Task(
        id="integration_test_task",
        status=TaskStatus.CREATED,
        setting=SettingInfo(
            bloom_level=3,
            depends_on=[],
            priority=50,
            goal="統合テスト用タスク",
            command="テストコマンド",
            type="test"
        ),
        timing=TimingInfo(created_at=current_time, updated_at=current_time)
    )

@pytest.fixture
def sample_agent():
    """テスト用のサンプルエージェント"""
    return Agent(
        id="integration_test_agent",
        role="統合テスト役職",
        status=AgentStatus.IDLE,
        last_heartbeat=time.time()
    )

@pytest.fixture
def event_loop_timeout():
    """イベントループテスト用のタイムアウト設定"""
    return 10.0  # 10秒

# テスト実行前のセットアップ
def pytest_sessionstart(session):
    """テストセッション開始時のセットアップ"""
    print("\n=== Sprint 2.1 統合テスト開始 ===")
    print("Redisサーバーが起動していることを確認してください")
    print("LLM接続環境が整っていることを確認してください")

def pytest_sessionfinish(session, exitstatus):
    """テストセッション終了時のクリーンアップ"""
    print("\n=== Sprint 2.1 統合テスト完了 ===")

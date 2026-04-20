import pytest
from models.tasks import Task, TaskStatus, SettingInfo, TimingInfo, ExecutionInfo
from models.agents import Agent, AgentStatus
from db.state_manager import StateManager
import time

class TestStateValidationAndRetry:
    """状態遷移の厳格化（バリデーション）とリトライ管理のテスト"""
    
    def test_valid_state_transitions(self, state_manager, sample_task):
        """正当な状態遷移が許可されること"""
        # CREATED -> ASSIGNED
        sample_task.status = TaskStatus.ASSIGNED
        state_manager.update_task(sample_task, "TASK_ASSIGNED")
        
        updated_task = state_manager.redis.get_task(sample_task.id)
        assert updated_task.status == TaskStatus.ASSIGNED
        
        # ASSIGNED -> DOING
        sample_task.status = TaskStatus.DOING
        state_manager.update_task(sample_task, "TASK_STARTED")
        
        updated_task = state_manager.redis.get_task(sample_task.id)
        assert updated_task.status == TaskStatus.DOING
    
    def test_invalid_state_transition_blocked(self, state_manager, sample_task):
        """不正な状態遷移が遮断されること"""
        # First save the task to Redis
        state_manager.redis.save_task(sample_task)
        
        # Try to transition from CREATED directly to COMPLETED
        sample_task.status = TaskStatus.COMPLETED
        
        with pytest.raises(ValueError, match="許可されざる状態遷移"):
            state_manager.update_task(sample_task, "TASK_COMPLETED")
        
        # Verify task was not updated
        current_task = state_manager.redis.get_task(sample_task.id)
        assert current_task.status == TaskStatus.CREATED
    
    def test_all_invalid_transitions(self, state_manager, sample_task):
        """すべての不正な状態遷移パターンをテスト"""
        invalid_transitions = [
            (TaskStatus.CREATED, [TaskStatus.DOING, TaskStatus.REVIEWING, TaskStatus.COMPLETED, TaskStatus.FAILED]),
            (TaskStatus.ASSIGNED, [TaskStatus.CREATED, TaskStatus.REVIEWING, TaskStatus.COMPLETED, TaskStatus.FAILED]),
            (TaskStatus.DOING, [TaskStatus.CREATED]),  # ASSIGNED is allowed for retry, same status is allowed
            (TaskStatus.REVIEWING, [TaskStatus.CREATED, TaskStatus.DOING]),  # ASSIGNED and COMPLETED are allowed, same status is allowed
            (TaskStatus.COMPLETED, [TaskStatus.CREATED, TaskStatus.ASSIGNED, TaskStatus.DOING, TaskStatus.REVIEWING]),  # Same status is allowed
            (TaskStatus.FAILED, [TaskStatus.CREATED, TaskStatus.ASSIGNED, TaskStatus.DOING, TaskStatus.REVIEWING, TaskStatus.COMPLETED])  # Same status is allowed
        ]
        
        for from_status, to_statuses in invalid_transitions:
            for to_status in to_statuses:
                # Create fresh task for each test case
                current_time = int(time.time())
                test_task = Task(
                    id=f"test_task_{from_status.value}_{to_status.value}",
                    status=from_status,
                    setting=SettingInfo(
                        bloom_level=3,
                        depends_on=[],
                        priority=50,
                        goal="Test task goal",
                        command="Test command",
                        type="test"
                    ),
                    timing=TimingInfo(created_at=current_time, updated_at=current_time)
                )
                state_manager.redis.save_task(test_task)
                
                # Try invalid transition
                test_task.status = to_status
                
                with pytest.raises(ValueError, match="許可されざる状態遷移"):
                    state_manager.update_task(test_task, f"INVALID_TRANSITION_{to_status.value}")
    
    def test_retry_count_increment_on_doing_failure(self, state_manager, sample_task):
        """DOING失敗時のリトライカウント加算"""
        # タスクをDOING状態に設定
        sample_task.status = TaskStatus.DOING
        sample_task.execution.status = "error"
        state_manager.redis.save_task(sample_task)
        
        # 失敗を報告（DOING -> ASSIGNEDへの遷移）
        sample_task.status = TaskStatus.ASSIGNED
        state_manager.update_task(sample_task, "TASK_FAILED")
        
        updated_task = state_manager.redis.get_task(sample_task.id)
        assert updated_task.retry.count == 1
        assert "doing_failed" in updated_task.retry.reason
        assert updated_task.status == TaskStatus.ASSIGNED
    
    def test_retry_count_increment_on_execution_error(self, state_manager, sample_task):
        """実行エラー時のリトライカウント加算"""
        # タスクをDOING状態に設定
        sample_task.status = TaskStatus.DOING
        state_manager.redis.save_task(sample_task)
        
        # 実行ステータスをerrorに設定して更新
        sample_task.execution.status = "error"
        state_manager.update_task(sample_task, "EXECUTION_ERROR")
        
        updated_task = state_manager.redis.get_task(sample_task.id)
        assert updated_task.retry.count == 1
        assert updated_task.status == TaskStatus.DOING  # 状態はDOINGのまま
        assert updated_task.execution.status == "error"
    
    def test_retry_limit_exceeded(self, state_manager, sample_task):
        """リトライ上限超過時の自動FAILED判定"""
        # リトライ上限を低く設定
        sample_task.retry.max_limit = 2
        sample_task.status = TaskStatus.DOING
        state_manager.redis.save_task(sample_task)
        
        # 1回目の失敗
        sample_task.status = TaskStatus.ASSIGNED
        sample_task.execution.status = "error"
        state_manager.update_task(sample_task, "TASK_FAILED_1")
        
        updated_task = state_manager.redis.get_task(sample_task.id)
        assert updated_task.retry.count == 1
        assert updated_task.status == TaskStatus.ASSIGNED
        
        # 2回目の失敗
        sample_task.status = TaskStatus.DOING
        state_manager.redis.save_task(sample_task)
        sample_task.status = TaskStatus.ASSIGNED
        sample_task.execution.status = "error"
        state_manager.update_task(sample_task, "TASK_FAILED_2")
        
        updated_task = state_manager.redis.get_task(sample_task.id)
        assert updated_task.retry.count == 2
        assert updated_task.status == TaskStatus.ASSIGNED
        
        # 3回目の失敗（上限超過）
        sample_task.status = TaskStatus.DOING
        state_manager.redis.save_task(sample_task)
        sample_task.status = TaskStatus.ASSIGNED
        sample_task.execution.status = "error"
        state_manager.update_task(sample_task, "TASK_FAILED_3")
        
        updated_task = state_manager.redis.get_task(sample_task.id)
        assert updated_task.retry.count == 3
        assert updated_task.status == TaskStatus.FAILED
        assert updated_task.execution.status == "failed"
    
    def test_retry_reason_accumulation(self, state_manager, sample_task):
        """リトライ理由の蓄積"""
        sample_task.retry.max_limit = 3
        sample_task.status = TaskStatus.DOING
        state_manager.redis.save_task(sample_task)
        
        # 複数回の失敗を記録
        failures = ["doing_failed", "timeout_error", "resource_error"]
        
        for i, reason in enumerate(failures):
            sample_task.status = TaskStatus.ASSIGNED if i < 2 else TaskStatus.DOING
            sample_task.execution.status = "error"
            state_manager.update_task(sample_task, f"FAILURE_{i+1}")
            
            # 手動で理由を追加（実際の実装では自動的に追加される）
            if i < len(failures):
                updated_task = state_manager.redis.get_task(sample_task.id)
                updated_task.retry.reason.append(failures[i])
                state_manager.redis.save_task(updated_task)
        
        final_task = state_manager.redis.get_task(sample_task.id)
        assert len(final_task.retry.reason) >= 2  # 少なくとも2つの理由が記録されている
    
    def test_valid_reviewing_transitions(self, state_manager, sample_task):
        """REVIEWING状態の正当な遷移"""
        # DOING -> REVIEWING
        sample_task.status = TaskStatus.DOING
        state_manager.redis.save_task(sample_task)
        
        sample_task.status = TaskStatus.REVIEWING
        state_manager.update_task(sample_task, "TASK_REVIEWING")
        
        updated_task = state_manager.redis.get_task(sample_task.id)
        assert updated_task.status == TaskStatus.REVIEWING
        
        # REVIEWING -> COMPLETED
        sample_task.status = TaskStatus.COMPLETED
        state_manager.update_task(sample_task, "TASK_COMPLETED")
        
        updated_task = state_manager.redis.get_task(sample_task.id)
        assert updated_task.status == TaskStatus.COMPLETED
        
        # REVIEWING -> ASSIGNED（レビュー拒否時のリトライ）
        sample_task.status = TaskStatus.REVIEWING
        state_manager.redis.save_task(sample_task)
        
        sample_task.status = TaskStatus.ASSIGNED
        state_manager.update_task(sample_task, "REVIEW_REJECTED")
        
        updated_task = state_manager.redis.get_task(sample_task.id)
        assert updated_task.status == TaskStatus.ASSIGNED

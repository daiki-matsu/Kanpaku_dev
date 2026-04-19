import pytest
from datetime import datetime
from src.models.tasks import Task, TaskStatus, SettingInfo, AssignedInfo, AnswerInfo, ExecutionInfo, ReviewInfo, RetryInfo, TimingInfo
from src.models.agents import Agent, AgentStatus
from src.models.events import Event
from src.models.state import SystemState
from src.models.lock import FileLock

class TestTaskModel:
    """Task model unit tests for Sprint 1"""

    def test_task_creation_minimal(self):
        """Minimal task creation test"""
        task = Task(id="task_001")
        
        assert task.id == "task_001"
        assert task.status == TaskStatus.CREATED
        assert isinstance(task.setting, SettingInfo)
        assert isinstance(task.assigned, AssignedInfo)
        assert isinstance(task.answer, AnswerInfo)
        assert isinstance(task.execution, ExecutionInfo)
        assert isinstance(task.review, ReviewInfo)
        assert isinstance(task.retry, RetryInfo)
        assert isinstance(task.timing, TimingInfo)

    def test_task_status_enum(self):
        """TaskStatus enum test"""
        assert TaskStatus.CREATED == "created"
        assert TaskStatus.ASSIGNED == "assigned"
        assert TaskStatus.DOING == "doing"
        assert TaskStatus.REVIEWING == "reviewing"
        assert TaskStatus.COMPLETED == "completed"
        assert TaskStatus.FAILED == "failed"

    def test_task_with_complete_data(self):
        """Complete task data test"""
        task = Task(
            id="task_002",
            status=TaskStatus.ASSIGNED,
            setting=SettingInfo(
                bloom_level=3,
                depends_on=["task_001"],
                priority=1,
                goal="Test goal",
                command="test command",
                type="test"
            ),
            assigned=AssignedInfo(
                to="toneri_1",
                echo_message="Please execute this task"
            ),
            answer=AnswerInfo(
                status="success",
                summary="Task completed",
                details="Detailed explanation"
            ),
            execution=ExecutionInfo(
                status="completed",
                action="write_file",
                path="/project/test.txt",
                logs="Execution successful"
            ),
            review=ReviewInfo(
                status="approved",
                score=85,
                feedback="Good work"
            ),
            retry=RetryInfo(
                count=2,
                reason=["timeout", "error"]
            ),
            timing=TimingInfo(
                created_at=1234567890,
                updated_at=1234567900
            )
        )
        
        assert task.id == "task_002"
        assert task.status == TaskStatus.ASSIGNED
        assert task.setting.priority == 1
        assert task.assigned.to == "toneri_1"
        assert task.answer.status == "success"
        assert task.execution.status == "completed"
        assert task.review.score == 85
        assert task.retry.count == 2
        assert task.timing.created_at == 1234567890

class TestAgentModel:
    """Agent model unit tests for Sprint 1"""

    def test_agent_creation_minimal(self):
        """Minimal agent creation test"""
        agent = Agent(id="toneri_1", role="toneri")
        
        assert agent.id == "toneri_1"
        assert agent.role == "toneri"
        assert agent.status == AgentStatus.IDLE
        assert agent.current_task_id is None
        assert agent.last_heartbeat is None

    def test_agent_status_enum(self):
        """AgentStatus enum test"""
        assert AgentStatus.IDLE == "idle"
        assert AgentStatus.THINKING == "thinking"
        assert AgentStatus.WORKING == "working"
        assert AgentStatus.ERROR == "error"
        assert AgentStatus.RETRYING == "retrying"

    def test_agent_with_complete_data(self):
        """Complete agent data test"""
        agent = Agent(
            id="toneri_2",
            role="toneri",
            status=AgentStatus.WORKING,
            current_task_id="task_001",
            last_heartbeat=1234567890.5
        )
        
        assert agent.id == "toneri_2"
        assert agent.role == "toneri"
        assert agent.status == AgentStatus.WORKING
        assert agent.current_task_id == "task_001"
        assert agent.last_heartbeat == 1234567890.5

class TestEventModel:
    """Event model unit tests for Sprint 1"""

    def test_event_creation_minimal(self):
        """Minimal event creation test"""
        event = Event(event_id="event_001", event_type="TASK_CREATED")
        
        assert event.event_id == "event_001"
        assert event.event_type == "TASK_CREATED"
        assert isinstance(event.timestamp, datetime)
        assert event.agent_id is None
        assert event.task_id is None
        assert event.details == {}

    def test_event_with_complete_data(self):
        """Complete event data test"""
        test_time = datetime(2023, 1, 1, 12, 0, 0)
        event = Event(
            event_id="event_002",
            event_type="TASK_ASSIGNED",
            timestamp=test_time,
            agent_id="toneri_1",
            task_id="task_001",
            details={"priority": "high", "assigned_by": "toben"}
        )
        
        assert event.event_id == "event_002"
        assert event.event_type == "TASK_ASSIGNED"
        assert event.timestamp == test_time
        assert event.agent_id == "toneri_1"
        assert event.task_id == "task_001"
        assert event.details["priority"] == "high"

class TestSystemStateModel:
    """SystemState model unit tests for Sprint 1"""

    def test_system_state_creation(self):
        """SystemState creation test"""
        state = SystemState(
            active_agents=3,
            tasks_doing=2,
            tasks_completed=10,
            last_updated=1234567890.0
        )
        
        assert state.active_agents == 3
        assert state.tasks_doing == 2
        assert state.tasks_completed == 10
        assert state.last_updated == 1234567890.0

    def test_system_state_defaults(self):
        """SystemState default values test"""
        state = SystemState(last_updated=1234567890.0)
        
        assert state.active_agents == 0
        assert state.tasks_doing == 0
        assert state.tasks_completed == 0
        assert state.last_updated == 1234567890.0

class TestFileLockModel:
    """FileLock model unit tests for Sprint 1"""

    def test_file_lock_creation(self):
        """FileLock creation test"""
        lock = FileLock(
            target_path="/project/test.txt",
            locked_by="toneri_1",
            locked_at=1234567890.0,
            expires_at=1234567950.0
        )
        
        assert lock.target_path == "/project/test.txt"
        assert lock.locked_by == "toneri_1"
        assert lock.locked_at == 1234567890.0
        assert lock.expires_at == 1234567950.0

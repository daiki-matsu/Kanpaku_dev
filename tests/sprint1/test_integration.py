import pytest
import tempfile
import os
from datetime import datetime
from src.executor.safe_io import SafeIO
from src.models.tasks import Task, TaskStatus
from src.models.agents import Agent, AgentStatus
from src.models.events import Event
from src.models.state import SystemState
from src.models.lock import FileLock

class TestSprint1Integration:
    """Sprint 1 integration tests for MVP functionality"""

    def test_complete_task_workflow(self, temp_project_dir):
        """Complete task workflow test"""
        # Initialize SafeIO
        safe_io = SafeIO(base_project_dir=temp_project_dir)
        
        # Create task
        task = Task(
            id="task_001",
            status=TaskStatus.CREATED,
            setting={
                "goal": "Create test file",
                "command": "write_file",
                "priority": 1
            }
        )
        
        # Create agent
        agent = Agent(
            id="toneri_1",
            role="toneri",
            status=AgentStatus.IDLE
        )
        
        # Simulate task assignment
        task.status = TaskStatus.ASSIGNED
        task.assigned.to = "toneri_1"
        agent.status = AgentStatus.THINKING
        agent.current_task_id = "task_001"
        
        # Create event for assignment
        assignment_event = Event(
            event_id="event_001",
            event_type="TASK_ASSIGNED",
            agent_id="toneri_1",
            task_id="task_001",
            details={"assigned_by": "toben"}
        )
        
        # Verify assignment
        assert task.status == TaskStatus.ASSIGNED
        assert agent.status == AgentStatus.THINKING
        assert agent.current_task_id == "task_001"
        assert assignment_event.event_type == "TASK_ASSIGNED"
        
        # Simulate task execution
        agent.status = AgentStatus.WORKING
        task.status = TaskStatus.DOING
        
        # Execute file operation using SafeIO
        file_content = "This is a test file created by toneri_1"
        write_result = safe_io.safe_write("test_output.txt", file_content)
        
        assert write_result["status"] == "success"
        
        # Update task with execution result
        task.execution.status = "completed"
        task.execution.action = "write_file"
        task.execution.path = "test_output.txt"
        task.execution.logs = write_result["logs"]
        
        # Read back the file to verify
        read_result = safe_io.safe_read("test_output.txt")
        assert read_result["status"] == "success"
        assert read_result["content"] == file_content
        
        # Complete task
        task.status = TaskStatus.COMPLETED
        task.answer.status = "success"
        task.answer.summary = "File created successfully"
        agent.status = AgentStatus.IDLE
        agent.current_task_id = None
        
        # Verify final state
        assert task.status == TaskStatus.COMPLETED
        assert agent.status == AgentStatus.IDLE
        assert agent.current_task_id is None

    def test_agent_state_transitions(self):
        """Agent state transition test"""
        agent = Agent(id="toneri_1", role="toneri")
        
        # Initial state
        assert agent.status == AgentStatus.IDLE
        
        # Transition to thinking
        agent.status = AgentStatus.THINKING
        agent.current_task_id = "task_001"
        assert agent.status == AgentStatus.THINKING
        assert agent.current_task_id == "task_001"
        
        # Transition to working
        agent.status = AgentStatus.WORKING
        assert agent.status == AgentStatus.WORKING
        
        # Transition back to idle
        agent.status = AgentStatus.IDLE
        agent.current_task_id = None
        assert agent.status == AgentStatus.IDLE
        assert agent.current_task_id is None

    def test_task_status_validation(self):
        """Task status validation test"""
        task = Task(id="task_001")
        
        # Valid transitions according to MVP plan
        valid_transitions = [
            (TaskStatus.CREATED, TaskStatus.ASSIGNED),
            (TaskStatus.ASSIGNED, TaskStatus.DOING),
            (TaskStatus.DOING, TaskStatus.REVIEWING),
            (TaskStatus.REVIEWING, TaskStatus.COMPLETED),
        ]
        
        for from_status, to_status in valid_transitions:
            task.status = from_status
            task.status = to_status  # This should be valid
            assert task.status == to_status

    def test_safe_io_security_boundaries(self, temp_project_dir):
        """SafeIO security boundary test"""
        safe_io = SafeIO(base_project_dir=temp_project_dir)
        
        # Test various attack attempts
        malicious_paths = [
            "../etc/passwd",
            "/etc/passwd",
            "../../../windows/system32/config",
            "..\\..\\windows\\system32\\config",
            "/root/.ssh/id_rsa",
            "~/.ssh/id_rsa"
        ]
        
        for malicious_path in malicious_paths:
            # All read attempts should fail
            read_result = safe_io.safe_read(malicious_path)
            assert read_result["status"] == "error"
            assert "不敬なる越権行為" in read_result["logs"].lower()
            
            # All write attempts should fail
            write_result = safe_io.safe_write(malicious_path, "malicious content")
            assert write_result["status"] == "error"
            assert "不敬なる越権行為" in write_result["logs"].lower()

    def test_event_stream_simulation(self):
        """Event stream simulation test"""
        events = []
        
        # Create sequence of events for a task lifecycle
        task_id = "task_001"
        agent_id = "toneri_1"
        
        # Task creation
        events.append(Event(
            event_id="event_001",
            event_type="TASK_CREATED",
            task_id=task_id,
            details={"priority": "high"}
        ))
        
        # Task assignment
        events.append(Event(
            event_id="event_002",
            event_type="TASK_ASSIGNED",
            agent_id=agent_id,
            task_id=task_id,
            details={"assigned_by": "toben"}
        ))
        
        # Task started
        events.append(Event(
            event_id="event_003",
            event_type="TASK_STARTED",
            agent_id=agent_id,
            task_id=task_id,
            details={}
        ))
        
        # Task completed
        events.append(Event(
            event_id="event_004",
            event_type="TASK_COMPLETED",
            agent_id=agent_id,
            task_id=task_id,
            details={"execution_time": 45.2}
        ))
        
        # Verify event sequence
        assert len(events) == 4
        assert events[0].event_type == "TASK_CREATED"
        assert events[1].event_type == "TASK_ASSIGNED"
        assert events[2].event_type == "TASK_STARTED"
        assert events[3].event_type == "TASK_COMPLETED"
        
        # Verify all events have proper timestamps
        for event in events:
            assert isinstance(event.timestamp, datetime)

    def test_system_state_tracking(self):
        """System state tracking test"""
        state = SystemState(last_updated=1234567890.0)
        
        # Initial state
        assert state.active_agents == 0
        assert state.tasks_doing == 0
        assert state.tasks_completed == 0
        
        # Simulate agents becoming active
        state.active_agents = 2
        state.last_updated = 1234567891.0
        
        # Simulate tasks in progress
        state.tasks_doing = 3
        state.last_updated = 1234567892.0
        
        # Simulate task completion
        state.tasks_doing = 2
        state.tasks_completed = 1
        state.last_updated = 1234567893.0
        
        # Verify final state
        assert state.active_agents == 2
        assert state.tasks_doing == 2
        assert state.tasks_completed == 1
        assert state.last_updated == 1234567893.0

    def test_file_lock_simulation(self):
        """File lock simulation test"""
        current_time = 1234567890.0
        
        # Create lock
        lock = FileLock(
            target_path="/project/important.txt",
            locked_by="toneri_1",
            locked_at=current_time,
            expires_at=current_time + 300  # 5 minutes TTL
        )
        
        # Verify lock properties
        assert lock.target_path == "/project/important.txt"
        assert lock.locked_by == "toneri_1"
        assert lock.locked_at == current_time
        assert lock.expires_at == current_time + 300
        
        # Simulate lock expiration check
        check_time = current_time + 400  # After expiration
        assert check_time > lock.expires_at  # Lock should be expired

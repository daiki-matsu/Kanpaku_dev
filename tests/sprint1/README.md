# Sprint 1 Test Suite

## Overview
Sprint 1 MVP implementation test suite for the Kanpaku project.

## Test Coverage

### 1. SafeIO Tests (`test_safe_io.py`)
- **SafeIO class unit tests**
- Path validation and security boundary testing
- File read/write operations
- Unicode content handling
- Nested directory creation
- Error handling for unauthorized access

### 2. Model Tests (`test_models.py`)
- **Task model testing**
  - Task creation and validation
  - TaskStatus enum verification
  - Complete data structure testing
- **Agent model testing**
  - Agent creation and state management
  - AgentStatus enum verification
- **Event model testing**
  - Event creation and timestamp handling
- **SystemState model testing**
  - State tracking and metrics
- **FileLock model testing**
  - Lock creation and TTL management

### 3. Integration Tests (`test_integration.py`)
- **Complete task workflow testing**
  - Task creation to completion lifecycle
  - Agent state transitions
  - SafeIO integration
- **Security boundary testing**
  - Path traversal attack prevention
  - Unauthorized access blocking
- **Event stream simulation**
  - Task lifecycle event sequence
- **System state tracking**
  - Real-time metrics updates

## Sprint 1 MVP Features Tested

According to the MVP plan, the following features are tested:

### Redis Data Structures (Simulated)
- [x] Tasks (assigned, doing, completed states)
- [x] Agents (idle, thinking states)
- [x] Event stream simulation
- [x] Lock mechanism

### File Operations
- [x] Safe file reading
- [x] Safe file writing
- [x] Path restriction (/project directory)
- [x] Security boundary enforcement

### Agent Operations
- [x] Toneri-1 (agent) file operations
- [x] Executor layer functionality
- [x] State transitions

## Running Tests

### Prerequisites
```bash
pip install pytest
pip install pydantic
```

### Run All Tests
```bash
pytest tests/sprint1/ -v
```

### Run Specific Test Files
```bash
# SafeIO tests only
pytest tests/sprint1/test_safe_io.py -v

# Model tests only
pytest tests/sprint1/test_models.py -v

# Integration tests only
pytest tests/sprint1/test_integration.py -v
```

### Run with Coverage
```bash
pytest tests/sprint1/ --cov=src --cov-report=html
```

## Test Structure

```
tests/sprint1/
|-- __init__.py          # Test module initialization
|-- conftest.py          # Pytest fixtures and configuration
|-- test_safe_io.py      # SafeIO class unit tests
|-- test_models.py       # Model class unit tests
|-- test_integration.py  # Integration tests
|-- README.md           # This documentation
```

## Key Test Scenarios

### Security Testing
- Path traversal prevention (`../etc/passwd`)
- Absolute path blocking (`/etc/passwd`)
- Directory traversal attacks
- Unauthorized access attempts

### Workflow Testing
- Complete task lifecycle
- Agent state management
- File operation integration
- Event stream generation

### Data Validation
- Model creation with various data combinations
- Enum value validation
- Default value verification
- Required field validation

## Notes
- Tests use temporary directories for file operations
- No actual Redis connection required (simulated)
- All tests are self-contained and isolated
- Unicode and special character handling tested
- Error conditions and edge cases covered

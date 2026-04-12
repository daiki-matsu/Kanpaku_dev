---
codd:
  node_id: plan:implementation-plan
  type: plan
  depends_on:
  - id: design:detailed-skill-evolution
    relation: depends_on
    semantic: technical
  - id: design:task-lifecycle-flow
    relation: depends_on
    semantic: technical
  - id: design:history-persistence-schema
    relation: depends_on
    semantic: technical
  depended_by: []
  conventions:
  - id: module:executor
    description: File execution module for sandbox operations
    targets: []
    reason: ''
  - id: module:jiju
    description: Orchestrator module for task decomposition and management
    targets: []
    reason: ''
  - id: module:kanpaku
    description: Primary interface module for user interaction
    targets: []
    reason: ''
  - id: module:monitor
    description: Monitoring module for timeout and heartbeat enforcement
    targets: []
    reason: ''
  - id: module:task_manager
    description: Task lifecycle management module
    targets: []
    reason: ''
  - id: module:persistence
    description: YAML persistence module for historical records
    targets: []
    reason: ''
  - id: infra:llm-stack
    description: LLM inference stack configuration
    targets: []
    reason: ''
  - id: infra:deployment
    description: Model deployment and resource allocation
    targets: []
    reason: ''
  - id: agent:hierarchy
    description: Agent hierarchy enforcement (Kanpaku-Jiju-Toneri-Onmyoji)
    targets: []
    reason: ''
  - id: agent:heartbeat
    description: Agent heartbeat monitoring (30s intervals)
    targets: []
    reason: ''
  - id: agent:timeout-policy
    description: Timeout policy enforcement (300s thinking, 120s doing)
    targets: []
    reason: ''
  - id: db:redis
    description: Redis state management and distributed locking
    targets: []
    reason: ''
  - id: db:chroma
    description: Vector database for skill storage and retrieval
    targets: []
    reason: ''
  - id: redis:file-lock
    description: Redis-based file locking mechanism
    targets: []
    reason: ''
  - id: state:persistence
    description: State persistence to YAML files for auditability
    targets: []
    reason: ''
  - id: skill:retrieval-logic
    description: Skill retrieval logic based on success rate and similarity
    targets: []
    reason: ''
  - id: ops:failure-visibility
    description: Failed task visibility on dashboard
    targets: []
    reason: ''
  - id: review:score-threshold
    description: Review score threshold (>=80 for task completion)
    targets: []
    reason: ''
  modules:
  - orchestrator
  - storage
  - sandbox
  - skill_manager
  - state
---

# Kanpaku System Implementation Plan

## Overview

The Kanpaku system is a high-concurrency agent orchestration framework that integrates real-time state management in Redis, persistent YAML-based audit trails, and an evolutionary skill acquisition mechanism powered by ChromaDB. The architecture is optimized for deployment on an NVIDIA RTX 2070 SUPER (8GB VRAM), requiring strict resource management for LLM inference and vector embeddings.

## System Architecture

### Core Components

1. **Redis**: Primary datastore for task states and execution logs
2. **Executors (Toneri, Onmyoji)**: Task execution components
3. **Orchestrator (Jiju)**: Task flow management and data integrity verification
4. **ChromaDB**: Vector database for skill storage and retrieval
5. **File System**: `/history/` directory for YAML task records

### Agent Hierarchy

- **Kanpaku**: Primary user interface
- **Jiju**: Orchestrator for task decomposition and management
- **Toneri**: L1-L3 task executor
- **Onmyoji**: L4-L6 task executor

## Sprint-Based Implementation Roadmap

### Sprint 1: Core Infrastructure Setup (5 days)

**Objective**: Establish foundational architecture and basic state management

#### Tasks
- **Task 1.1**: Redis schema deployment
  - Initialize `tasks:{task_id}` hash structure
  - Create agent inbox lists (`inbox:toneri`, `inbox:onmyoji`)
  - Implement distributed locking with `SET NX EX 300`
  - *Dependencies: db:redis*

- **Task 1.2**: Agent base class architecture
  - Create base class for all agent types with consistent logging methods
  - Define abstract methods for task lifecycle management
  - Implement heartbeat mechanism (30s intervals)
  - *Dependencies: agent:heartbeat, module:executor*

- **Task 1.3**: Directory structure and basic utilities
  - Define `/history/tasks/` directory structure
  - Create utility functions for structured `LogEntry` formatting
  - Implement basic YAML serialization framework
  - *Dependencies: module:persistence*

#### Acceptance Criteria
- Redis connection and basic operations functional
- Agent base class instantiated with heartbeat monitoring
- Directory structure created and basic file operations working

### Sprint 2: State Machine and Task Routing (7 days)

**Objective**: Implement core task execution flow and agent routing logic

#### Tasks
- **Task 2.1**: Bloom taxonomy routing implementation
  - Configure Jiju to route L1-L3 tasks to Toneri
  - Configure Jiju to route L4-L6 tasks to Onmyoji
  - Implement task complexity assessment logic
  - *Dependencies: agent:hierarchy, module:jiju*

- **Task 2.2**: Temporal monitoring service
  - Implement `module:monitor` for timeout enforcement
  - Configure automatic task resets:
    - "Thinking" timeout: >300s
    - "Doing" timeout: >120s
  - Setup timeout policy enforcement
  - *Dependencies: agent:timeout-policy, module:monitor*

- **Task 2.3**: Retry and terminal logic
  - Implement retry counter in `module:task_manager`
  - Enforce 10-attempt ceiling for terminal state
  - Configure exponential backoff: `delay = base_delay * (2^retry_count)`
  - Set maximum delay ceiling at 300s
  - *Dependencies: module:task_manager*

#### Acceptance Criteria
- Tasks correctly routed based on complexity
- Timeout monitoring and automatic resets functional
- Retry logic with exponential backoff operational

### Sprint 3: Persistence Layer and Data Integrity (8 days)

**Objective**: Ensure all agent actions are auditable and recoverable

#### Tasks
- **Task 3.1**: YAML serialization engine
  - Complete `module:persistence` utility development
  - Generate `/history/tasks/T{task_id}.yaml` files with proper schema
  - Implement structured log formatting with sanitization
  - *Dependencies: state:persistence, module:persistence*

- **Task 3.2**: Atomic history locking
  - Implement `lock:history:{task_id}` mechanism
  - Prevent race conditions during YAML writes
  - Ensure atomic file operations with proper error handling
  - *Dependencies: redis:file-lock*

- **Task 3.3**: Integrity verification system
  - Build Jiju drift detection hook
  - Compare Redis `updated_at` with YAML `completed_at`
  - Enforce 1000ms tolerance threshold
  - Halt pipeline on synchronization failure
  - *Dependencies: module:jiju, db:redis*

#### Acceptance Criteria
- YAML files created with proper structure and sanitization
- Concurrent access controlled with Redis locks
- Drift detection operational with automatic pipeline halt on failure

### Sprint 4: Performance Optimization and Security (9 days)

**Objective**: Optimize performance and implement security measures

#### Tasks
- **Task 4.1**: Performance optimization
  - Optimize YAML serialization to meet <200ms target
  - Implement log truncation at 50,000 characters
  - Add sub-directory partitioning planning for >10,000 files
  - *Dependencies: module:persistence*

- **Task 4.2**: Security and sanitization
  - Implement log cleaner for sensitive data
  - Redact environment variables and credentials
  - Sanitize `tool_call` entries before persistence
  - *Dependencies: module:persistence*

- **Task 4.3**: LLM stack integration
  - Configure LLM inference stack for RTX 2070 SUPER
  - Implement shared embedding RPC service
  - Setup model deployment and resource allocation
  - *Dependencies: infra:llm-stack, infra:deployment*

#### Acceptance Criteria
- Performance targets met (<200ms serialization/write)
- All sensitive data properly sanitized
- LLM stack operational within VRAM constraints

### Sprint 5: Skill Evolution and VectorDB Integration (7 days)

**Objective**: Enable system learning from successful task outcomes

#### Tasks
- **Task 5.1**: Vector database setup
  - Initialize ChromaDB with `sentence-transformers/all-MiniLM-L6-v2`
  - Apply quantization for RTX 2070 SUPER VRAM limits
  - Implement vector storage and retrieval operations
  - *Dependencies: db:chroma, infra:deployment*

- **Task 5.2**: Skill registration pipeline
  - Implement Jiju gatekeeper logic
  - Filter tasks for promotion: `(score >= 80) AND (status == COMPLETED)`
  - Configure review score threshold enforcement
  - *Dependencies: skill:retrieval-logic, review:score-threshold*

- **Task 5.3**: Weighted retrieval logic
  - Develop ranking algorithm: `FinalScore = (0.7 * CosineSimilarity) + (0.3 * SuccessRate)`
  - Implement Top-3 skill injection system
  - Enforce 1,000-token truncation for code snippets
  - *Dependencies: skill:retrieval-logic*

#### Acceptance Criteria
- ChromaDB operational with quantized models
- Skill promotion pipeline functional with proper filtering
- Skill retrieval and injection working with weighted scoring

### Sprint 6: Testing and Dashboard Integration (6 days)

**Objective**: Comprehensive testing and operational visibility

#### Tasks
- **Task 6.1**: Comprehensive testing
  - Unit tests for all utility functions and modules
  - Integration tests with simulated agent environments
  - Load testing for concurrent operations
  - Performance validation under stress

- **Task 6.2**: Dashboard and monitoring
  - Implement failed task visibility on dashboard
  - Add system health monitoring
  - Create operational metrics and alerts
  - *Dependencies: ops:failure-visibility*

- **Task 6.3**: Documentation and deployment
  - Complete technical documentation
  - Create deployment guides
  - Final system integration and validation

#### Acceptance Criteria
- All tests passing with >95% coverage
- Dashboard operational with real-time metrics
- Production-ready deployment package

## Risk Management

| Risk Category | Description | Mitigation Strategy | Sprint Focus |
|:---|:---|:---|:---|
| **VRAM Contention** | RTX 2070 SUPER (8GB) OOM risk | Shared embedding RPC service; resident model manager | Sprint 4 |
| **System Drift** | Redis-YAML synchronization issues | Jiju drift detection (1000ms threshold); pipeline halt on failure | Sprint 3 |
| **Recursive Failure** | Infinite retry loops | 10-retry ceiling; escalation to Onmyoji for evaluation | Sprint 2 |
| **Skill Regression** | Low-quality pattern retrieval | 0.7/0.3 similarity-to-success ratio; 80+ score threshold | Sprint 5 |
| **Filesystem Bloat** | Directory performance degradation | Log truncation; sub-directory partitioning plan | Sprint 4 |

## Technical Specifications

### Performance Targets
- YAML serialization/write: <200ms
- Redis operations: <50ms
- Vector embedding generation: <500ms
- Concurrent task processing: 100+ tasks

### Resource Constraints
- VRAM usage: <7.5GB (RTX 2070 SUPER)
- Memory usage: <16GB system RAM
- Disk I/O: <100MB/s for persistence operations

### Quality Gates
- Unit test coverage: >95%
- Integration test success rate: 100%
- Performance benchmarks: All targets met
- Security scan: No critical vulnerabilities

## Module Dependencies

### Core Modules
- **module:executor**: File execution for sandbox operations (Sprint 1)
- **module:jiju**: Orchestrator for task decomposition and management (Sprint 2)
- **module:kanpaku**: Primary user interface (Sprint 1)
- **module:monitor**: Timeout and heartbeat enforcement (Sprint 2)
- **module:task_manager**: Task lifecycle management (Sprint 2)
- **module:persistence**: YAML persistence for historical records (Sprint 3)

### Infrastructure Components
- **infra:llm-stack**: LLM inference configuration (Sprint 4)
- **infra:deployment**: Model deployment and resource allocation (Sprint 4)
- **db:redis**: Redis state management and locking (Sprint 1)
- **db:chroma**: Vector database for skills (Sprint 5)

### Operational Policies
- **agent:hierarchy**: Agent hierarchy enforcement (Sprint 2)
- **agent:heartbeat**: 30s interval monitoring (Sprint 1)
- **agent:timeout-policy**: 300s thinking, 120s doing timeouts (Sprint 2)
- **redis:file-lock**: File locking mechanism (Sprint 3)
- **state:persistence**: State auditability (Sprint 3)
- **skill:retrieval-logic**: Success-based skill retrieval (Sprint 5)
- **ops:failure-visibility**: Failed task dashboard visibility (Sprint 6)
- **review:score-threshold**: >=80 completion threshold (Sprint 5)

## Open Questions and Future Considerations

1. **Log Rotation**: Volume thresholds for `/history/tasks/` archiving (Post-Sprint 6)
2. **Partial Persistence**: Incremental writes for long-running tasks (Post-Sprint 6)
3. **Schema Versioning**: YAML schema evolution management (Post-Sprint 6)
4. **Verification Metadata**: Cryptographic hashes for sandbox state (Post-Sprint 6)
5. **Model Swapping**: Dynamic model management for VRAM optimization (Post-Sprint 6)

This sprint-based implementation plan provides a structured approach to building the Kanpaku system with clear milestones, dependencies, and acceptance criteria while maintaining the technical depth and comprehensive coverage of the original specification.

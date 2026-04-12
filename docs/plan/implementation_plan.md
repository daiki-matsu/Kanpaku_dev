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

#### Sprint 1（5 days）: Core Infrastructure Setup

**Objective**: Establish foundational architecture and basic state management

| タスクID | タスク名 | モジュールヒント | 成果物 |
|----------|----------|------------------|--------|
| 1-1 | Redis schema deployment | module:executor | Initialize `tasks:{task_id}` hash structure, Create agent inbox lists, Implement distributed locking |
| 1-2 | Agent base class architecture | module:executor | Create base class for all agents, Define abstract methods, Implement heartbeat mechanism |
| 1-3 | Directory structure and basic utilities | module:persistence | Define `/history/tasks/` structure, Create utility functions, Implement YAML serialization |

#### Acceptance Criteria
- Redis connection and basic operations functional
- Agent base class instantiated with heartbeat monitoring
- Directory structure created and basic file operations working

#### Sprint 2（7 days）: State Machine and Task Routing

**Objective**: Implement core task execution flow and agent routing logic

| タスクID | タスク名 | モジュールヒント | 成果物 |
|----------|----------|------------------|--------|
| 2-1 | Bloom taxonomy routing implementation | module:jiju | Configure Jiju routing for L1-L3/L4-L6 tasks, Implement task complexity assessment |
| 2-2 | Temporal monitoring service | module:monitor | Implement timeout enforcement, Configure automatic resets, Setup timeout policy |
| 2-3 | Retry and terminal logic | module:task_manager | Implement retry counter, Enforce 10-attempt ceiling, Configure exponential backoff |

#### Acceptance Criteria
- Tasks correctly routed based on complexity
- Timeout monitoring and automatic resets functional
- Retry logic with exponential backoff operational

#### Sprint 3（8 days）: Persistence Layer and Data Integrity

**Objective**: Ensure all agent actions are auditable and recoverable

| タスクID | タスク名 | モジュールヒント | 成果物 |
|----------|----------|------------------|--------|
| 3-1 | YAML serialization engine | module:persistence | Complete utility development, Generate YAML files with schema, Implement structured log formatting |
| 3-2 | Atomic history locking | module:persistence | Implement locking mechanism, Prevent race conditions, Ensure atomic file operations |
| 3-3 | Integrity verification system | module:jiju | Build drift detection hook, Compare timestamps, Enforce tolerance threshold |

#### Acceptance Criteria
- YAML files created with proper structure and sanitization
- Concurrent access controlled with Redis locks
- Drift detection operational with automatic pipeline halt on failure

#### Sprint 4（9 days）: Performance Optimization and Security

**Objective**: Optimize performance and implement security measures

| タスクID | タスク名 | モジュールヒント | 成果物 |
|----------|----------|------------------|--------|
| 4-1 | Performance optimization | module:persistence | Optimize YAML serialization, Implement log truncation, Add sub-directory partitioning |
| 4-2 | Security and sanitization | module:persistence | Implement log cleaner, Redact credentials, Sanitize tool_call entries |
| 4-3 | LLM stack integration | infra:llm-stack | Configure inference stack, Implement shared embedding RPC, Setup model deployment |

#### Acceptance Criteria
- Performance targets met (<200ms serialization/write)
- All sensitive data properly sanitized
- LLM stack operational within VRAM constraints

#### Sprint 5（7 days）: Skill Evolution and VectorDB Integration

**Objective**: Enable system learning from successful task outcomes

| タスクID | タスク名 | モジュールヒント | 成果物 |
|----------|----------|------------------|--------|
| 5-1 | Vector database setup | db:chroma | Initialize ChromaDB with transformers, Apply quantization for VRAM limits, Implement vector operations |
| 5-2 | Skill registration pipeline | module:jiju | Implement gatekeeper logic, Filter tasks for promotion, Configure score threshold |
| 5-3 | Weighted retrieval logic | module:jiju | Develop ranking algorithm, Implement Top-3 skill injection, Enforce token truncation |

#### Acceptance Criteria
- ChromaDB operational with quantized models
- Skill promotion pipeline functional with proper filtering
- Skill retrieval and injection working with weighted scoring

#### Sprint 6（6 days）: Testing and Dashboard Integration

**Objective**: Comprehensive testing and operational visibility

| タスクID | タスク名 | モジュールヒント | 成果物 |
|----------|----------|------------------|--------|
| 6-1 | Comprehensive testing | module:executor | Unit tests for utilities, Integration tests with agents, Load testing for concurrency |
| 6-2 | Dashboard and monitoring | module:monitor | Failed task visibility, System health monitoring, Operational metrics |
| 6-3 | Documentation and deployment | module:kanpaku | Technical documentation, Deployment guides, System integration |

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

---
codd:
  node_id: design:security-sandbox
  type: design
  depends_on:
  - id: test:acceptance-criteria
    relation: constrained_by
    semantic: governance
  depended_by:
  - id: design:state-management-redis
    relation: depends_on
    semantic: technical
  conventions:
  - targets:
    - module:executor
    reason: File operations MUST be restricted to the specific project folder (e.g.,
      /project/).
  modules:
  - sandbox
  - executor
---

# Security and Sandbox Design

## 1. Overview
The Security and Sandbox Design for Kanpaku establishes the defensive perimeter and operational constraints necessary to ensure agent-led task execution does not compromise the host system or cross-project boundaries. This design focuses on strict isolation of the `module:executor` (Toneri and Onmyoji agents) and defines the enforcement mechanisms for the system's reliability policies. 

This document complies with the `module:executor` convention requiring all file operations to be restricted to the specific project folder (e.g., `/project/`). By implementing path-level sandboxing, resource-based timeouts, and cryptographic integrity for state transitions, Kanpaku mitigates risks associated with autonomous code execution and state-driven orchestration.

## 2. Architecture

### 2.1 File System Sandbox (module:executor)
The primary security invariant for Kanpaku is the isolation of the `module:executor`. All file operations (read, write, delete, append) performed by agents are governed by a strict path-validation middleware.
- **Root Constraint:** The application enforces a hard root at `/project/`. 
- **Validation Logic:** Before any `fs` module call is executed, the requested path is normalized using `path.resolve()`. The system explicitly checks that the resolved absolute path starts with the designated `/project/` string. 
- **Implementation Pattern:** The sandbox uses a `safe_write` function pattern: `if not path.startswith("/project/"): raise Exception("Forbidden")` to enforce path restrictions at the application layer. 
- **Forbidden Operations:** Any attempt to utilize parent directory traversal (`../`) or absolute paths outside the scope triggers a `Sandbox Breach` event, immediately transitioning the task to `TASK_FAILED` and logging a "Forbidden" exception to `/logs/state.log`.
- **Concurrency Control:** To prevent race conditions during multi-agent execution, Redis-based distributed locks are implemented via keys formatted as `lock:{filepath}`. An agent must acquire this lock before modifying any file within `/project/`. Locks use the format `SET lock:{filepath} {by: agent_id} EX 300 NX` and can be extended with `EXPIRE lock:{filepath} 300` for long-running operations.

### 2.2 Agent Timeout and Reliability Policy
To prevent resource exhaustion and ensure the "Imperial Court" remains responsive, the system enforces strict temporal sandboxes as defined in the `agent:timeout-policy`.
- **Thinking Timeout (300s):** LLM inference processes (e.g., `gemma4-26B-A4B` or `Bonsai-8B`) are monitored by a watchdog timer. If an agent remains in `thinking` status for more than 300 seconds, the Orchestrator emits a `TASK_STALLED` event and terminates the inference request.
- **Doing Timeout (120s):** I/O operations and file manipulations in the sandbox are limited to 120 seconds. If `module:executor` exceeds this limit, the process is killed to prevent hanging file handles.
- **Heartbeat Monitoring:** Active agents must update their `last_heartbeat` field in Redis every 30 seconds. Failure to update within 60 seconds results in the agent being flagged as `zombie` and its tasks being returned to the `assigned` pool.

### 2.3 Task Integrity and Quality Gates
Security in Kanpaku extends to the logical integrity of the workflow, ensuring that only verified results propagate through the system.
- **Review Threshold:** Compliance with `review:score-threshold` is non-negotiable. A task transition to `completed` is blocked unless the Onmyoji (Analyzer) or Jiju (Manager) provides a `review.score` >= 80.
- **Retry Sandbox:** Failed tasks are restricted to a maximum of 10 retry attempts (`retry.count <= 10`). Upon the 11th failure, the task is quarantined, preventing the agent from entering an infinite loop of resource consumption.
- **Persistence:** Real-time state is stored in Redis hashes (`tasks:{id}`), while the source of truth for historical auditing is persisted in `/history/tasks/T{id}.yaml`. The system performs a checksum verification between Redis and YAML during the `ANALYZE_CREATING` phase to detect state drifting.

### 2.4 Skill and VectorDB Security
The "Skill" evolution mechanism utilizes Chroma VectorDB to store and retrieve execution patterns.
- **Metadata Sanitization:** Before storage, skill patterns extracted by Onmyoji are stripped of environment-specific credentials or sensitive strings.
- **Injection Prevention:** Retreived skills are injected into the agent prompt as context. The prompt template uses strict delimiters to prevent the agent from interpreting skill metadata as direct imperial commands (Mikado instructions).

## 3. Open Questions

1. **Network Egress Isolation:** Should the `module:executor` be restricted from all external network calls via `iptables` or a dedicated Docker network driver, or are specific whitelisted API endpoints (e.g., LLM providers) permitted?
2. **GPU Resource Quotas:** How will the system enforce multi-tenant GPU memory isolation if multiple `Toneri` agents attempt to run inference on the same physical hardware simultaneously?
3. **Sandbox Recovery:** In the event of a `TASK_STALLED` or `Sandbox Breach`, what is the automated procedure for cleaning up orphaned temporary files or Redis locks without manual intervention?

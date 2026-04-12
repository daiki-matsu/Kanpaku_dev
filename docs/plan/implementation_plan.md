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
  conventions: []
  modules:
  - orchestrator
  - storage
  - sandbox
  - skill_manager
  - state
---

# Implementation Roadmap

## 1. Overview
The Implementation Roadmap for the Kanpaku system details the phased construction of a high-concurrency agent orchestration framework. This system integrates real-time state management in Redis, a persistent YAML-based audit trail, and an evolutionary skill acquisition mechanism powered by ChromaDB. The architecture is specifically optimized for deployment on an NVIDIA RTX 2070 SUPER (8GB VRAM), necessitating strict resource management for LLM inference and vector embeddings.

The roadmap focuses on three core pillars:
1.  **State & Lifecycle Control:** Implementing the deterministic task state machine with strict temporal constraints (300s thinking/120s doing timeouts) and Bloom-level routing.
2.  **Audit & Persistence:** Establishing a reliable synchronization layer between the volatile Redis state and the immutable `/history/tasks/` storage, including drift detection.
3.  **Skill Evolution:** Deploying a vector-based "memory" that promotes successful task outcomes (Review Score >= 80) into reusable skills to improve execution efficiency.

## 2. Milestones

### Milestone 1: Core State Machine and Agent Routing
The objective of this milestone is to establish the "hot" execution layer using Redis and the orchestrator (Jiju).
*   **Redis Schema Deployment:** Initialize the `tasks:{task_id}` hash and agent inbox lists (`inbox:toneri`, `inbox:onmyoji`).
*   **Bloom Taxonomy Routing:** Configure Jiju to route L1-L3 tasks to Toneri and L4-L6 tasks to Onmyoji.
*   **Temporal Monitor Service:** Implement the `module:monitor` to enforce the 30-second heartbeat interval. Configure automatic task resets for "Thinking" (>300s) and "Doing" (>120s) timeouts.
*   **Retry & Terminal Logic:** Implement the terminal retry counter logic in `module:task_manager`, ensuring tasks reaching 10 attempts are moved to the `FAILED` state and removed from active loops.
*   **Exponential Backoff:** Implement retry delay algorithm `delay = base_delay * (2^retry_count)` with 300s maximum ceiling to prevent resource exhaustion during failure cascades.
*   **Locking Mechanism:** Deploy the Redis distributed locking pattern using `SET NX EX 300` for file-system access in `/project/`, including the Lua script for safe atomic releases.

### Milestone 2: Persistence Layer and Drift Detection
This milestone ensures that every action taken by agents is auditable and recoverable.
*   **YAML Serialization Engine:** Develop the `module:persistence` utility to generate `/history/tasks/T{task_id}.yaml` according to the defined schema (logs, metadata, review scores).
*   **Atomic History Locking:** Implement `lock:history:{task_id}` to prevent race conditions during YAML writes when multiple agents or the orchestrator interact with a task record.
*   **Integrity Verification:** Build the Jiju "Drift Detection" hook that compares the Redis `updated_at` field with the YAML `completed_at` timestamp (1000ms tolerance) before finalization.
*   **Sanitization Pipeline:** Implement the log cleaner to redact environment variables and credentials from `tool_call` entries before disk persistence.

### Milestone 3: Skill Evolution and VectorDB Integration
The final milestone enables the system to learn from its successes using ChromaDB.
*   **Vector Database Setup:** Initialize ChromaDB with the `sentence-transformers/all-MiniLM-L6-v2` model. Apply quantization to keep the model footprint within the RTX 2070 SUPER VRAM limits.
*   **Skill Registration Pipeline:** Implement the Jiju gatekeeper logic to filter tasks for promotion based on the `(score >= 80) AND (status == COMPLETED)` criteria.
*   **Weighted Retrieval Logic:** Develop the ranking algorithm for agent pre-execution hooks: `FinalScore = (0.7 * CosineSimilarity) + (0.3 * SuccessRate)`.
*   **Context Injection:** Implement the Top-3 skill injection system, including a 1,000-token truncation rule for code snippets to maintain manageable context windows for agents.

## 3. Risks

| Risk Category | Description | Mitigation Strategy |
|:---|:---|:---|
| **VRAM Contention** | The RTX 2070 SUPER (8GB) may experience OOM when running the LLM, the quantized embedding model, and ChromaDB simultaneously. | Implement a shared embedding RPC service to prevent model duplication; use a resident manager to swap models if VRAM exceeds 7.5GB. |
| **System Drift** | Discrepancies between the Redis "hot" state and the YAML "cold" storage could lead to skill corruption or lost audit logs. | Enforce the Jiju drift detection check (1000ms threshold) and halt the task pipeline if synchronization fails. |
| **Recursive Failure** | Complex tasks may trigger an infinite loop of retries if the root cause is architectural rather than execution-based. | Strictly enforce the 10-retry ceiling and escalate `FAILED` tasks to the Onmyoji (L4-L6) for evaluation rather than further execution attempts. |
| **Skill Regression** | High-similarity but low-quality code patterns could be retrieved if success rates are not properly weighted. | Maintain the 0.7/0.3 similarity-to-success ratio in `skill:retrieval-logic` and enforce the 80+ review score threshold for all new skills. |
| **Filesystem Bloat** | High task volume may degrade directory listing performance in `/history/tasks/`. | Implement a truncation rule for logs at 50,000 characters and plan for sub-directory partitioning (e.g., `/history/tasks/01/`) after 10,000 files. |

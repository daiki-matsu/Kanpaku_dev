---
codd:
  node_id: test:acceptance-criteria
  type: test
  depends_on:
  - id: req:kanpaku-requirements
    relation: derives_from
    semantic: governance
  depended_by:
  - id: design:system-design
    relation: constrained_by
    semantic: technical
  - id: design:security-sandbox
    relation: constrained_by
    semantic: governance
  conventions:
  - targets:
    - agent:timeout-policy
    reason: Thinking(300s) and Doing(120s) timeouts are release-blocking for agent
      reliability.
  - targets:
    - review:score-threshold
    reason: Review score >= 80 is required for TASK_COMPLETED status.
  modules:
  - orchestrator
  - agent_jiju
---

# Kanpaku Acceptance Criteria

## 1. Overview
Kanpaku is a hierarchical multi-agent orchestration system designed for autonomous task execution and project management using Consistency-Driven Development (CoDD) principles. The system mirrors the Heian-era imperial court structure, where roles are strictly divided among the Mikado (User), Kanpaku (Goal Setting), Jiju (Task Decomposition/Monitoring), Toneri (Execution L1-L3), and Onmyoji (Analysis L4-L6). The system leverages Redis for real-time state management, YAML for persistent history, and a self-evolving "Skill" mechanism using Chroma VectorDB. This document defines the verifiable requirements for system stability, agent reliability, security sandboxing, and quality thresholds.

## 2. Acceptance Criteria

### 2.1 Agent Hierarchy and Role Responsibility
- **Mikado (User):** Must be able to input high-level instructions via the interface.
- **Kanpaku (Goal Setter):** Must process user input to generate formal instructions (`ORDER_CREATED`) and determine if new skills are needed using `gemma4-26B-A4B`.
- **Jiju (Manager):** Must decompose instructions into specific tasks (`TASK_CREATED`), assign agents, monitor heartbeats, and update the dashboard using `gemma4-E2B`.
- **Toneri (Executor):** Must execute Bloom Level L1-L3 tasks (Remember, Understand, Apply) including file operations using `Bonsai-8B` or `DeepSeek 6.7B`.
- **Onmyoji (Analyzer):** Must execute Bloom Level L4-L6 tasks (Analyze, Evaluate, Create) focusing on structural analysis and skill pattern extraction using `gemma4-26B-A4B`.

### 2.2 Task Lifecycle and State Transitions
- **Workflow State Machine:** Tasks must transition through: `created` -> `assigned` -> `doing` -> `reviewing` -> `completed` or `failed`.
- **Review Threshold:** A task status changes to `completed` only if the `review.score` is >= 80 (Ref: `review:score-threshold`).
- **Review Failure:** If `review.score` < 80, the task must return to `assigned` status with a `retry.count` increment.
- **Retry Limit:** A task must transition to `failed` status and be removed from the processing loop after the 10th failed attempt.

### 2.3 Operational Constraints and Performance
- **Thinking Timeout:** Any agent in `thinking` status (LLM inference) must trigger a `TASK_STALLED` event if it exceeds 300 seconds (Ref: `agent:timeout-policy`).
- **Doing Timeout:** Any agent in `working` status (I/O, file operations) must trigger a `TASK_STALLED` event if it exceeds 120 seconds (Ref: `agent:timeout-policy`).
- **Heartbeat:** The system must update `last_heartbeat` every 30 seconds for active agents.
- **File Sandbox:** All file write/delete operations must be restricted to the `/project/` directory. Attempts to access paths outside this scope must throw a "Forbidden" exception.
- **Concurrency Control:** Redis locks (`lock:{filepath}`) must prevent multiple agents from writing to the same file simultaneously.

### 2.4 Skill Evolution (Self-Improvement)
- **Pattern Extraction:** Upon a successful task (Score >= 80), the system must trigger `ANALYZE_CREATING` to extract patterns.
- **VectorDB Storage:** New skills must be embedded and stored in Chroma DB with metadata (success_rate, bloom_level).
- **Skill Retrieval:** For new tasks, the top 3 similar successful skills must be injected into the agent's prompt to improve execution accuracy.

### 2.5 Persistence and Logging
- **Redis State:** Current status of tasks and agents must be queryable via Redis hashes (`tasks:{id}`, `agents:{id}`).
- **YAML History:** Every task completion or state change must be persisted to `/history/tasks/T{id}.yaml` and `/logs/state.log`.

## 3. Failure Criteria
- **Threshold Violations:** Any review resulting in `TASK_COMPLETED` with a score < 80.
- **Timeout Violations:** Agents remaining in `thinking` for > 300s or `doing` for > 120s without a stall event being recorded.
- **Sandbox Breach:** Any successful file operation (write/delete) performed outside the designated `/project/` folder.
- **Inconsistency:** Discrepancy between Redis `status` and the YAML persistent history.
- **UI Failures:** Dashboard failing to reflect `TASK_FAILED` status in high-visibility (red) formatting.
- **Server Health:** Any HTTP response returning a 5xx status code (Internal Server Error) during API interactions.
- **Authentication/Routing:** Browser tests failing to redirect to the post-login dashboard or rendering a 404/blank page after a successful login flow.

## 4. E2E Test Generation Meta-Prompt

### 4.1 Domain Decomposition and Mapping
Generate Playwright E2E tests split into the following domains. Each domain must have an API integration test (`.spec.ts`) and a Browser test (`.browser.spec.ts`).

| Domain | Description | API Test File | Browser Test File |
| :--- | :--- | :--- | :--- |
| **Auth/RBAC** | Login flow, redirect logic, and role-based access. | `tests/e2e/auth.spec.ts` | `tests/e2e/auth.browser.spec.ts` |
| **Workflow** | Task creation, assignment, and status transitions. | `tests/e2e/workflow.spec.ts` | `tests/e2e/workflow.browser.spec.ts` |
| **Sandbox** | Security constraints on file operations and paths. | `tests/e2e/sandbox.spec.ts` | N/A |
| **Reliability** | Timeout handling (300s/120s) and retry logic. | `tests/e2e/reliability.spec.ts` | `tests/e2e/reliability.browser.spec.ts` |
| **Skills** | VectorDB storage and skill retrieval cycles. | `tests/e2e/skills.spec.ts` | N/A |

### 4.2 Test Level Requirements
- **API Integration Tests:** Verify status codes, JSON schema, and Redis state. Every request must first assert `response.status() < 500`.
- **Browser Tests:** 
    - **Login Flow:** Navigate to `/login`, submit credentials, assert redirect to `/dashboard`, and verify the "Kanpaku" title is visible.
    - **Transition Assertions:** Every page transition must verify both the new URL and the presence of a specific UI element (e.g., Task List Table).
- **Environment Setup:** 
    - Detect project type (Node.js). 
    - Startup: `npm run build && npm run start`.
    - CI: Run server in background and use `wait-on http://localhost:3000`.
- **Shared Helpers:** All tests must use `tests/e2e/helpers/` for authentication tokens, Redis flushing, and test data injection.

### 4.3 Generation Rules
- **Headers:** All files must start with:
  `// @generated-from: test:acceptance-criteria`
  `// @generated-by: codd propagate`
- **Maintenance:** Preserve any block marked with `// @manual`.
- **Unimplemented Routes:** Scan the current router config; if an endpoint is defined but not implemented, use `test.fixme()` with a note.
- **Quality Gate:** Release-blocking criteria:
    1. 100% of Acceptance Criteria covered.
    2. Zero `SKIP` or `FAIL` in the CI pipeline.
    3. `agent:timeout-policy` (300s thinking/120s doing) explicitly asserted.
    4. `review:score-threshold` (>=80) explicitly asserted in workflow tests.

---
codd:
  node_id: ops:monitoring-guide
  type: operations
  depends_on:
  - id: detailed_design:task-lifecycle-flow
    relation: depends_on
    semantic: technical
  depended_by: []
  conventions:
  - targets:
    - ops:failure-visibility
    reason: Tasks reaching 10 retries must be visually highlighted (failed status)
      on the dashboard.
  modules:
  - interface
  - orchestrator
  - monitor
---

# Dashboard and Monitoring Guide

## 1. Overview
The Dashboard and Monitoring Guide for the Kanpaku system provides the operational framework for maintaining visibility into the distributed agent lifecycle. This document centralizes the monitoring requirements for the **module:jiju** orchestrator, **Toneri** execution agents, and **Onmyoji** analysis agents. The core objective is to ensure that the deterministic flow of tasks—governed by Redis state management and Bloom’s Taxonomy routing—remains within the defined temporal and reliability constraints.

Key operational metrics include the enforcement of the 300-second thinking timeout, the 120-second doing timeout, and the 30-second heartbeat interval. Most critically, this guide defines the visualization and alerting rules for the terminal failure state: any task reaching a retry count of 10 must be immediately flagged, removed from the active loop, and archived to `/history/tasks/` for forensic analysis. This compliance ensures the integrity of the `/project/` sandbox and the Chroma DB skill store.

## 2. Runbook

### 2.1 Handling Zombie Agents
An agent is classified as a "zombie" if its `last_heartbeat` in the Redis `agents:{id}` hash exceeds 60 seconds (double the 30s heartbeat interval).
- **Detection:** The dashboard highlights agents with a `status: zombie` tag.
- **Action:** 
    1. Terminate the process associated with the `agent_id`.
    2. Execute the Lua safety script to release any active file locks held by the zombie agent: `if redis.call("get",KEYS[1]) == ARGV[1] then return redis.call("del",KEYS[1]) else return 0 end`.
    3. Monitor the Redis `tasks:{id}` associated with the agent; the **module:monitor** will automatically reset these to `TASK_CREATED` and increment the `retry_count`.

### 2.2 Terminal Failure (Retry Count 10)
When a task hits the 10-retry limit, it transitions to the `FAILED` state.
- **Detection:** Dashboard entries for these tasks must be highlighted in high-contrast RED.
- **Action:**
    1. Inspect the generated YAML at `/history/tasks/T{id}.yaml`.
    2. Review the Jiju validation scores (typically < 80) to determine if the failure was due to logic errors or environment constraints.
    3. If the failure resulted from a "Doing Timeout" (120s), evaluate if the task requires decomposition into smaller L1-L3 sub-tasks.
    4. Manually purge the task from the Redis active keyspace if the automatic cleanup by **module:task_manager** fails.

### 2.3 Lock Contention Resolution
If multiple agents are stalled waiting for a file lock in the `/project/` prefix:
- **Detection:** Monitor Redis `lock:{filepath}` keys.
- **Action:** If a lock persists beyond 300 seconds (the default TTL `EX 300`), it is considered leaked. The system should automatically expire it, but manual intervention via `DEL lock:{filepath}` is permitted if blocking critical path L6 (Create) tasks.

## 3. Monitoring

### 3.1 Real-Time Dashboard Requirements
The monitoring dashboard must visualize the following Redis keys and transitions:
- **Active Task Queue:** Real-time count of `TASK_CREATED` items in `inbox:toneri` (L1-L3) and `inbox:onmyoji` (L4-L6).
- **Execution Latency:** Current duration of tasks in `DOING` state. Any task > 100s must trigger a visual warning before the 120s hard timeout.
- **Retry Heatmap:** A visual representation of `retry_count` distribution across active tasks.
- **Terminal Failure Visibility (ops:failure-visibility):** A dedicated "Failure Vault" screen listing all tasks that reached the 10-retry threshold. This view must display the task ID, the last agent involved, and the final error log.

### 3.2 Key Performance Indicators (KPIs)
| Metric | Threshold | Alert Level | Action |
| :--- | :--- | :--- | :--- |
| Thinking Timeout | > 300s | Warning | Log transition to `TASK_CREATED`. |
| Doing Timeout | > 120s | Critical | Terminate agent session & release locks. |
| Heartbeat | > 60s | Critical | Mark agent as `zombie`. |
| Retry Count | >= 10 | Terminal | Move to `FAILED`, highlight in RED, archive YAML. |
| Review Score | < 80 | Info | Increment `retry_count` and re-queue. |

### 3.3 Persistence Audit
The **module:monitor** must perform a daily sweep to ensure parity between the Redis `COMPLETED` records and the `/history/tasks/*.yaml` files. Any discrepancy (Redis record without YAML) indicates a failure in the state transition logic and must be logged as a system integrity error.

## 4. CI/CD Pipeline Generation Meta-Prompt

```yaml
# // @generated-by: codd propagate
# This workflow is generated to validate the Kanpaku system's task lifecycle and state management.
name: Kanpaku CI/CD Pipeline

on:
  pull_request:
    branches:
      - main
      - develop

jobs:
  build_verification:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20' # Detected from project engine constraints
          cache: 'npm'
      - name: Install dependencies
        run: npm ci
      - name: Build application
        run: npm run build

  unit_tests:
    needs: build_verification
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - name: Run Unit Tests
        run: npm run test:unit

  integration_tests:
    needs: build_verification
    runs-on: ubuntu-latest
    services:
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_PASSWORD: password
          POSTGRES_DB: kanpaku_test
        ports:
          - 5432:5432
    env:
      DATABASE_URL: postgresql://postgres:password@localhost:5432/kanpaku_test
      REDIS_URL: redis://localhost:6379
    steps:
      - uses: actions/checkout@v4
      - name: Database Seed
        run: npm run db:seed
      - name: Run Integration Tests (Task State Transitions)
        run: npm run test:integration

  e2e_tests:
    needs: integration_tests
    runs-on: ubuntu-latest
    services:
      redis:
        image: redis:7-alpine
      postgres:
        image: postgres:15-alpine
    env:
      DATABASE_URL: postgresql://postgres:password@localhost:5432/kanpaku_test
      REDIS_URL: redis://localhost:6379
      NEXTAUTH_SECRET: ${{ secrets.NEXTAUTH_SECRET }}
    steps:
      - uses: actions/checkout@v4
      - name: Install wait-on
        run: npm install -g wait-on
      - name: Start Application Server
        run: npm run start &
      - name: Wait for Health Endpoint
        run: wait-on http://localhost:3000/api/health
      - name: Run E2E Tests (Agent Workflows)
        run: npm run test:e2e

  performance_tests:
    needs: integration_tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Performance Tests (Concurrent Task Load)
        run: npm run test:perf -- --thresholds "doing_timeout=120,thinking_timeout=300"

merge_gate:
  if: always()
  needs: [unit_tests, integration_tests, e2e_tests, performance_tests]
  runs-on: ubuntu-latest
  steps:
    - name: Check All Tests Passed
      run: |
        if [[ "${{ needs.unit_tests.result }}" != "success" || \
              "${{ needs.integration_tests.result }}" != "success" || \
              "${{ needs.e2e_tests.result }}" != "success" || \
              "${{ needs.performance_tests.result }}" != "success" ]]; then
          echo "Test suite failed. PR merge blocked."
          exit 1
        fi

# Branch Protection Recommendations:
# 1. Require status check "merge_gate" to pass before merging.
# 2. Require conversation resolution.
# 3. Enforce 10-retry visibility dashboard as a prerequisite for manual QA sign-off.
```

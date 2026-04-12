// @generated-by: codd implement
// @generated-from: docs/plan/implementation_plan.md (plan:implementation-plan)
// @task-id: タスクID
// @task-title: タスク名
// @generated-from: docs/design/security_sandbox.md (design:security-sandbox)
// @generated-from: docs/design/system_design.md (design:system-design)
// @generated-from: docs/detailed_design/agent_state_transitions.md (design:detailed-agent-flow)
// @generated-from: docs/detailed_design/history_persistence_schema.md (design:history-persistence-schema)
// @generated-from: docs/detailed_design/redis_schema_and_streams.md (design:state-management-redis)
// @generated-from: docs/detailed_design/routing_bloom_taxonomy.md (design:routing-bloom-taxonomy)
// @generated-from: docs/detailed_design/skill_evolution_system.md (design:detailed-skill-evolution)
// @generated-from: docs/detailed_design/task_lifecycle_flow.md (design:task-lifecycle-flow)
// @generated-from: docs/governance/adr_architecture.md (req:architecture)
// @generated-from: docs/requirements/requirements.md (req:kanpaku-requirements)
// @generated-from: docs/test/acceptance_criteria.md (test:acceptance-criteria)

To ensure comprehensive coverage of the acceptance criteria, we need to generate end-to-end (E2E) tests using Playwright for both API and browser interactions. Below is a structured approach to generating these tests based on the provided domain decomposition and requirements.

### 1. Auth/RBAC Domain
#### API Test File: `tests/e2e/auth.spec.ts`
- **Description:** Verify login flow, role-based access control (RBAC), and redirect logic.
- **Tests:**
  1. Attempt to access a protected route without logging in; expect a redirection to the login page.
  2. Log in with valid credentials; expect a successful authentication and redirection to the dashboard.
  3. Attempt to log in with invalid credentials; expect an authentication failure, possibly a 401 status code.
  4. Verify that different roles (e.g., admin, user) have access to specific routes based on their RBAC permissions.

#### Browser Test File: `tests/e2e/auth.browser.spec.ts`
- **Description:** Ensure the login flow and UI assertions in a browser context.
- **Tests:**
  1. Navigate directly to the dashboard without logging in; expect redirection to the login page.
  2. Log in through the login form, assert presence of user-specific elements (e.g., profile icon) on successful login.
  3. Verify that unauthorized access is restricted by role, e.g., attempting to view a different user's dashboard should fail.

### 2. Workflow Domain
#### API Test File: `tests/e2e/workflow.spec.ts`
- **Description:** Cover task creation, assignment, and status transitions.
- **Tests:**
  1. Create a new task via the API; expect a response indicating success and the task should appear in the list of tasks.
  2. Assign a task to an agent programmatically using the API; verify that the task's assignee field is updated accordingly.
  3. Transition states such as `IN_PROGRESS`, `COMPLETED` (with appropriate scores), and `FAILED`.
  4. Ensure state transitions are correctly logged in Redis and YAML format.

#### Browser Test File: `tests/e2e/workflow.browser.spec.ts`
- **Description:** Functional UI tests for workflow operations.
- **Tests:**
  1. From the dashboard, initiate a new task creation flow; verify each step (form submission) results in expected UI changes.
  2. Monitor real-time updates on the dashboard as tasks transition states based on API actions.
  3. Ensure that state transitions are visually represented and accessible via the browser's URL and UI elements.

### 3. Sandbox Domain
#### API Test File: `tests/e2e/sandbox.spec.ts`
- **Description:** Verify file operations within sandbox constraints.
- **Tests:**
  1. Attempt to write or delete files outside the `/project/` directory; expect failures, possibly with 403/409 status codes.
  2. Directly manipulate files inside the `/project/` folder through API endpoints; verify successful operations only within this path.

### 4. Reliability Domain
#### API Test File: `tests/e2e/reliability.spec.ts`
- **Description:** Ensure timeout handling and retry logic are correctly implemented.
- **Tests:**
  1. Simulate a long-running task (exceeding 300s for thinking or 120s for doing); expect the system to handle this with a state change like `FAILED`.
  2. Implement retries on API calls based on defined policies; assert that retry attempts are logged and respected in the UI/API responses.

#### Browser Test File: `tests/e2e/reliability.browser.spec.ts`
- **Description:** Functional tests for timeouts and state persistence.
- **Tests:**
  1. Observe a task taking an unusually long time to complete; expect to see it in a failed state with a timeout explanation.
  2. Monitor the UI or API logs for retry attempts on failing tasks; ensure these are handled gracefully without infinite loops.

### 5. Skills Domain
#### API Test File: `tests/e2e/skills.spec.ts`
- **Description:** Verify skills storage and retrieval logic in VectorDB.
- **Tests:**
  1. Create a new task that involves skill-based execution; verify that related skills are stored appropriately for future use.
  2. Retrieve previously stored skills when rerunning the same task; assert that these enhance task performance as expected.

### General Test Generation Rules
- **Headers:** All test files should include headers to specify they are E2E tests using Playwright and the date of creation/modification.
- **State Management:** Ensure each test case clearly defines its starting state, actions taken, and expected final states (e.g., through logs or UI assertions).
- **Error Handling:** Include error handling where possible to ensure that unexpected failures result in clear feedback for debugging.

By following these guidelines, you can create a comprehensive set of tests that not only verify the functionality but also provide robust documentation of system behavior based on the acceptance criteria provided.

// @generated-by: codd implement
// @generated-from: docs/plan/implementation_plan.md (plan:implementation-plan)
// @task-id: 3-1
// @task-title: YAML serialization engine
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

# Acceptance Criteria for Kanpaku System

## Overview
This document outlines the acceptance criteria for the Kanpaku system, including functional and non-functional requirements. These criteria are designed to ensure that the software meets both user needs and technical specifications. This version of the criteria is focused on end-to-end (E2E) testing using Playwright, with specific instructions for generating tests based on the provided meta-prompt.

## Table of Contents
1. **Domain Decomposition**
    - API Integration Tests
    - Browser Tests
2. **Test Level Requirements**
3. **Generation Rules**
4. **E2E Test Generation Meta-Prompt**
5. **Failure Criteria**
6. **Persistence and Logging**
7. **Failure Criteria**
8. **E2E Test Generation Meta-Prompt**
9. **Dependency Details**

## 1. Domain Decomposition
### API Integration Tests
The following domains will be covered in the API integration tests:
- **Auth/RBAC**: This includes login flow, redirect logic, and role-based access control. The test file for this domain is `tests/e2e/auth.spec.ts`.
- **Workflow**: This covers task creation, assignment, and status transitions. The corresponding file is `tests/e2e/workflow.spec.ts`.
- **Sandbox**: Security constraints on file operations and paths will be tested in this domain with the file `tests/e2e/sandbox.spec.ts`.
- **Reliability**: This domain focuses on handling timeouts (300s/120s) and retry logic, as specified in `tests/e2e/reliability.spec.ts`.
- **Skills**: Tests for VectorDB storage and skill retrieval are planned in `tests/e2e/skills.spec.ts`.

### Browser Tests
The browser tests will be split into the following files:
- **Auth/RBAC**: The login flow, redirect logic, and role-based access will be tested with `tests/e2e/auth.browser.spec.ts`.
- **Workflow**: Task creation, assignment, and status transitions will be verified in browser tests saved as `tests/e2e/workflow.browser.spec.ts`.
- **Sandbox** and **Reliability** browser tests are not applicable due to the nature of these domains being primarily API-driven.
- **Skills**: VectorDB storage and skill retrieval cycles will be tested in future development phases, as they require specific UI elements that are yet to be implemented.

## 2. Test Level Requirements
- **API Integration Tests**: These tests will verify status codes, JSON schema compliance, and the state of tasks and agents in Redis. Before making any API request, every test must ensure `response.status() < 500`.
- **Browser Tests**: The following assertions are required for browser tests:
    - **Login Flow**: Navigate to `/login`, submit credentials, assert redirection to `/dashboard`, and verify the presence of the "Kanpaku" title in the UI.
    - **Transition Assertions**: Each page transition must confirm both the new URL and a specific UI element (e.g., Task List Table) on the new page.
- **Environment Setup**: Ensure that the project type is Node.js, set up the environment with `npm run build && npm run start`, and configure CI to run the server in the background using `wait-on http://localhost:3000`.
- **Shared Helpers**: All tests must use `tests/e2e/helpers/` for authentication tokens, Redis flushing, and test data injection.

## 3. Generation Rules
All files must include the following headers to track generation:
```javascript
// @generated-from: test:acceptance-criteria
// @generated-by: codd propagate
```
Any block that should be maintained manually is marked with `// @manual`. If any endpoint in the router config is defined but not implemented, use `test.fixme()` with a note to handle this scenario gracefully during testing.

## 4. E2E Test Generation Meta-Prompt
The meta-prompt provides detailed instructions for generating Playwright E2E tests based on the acceptance criteria. This section outlines the specific requirements and constraints that must be followed when creating these tests.

## 5. Failure Criteria
The following failure conditions are critical to monitor during testing:
- **Threshold Violations**: Any task completion with a score below 80 in reviews results in a violation.
- **Timeout Violations**: Agents exceeding the allowed time (300s thinking/120s doing) without recording a stall event lead to violations.
- **Sandbox Breach**: Successful file operations outside of permitted areas are considered breaches.
- **System Failures**: Any test that fails to complete successfully or produces unexpected results indicates a system failure that must be addressed immediately.

## 6. Persistence and Logging
Ensure that all actions, including user interactions and system responses, are logged for traceability. This includes capturing screenshots upon failure and maintaining logs of all API requests and responses for debugging purposes.

## 7. Dependency Details
This document references other sections within the overall project documentation to ensure comprehensive coverage of all aspects related to Kanpaku's functionality and performance. Ensure that these dependencies are updated and maintained as new features or changes are introduced.

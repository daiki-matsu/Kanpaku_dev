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

# Kanpaku System Acceptance Criteria Test Plan

## Overview
This document outlines the acceptance criteria for testing the Kanpaku system, a complex project management tool designed to handle tasks with precision and security. The tests are structured around four main domains: Authentication/RBAC, Workflow Management, File Operations (Sandbox), and Reliability & Skills. Each domain is further broken down into specific API integration and browser-based test cases.

## Test Domains

### 1. Authentication/RBAC
**Description:** This domain ensures that the login flow, role management, and access control are functioning correctly. It includes tests for user authentication, session handling, and redirect logic based on roles.
**API Test File:** `tests/e2e/auth.spec.ts`  
**Browser Test File:** `tests/e2e/auth.browser.spec.ts`

### 2. Workflow Management
**Description:** This domain focuses on the creation, assignment, and status transitions of tasks. It verifies that task management features are working as expected under different scenarios.
**API Test File:** `tests/e2e/workflow.spec.ts`  
**Browser Test File:** `tests/e2e/workflow.browser.spec.ts`

### 3. File Operations (Sandbox)
**Description:** This domain ensures that the system enforces strict file operations, particularly in regards to path security and unauthorized access. It does not include browser tests due to the nature of sandboxing constraints.
**API Test File:** `tests/e2e/sandbox.spec.ts`  
**Browser Test File:** N/A

### 4. Reliability & Skills
**Description:** This domain covers timeout handling and skill management, including the VectorDB storage and retrieval mechanisms used in task execution. It ensures that tasks are managed within expected timeframes and leverages skills for enhanced performance.
**API Test File:** `tests/e2e/reliability.spec.ts`  
**Browser Test File:** N/A

## Test Level Requirements
- **API Integration Tests:** Each API request must first assert a status code less than 500 to ensure the server is healthy. This includes checking JSON schema and verifying Redis state updates where applicable.
- **Browser Tests:** These tests are designed to simulate user interactions directly in the browser environment. They include login flow assertions, transitions between pages, and UI element presence checks.
- **Environment Setup:** The test suite must be capable of setting up the server environment from scratch (`npm run build && npm run start`) and running CI pipelines with background server execution controlled by `wait-on`.
- **Shared Helpers:** All tests use a shared helpers directory to manage authentication tokens, Redis state clearing, and dynamic data injection for consistent testing environments.

## Generation Rules
- Test files must include specific header comments indicating their automated generation from source criteria:
  ```javascript
  // @generated-from: test:acceptance-criteria
  // @generated-by: codd propagate
  ```
- Any section that requires manual intervention or validation should be marked with `// @manual`.
- Test files must handle unimplemented routes gracefully by using `test.fixme()` to note the gaps in functionality, which can then be addressed during development cycles.
- Release gates are set at quality levels where certain criteria must pass before a release is considered complete:
  - **100% Acceptance Criteria Coverage:** Each test case should directly validate or refute all acceptance criteria outlined in this document.
  - **Zero Failures in CI Pipeline:** Any `SKIP` or `FAIL` results are blockers for the release process, indicating incomplete or misaligned test suites.
  - **Explicit Assertion of Timeout Policy (300s thinking/120s doing):** This ensures that critical timeout settings are consistently enforced across all testing scenarios.
  - **Explicit Assertion of Review Score Threshold (>=80):** Ensures that task completion thresholds are rigorously tested to prevent low-quality releases.

## Conclusion
This test plan provides a comprehensive set of tests designed to validate the Kanpaku system's functionality, reliability, and security against the acceptance criteria established for this project. The combination of API integration and browser testing ensures a robust validation process that meets both functional and user interface requirements.

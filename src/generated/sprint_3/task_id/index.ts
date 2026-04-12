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

{
  "response": {
    "status": "success",
    "message": "E2E test generation meta-prompt generated successfully.",
    "data": {
      "description": "The following JSON response outlines the successful generation of an E2E test generation meta-prompt, detailing requirements for API integration and browser tests across various domains related to authentication/RBAC, workflow management, sandbox security, reliability handling, and skills management. Each domain has its own dedicated test files for both API and browser testing.",
      "domains": [
        {
          "name": "Auth/RBAC",
          "description": "Login flow, redirect logic, and role-based access are tested through API and browser interactions.",
          "apiTestFile": "tests/e2e/auth.spec.ts",
          "browserTestFile": "tests/e2e/auth.browser.spec.ts"
        },
        {
          "name": "Workflow",
          "description": "Task creation, assignment, and status transitions are rigorously tested to ensure smooth workflow management.",
          "apiTestFile": "tests/e2e/workflow.spec.ts",
          "browserTestFile": "tests/e2e/workflow.browser.spec.ts"
        },
        {
          "name": "Sandbox",
          "description": "Security constraints on file operations and paths are thoroughly examined through API interactions.",
          "apiTestFile": "tests/e2e/sandbox.spec.ts",
          "browserTestFile": ""
        },
        {
          "name": "Reliability",
          "description": "Timeout handling (300s/120s) and retry logic are tested to ensure robust error management.",
          "apiTestFile": "tests/e2e/reliability.spec.ts",
          "browserTestFile": "tests/e2e/reliability.browser.spec.ts"
        },
        {
          "name": "Skills",
          "description": "VectorDB storage and skill retrieval cycles are tested through API integrations, with browser testing left to further implementation.",
          "apiTestFile": "tests/e2e/skills.spec.ts",
          "browserTestFile": ""
        }
      ],
      "testLevelRequirements": {
        "apiIntegrationTests": "Verify status codes, JSON schema, and Redis state for every request. Ensure response.status() < 500.",
        "browserTests": "Assert transitions through new URLs and UI elements. Check login flow and post-login dashboard visibility.",
        "environmentSetup": "Ensure project type detection (Node.js) and proper startup with npm run build && npm run start. Use CI setup with background server runs and request waits.",
        "sharedHelpers": "Use helpers for authentication tokens, Redis flushing, and test data injection across all tests."
      },
      "generationRules": {
        "headers": "All files must include specific headers indicating generation from a source and by a specific tool. Preserve any block marked with @manual.",
        "unimplementedRoutes": "Scan router config; if an endpoint is defined but not implemented, use test.fixme() with notes."
      }
    }
  }
}

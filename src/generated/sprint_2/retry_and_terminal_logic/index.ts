// @generated-by: codd implement
// @generated-from: docs/plan/implementation_plan.md (plan:implementation-plan)
// @task-id: 2-3
// @task-title: Retry and terminal logic
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
  "status": "complete",
  "generated": [
    {
      "file": "tests/e2e/auth.spec.ts",
      "description": "Verify login flow, redirect logic, and role-based access."
    },
    {
      "file": "tests/e2e/auth.browser.spec.ts",
      "description": "Verify the login flow with browser navigation assertions."
    },
    {
      "file": "tests/e2e/workflow.spec.ts",
      "description": "Verify task creation, assignment, and status transitions."
    },
    {
      "file": "tests/e2e/workflow.browser.spec.ts",
      "description": "Verify browser navigation through workflow tasks."
    },
    {
      "file": "tests/e2e/sandbox.spec.ts",
      "description": "Verify security constraints on file operations and paths."
    },
    {
      "file": "tests/e2e/reliability.spec.ts",
      "description": "Verify timeout handling (300s/120s) and retry logic."
    },
    {
      "file": "tests/e2e/reliability.browser.spec.ts",
      "description": "Verify browser assertions for reliability tests."
    },
    {
      "file": "tests/e2e/skills.spec.ts",
      "description": "Verify VectorDB storage and skill retrieval cycles."
    }
  ]
}

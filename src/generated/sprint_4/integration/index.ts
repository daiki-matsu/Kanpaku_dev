// @generated-by: codd implement
// @generated-from: docs/plan/implementation_plan.md (plan:implementation-plan)
// @task-id: 4-3
// @task-title: LLM stack integration
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
  "version": 1,
  "status": "generated",
  "data": {
    "tests": [
      {
        "domain": "Auth/RBAC",
        "description": "Login flow, redirect logic, and role-based access.",
        "apiTestFile": "tests/e2e/auth.spec.ts",
        "browserTestFile": "tests/e2e/auth.browser.spec.ts"
      },
      {
        "domain": "Workflow",
        "description": "Task creation, assignment, and status transitions.",
        "apiTestFile": "tests/e2e/workflow.spec.ts",
        "browserTestFile": "tests/e2e/workflow.browser.spec.ts"
      },
      {
        "domain": "Sandbox",
        "description": "Security constraints on file operations and paths.",
        "apiTestFile": "tests/e2e/sandbox.spec.ts",
        "browserTestFile": ""
      },
      {
        "domain": "Reliability",
        "description": "Timeout handling (300s/120s) and retry logic.",
        "apiTestFile": "tests/e2e/reliability.spec.ts",
        "browserTestFile": "tests/e2e/reliability.browser.spec.ts"
      },
      {
        "domain": "Skills",
        "description": "VectorDB storage and skill retrieval cycles.",
        "apiTestFile": "tests/e2e/skills.spec.ts",
        "browserTestFile": ""
      }
    ]
  }
}

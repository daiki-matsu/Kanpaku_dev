// @generated-by: codd implement
// @generated-from: docs/plan/implementation_plan.md (plan:implementation-plan)
// @task-id: 1-3
// @task-title: Directory structure and basic utilities
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
  "meta": {
    "title": "Kanpaku System Acceptance Criteria",
    "description": "Detailed acceptance criteria for the Kanpaku system, including test generation instructions and failure conditions.",
    "version": "1.0"
  },
  "sections": [
    {
      "id": "intro",
      "title": "Introduction",
      "content": "This document outlines the acceptance criteria for the Kanpaku system, including its functionalities, performance requirements, and test generation instructions."
    },
    {
      "id": "system_requirements",
      "title": "System Requirements",
      "content": [
        "The system must handle task creation, assignment, and status updates efficiently.",
        "File operations within the sandbox should be strictly controlled to prevent unauthorized access.",
        "Skill retrieval mechanisms must ensure accurate execution based on historical data."
      ]
    },
    {
      "id": "failure_conditions",
      "title": "Failure Criteria",
      "content": [
        "Review results in a 'TASK_COMPLETED' status with a score below 80.",
        "Agents remain in 'thinking' for more than 300 seconds or 'doing' for more than 120 seconds without recording a stall event.",
        "File operations occur outside the designated '/project/' folder."
      ]
    },
    {
      "id": "test_generation",
      "title": "E2E Test Generation Meta-Prompt",
      "content": [
        "Generate Playwright E2E tests split into domains such as Auth/RBAC, Workflow, Sandbox, Reliability, and Skills.",
        "Each domain should have an API integration test and a Browser test."
      ]
    },
    {
      "id": "test_setup",
      "title": "Test Setup and Requirements",
      "content": [
        "Ensure the project type is detected (Node.js).",
        "Startup: Run `npm run build && npm run start`.",
        "CI setup: Run server in background and use `wait-on http://localhost:3000` for API integration tests."
      ]
    },
    {
      "id": "generation_rules",
      "title": "Generation Rules",
      "content": [
        "All files must start with specific headers to indicate generation and maintenance instructions.",
        "Preserve any block marked with `// @manual` for manual testing scenarios."
      ]
    }
  ]
}

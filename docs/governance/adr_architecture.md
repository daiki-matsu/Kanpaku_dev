---
codd:
  node_id: gov:adr-001-architecture
  type: governance
  depends_on:
  - id: req:kanpaku-requirements
    relation: derives_from
    semantic: governance
  depended_by:
  - id: design:system-design
    relation: derives_from
    semantic: technical
  - id: infra:resource-allocation
    relation: depends_on
    semantic: technical
  conventions:
  - targets:
    - agent:hierarchy
    reason: The Kanpaku-Jiju-Toneri-Onmyoji hierarchy must be strictly enforced for
      task delegation.
  modules:
  - orchestrator
---

# ADR: Agent Hierarchy and State Management

## 1. Overview
The Kanpaku System (関白システム) establishes an autonomous, multi-agent hierarchy inspired by the Heian-era Japanese imperial court. This architecture enforces a strict division of labor and state-driven task management to ensure consistency, observability, and parallel execution. The system transitions from the previous Shogun architecture to a more nuanced structure where the Kanpaku acts as the primary interface, the Jiju manages task decomposition and reviews, and the Toneri and Onmyoji execute specific roles based on Bloom’s taxonomy levels. 

By integrating Consistency-Driven Development (CoDD), the system mandates that all agent actions reflect real-time updates on a dashboard and adhere to rigorous validation standards. Security is maintained through strict file-system sandboxing, limiting AI operations to designated project directories. Performance is governed by explicit timeouts and heartbeat intervals to prevent stalls and ensure responsive interrupts.

## 2. Decision Log

### 2.1 Agent Hierarchy and Role Enforcement
The system strictly enforces the following hierarchy (agent:hierarchy) for all task delegations:
- **Mikado (帝):** The human user. Provides high-level instructions and monitors the dashboard.
- **Kanpaku (関白):** The sole interface for the Mikado. Uses `gemma4-26B-A4B` (Ollama) to set goals, create instruction sets for Jiju, and decide on agent skill creation.
- **Jiju (侍従):** The middle-management layer. Uses `gemma4-E2B` (Ollama). Responsible for decomposing instructions into tasks, assigning Toneri or Onmyoji, reviewing results via `codd review`, and updating the dashboard. Runs in multiple processes to handle parallel task oversight.
- **Toneri (舎人):** Execution agents for Bloom levels L1 (Remember), L2 (Understand), and L3 (Apply). Uses `Bonsai-8B`, `DeepSeek 6.7B`, or `gemma4-E2B` (llama.cpp/Ollama). Authorized for file operations within the sandbox.
- **Onmyoji (陰陽師):** Thinking-specialized agents for Bloom levels L4 (Analyze), L5 (Evaluate), and L6 (Create). Uses `gemma4-26B-A4B`. These agents are strictly prohibited from direct file execution and focus on pattern extraction and architectural design.

### 2.2 State Management and Redis Data Structures
To maintain system-wide consistency, Redis is utilized as the primary state store.
- **Task Management (`tasks:{task_id}`):** Stores task settings (type, priority 1-100, bloom_level), assignment data, execution results, and review scores. Statuses include `created`, `doing`, `reviewing`, `completed`, and `failed`.
- **Agent Monitoring (`agents:{agent_id}`):** Tracks status (`idle`, `thinking`, `working`, `error`, `retrying`, `stopped`), the current task ID, and the `last_heartbeat`.
- **Event Orchestration:**
    - `events:stream`: A global stream for event history (e.g., `TASK_STARTED`, `REVIEW_REJECTED`).
    - `inbox:{agent_id}`: Per-agent streams for receiving task notifications (Nudges).
- **Concurrency Control (`lock:{filepath}`):** Implements a distributed lock with a 300s TTL to prevent simultaneous file modifications. Locks are checked using `GET` and released via Lua scripts to ensure atomicity.

### 2.3 Operational Rules and Timeouts
The `AgentTimePolicy` is strictly applied to prevent process stagnation:
- **Thinking Timeout:** 300 seconds (for LLM inference).
- **Doing Timeout:** 120 seconds (for I/O and file operations).
- **Heartbeat Interval:** 30 seconds. Agents must emit a status update (e.g., "Creating document...") every 30 seconds.
- **Retry Logic:** If a task reaches `retry.count = 10`, it is moved to `failed` and highlighted in red on the dashboard.

### 2.4 Skill Evolution and VectorDB Integration
The system self-evolves by extracting successful patterns into "Skills" stored in Chroma (VectorDB):
1. **Trigger:** `TASK_COMPLETED` with a `review.score >= 80`.
2. **Analysis:** Kanpaku initiates analysis; Onmyoji extracts the structural pattern.
3. **Storage:** Skills are saved as JSON-structured documents in the `skills` collection, indexed by embeddings of their descriptions and success patterns.
4. **Retrieval:** During `TASK_CREATED`, the Jiju queries the top 3 similar skills based on `success_rate` and `usage_count` to inject as prompt templates.

### 2.5 Security and Sandbox Constraints
- **File Isolation:** All file operations (write, move, delete) are restricted to the `/project/` directory. The `Executor` layer must validate that every `path` starts with the authorized prefix, raising an exception and triggering a `TASK_FAILED` state if violated.
- **Auth and Access:** Only the Jiju (via system-level CoDD commands) is authorized to move a task to the `completed` status after passing `codd validate` and `codd review`.

### 2.6 Infrastructure and Model Deployment
The system is deployed on hardware featuring an NVIDIA RTX 2070 SUPER (8GB VRAM), 64GB DDR4 RAM, and a Core i5-13600KF.
- **Inference Engines:** Combined use of Ollama (for Gemma-based models) and llama.cpp (for Bonsai and DeepSeek) to optimize VRAM utilization.
- **Persistence:** While Redis holds the live state, all task, event, and agent histories are persisted as YAML files in `/history/` and `/logs/` for long-term auditability.

## 3. Follow-ups
- **Android Integration:** Develop a mobile management interface for the Mikado to monitor the dashboard and intervene in failed tasks.
- **LoRA Specialization:** Implement logic for the Kanpaku to trigger LoRA fine-tuning based on accumulated successful skill patterns to improve decision-making accuracy.
- **Task Cleanup:** Implement a periodic cleanup routine to archive completed task files from the `/history/tasks/` directory to secondary storage after 30 days.
- **Skill Pruning:** Establish a routine for the Onmyoji to merge similar skills and delete those with a `success_rate` below 20% after at least 5 usage attempts.

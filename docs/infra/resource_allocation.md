---
codd:
  node_id: infra:resource-allocation
  type: document
  depends_on:
  - id: gov:adr-001-architecture
    relation: depends_on
    semantic: technical
  depended_by: []
  conventions:
  - targets:
    - infra:deployment
    reason: Parallel execution of models must not exceed 8GB VRAM; use quantization
      (llama.cpp) where necessary.
  modules:
  - llm_provider
---

# Model Deployment and Resource Config

## 1. Overview
The Kanpaku system deployment is optimized for high-autonomy execution within a resource-constrained environment, specifically targeting an NVIDIA RTX 2070 SUPER with 8GB of VRAM. This document details the allocation of computational resources, model quantization strategies, and the orchestration of inference engines to maintain system stability while adhering to the strict agent hierarchy defined in `gov:adr-001-architecture`. 

The primary challenge is the execution of `gemma4-26B-A4B` (Kanpaku/Onmyoji) and various 8B-class models (Jiju/Toneri) within the 8GB VRAM ceiling. To resolve this, the system utilizes a hybrid inference approach combining Ollama for Gemma-based models and llama.cpp for Bonsai and DeepSeek models, prioritizing GGUF quantization and selective layer offloading to the Core i5-13600KF CPU and 64GB DDR4 RAM.

## 2. Details

### 2.1 Hardware Specification
All components are deployed on a single node with the following specifications:
- **GPU:** NVIDIA GeForce RTX 2070 SUPER (8GB GDDR6 VRAM).
- **CPU:** Intel Core i5-13600KF (14 cores, 20 threads).
- **RAM:** 64GB DDR4-3200.
- **Storage:** NVMe SSD for fast model loading and state persistence in Redis.
- **OS/Runtime:** Ubuntu 22.04 LTS, Docker, NVIDIA Container Toolkit.

### 2.2 Model Quantization and Memory Mapping
To comply with the `infra:deployment` constraint (8GB VRAM limit), the following quantization and offloading configurations are mandated:

| Agent Role | Model Name | Engine | Quantization | VRAM Allocation | CPU Offloading |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Kanpaku** | gemma4-26B-A4B | Ollama | Q3_K_M (GGUF) | 4.5 GB (partial) | ~12 GB in System RAM |
| **Onmyoji** | gemma4-26B-A4B | Ollama | Q3_K_M (GGUF) | 4.5 GB (partial) | ~12 GB in System RAM |
| **Jiju** | gemma4-E2B | Ollama | Q4_K_M | 2.1 GB | None |
| **Toneri (L1-L3)** | Bonsai-8B | llama.cpp | Q4_K_M | 5.5 GB | None |
| **Toneri (L1-L3)** | DeepSeek 6.7B | llama.cpp | Q5_K_M | 5.2 GB | None |

### 2.3 Inference Engine Configuration
- **Ollama (Endpoint: `localhost:11434`):**
  - Manages `gemma4` family models.
  - Configuration: `OLLAMA_NUM_PARALLEL=1` to prevent VRAM oversubscription during Kanpaku/Onmyoji reasoning.
  - Context Window: 8192 tokens for Kanpaku; 4096 tokens for Jiju.
- **llama.cpp (Endpoint: `localhost:8080`):**
  - Manages `Bonsai-8B` and `DeepSeek 6.7B` using the server binary.
  - Flag: `--n-gpu-layers 35` for Toneri models to ensure they stay entirely within the 8GB VRAM when active.

### 2.4 Resource Guarding and Parallelism
The system enforces the following operational rules to maintain the 8GB VRAM invariant:
1. **Serialization of Large Models:** Requests to Kanpaku and Onmyoji (26B) are queued. They are never allowed to execute inference simultaneously on the GPU.
2. **Dynamic Context Management:** Jiju agents running in parallel must have their `num_ctx` capped at 2048 if more than three processes are active.
3. **VRAM Guardrail:** A monitoring script (`scripts/vram_guard.py`) checks VRAM usage via `nvidia-smi` every 5 seconds. If usage exceeds 7.8GB, the script sends a `SIGTERM` to the lowest priority Toneri process and sets the task status to `retrying` in Redis.

### 2.5 Persistence and State Storage
- **Redis (`localhost:6379`):** Stores task keys (`tasks:{task_id}`), agent heartbeats, and locks.
- **ChromaDB (`localhost:8000`):** Vector database for Skill Evolution. Uses `SentenceTransformers` on the CPU to reserve GPU for LLM inference.
- **File System:** All logs and task histories are stored in `/project/history/` and `/project/logs/` as YAML, as specified in `gov:adr-001-architecture`.

### 2.6 Compliance and Security
- **Constraint Compliance (infra:deployment):** Parallel execution is managed by the Jiju agent acting as a traffic controller. By utilizing Q3_K_M quantization for the 26B models and offloading layers to the 64GB system RAM, the system ensures that the 8GB VRAM limit is never breached, even during complex "Analyze" (L4) or "Create" (L6) tasks.
- **Sandbox Enforcement:** The `Executor` class in the Toneri/Onmyoji layer performs a prefix check on all file paths. Operations outside `/project/` trigger an immediate `PermissionError` and transition the task to `failed`.
- **SLA/Performance:** 
  - Thinking Timeout: 300s.
  - Doing Timeout: 120s.
  - Heartbeat Requirement: Every 30s via `agents:{agent_id}` updates in Redis.

## 3. Open Questions
- **26B Performance:** Will Q3_K_M quantization significantly degrade the Onmyoji's ability to perform L6 (Create) architectural design compared to 4-bit or 8-bit?
- **Inference Latency:** Given the partial CPU offloading for the 26B model, what is the expected tokens-per-second (TPS), and how will this impact the 300s thinking timeout?
- **VRAM Fragmentation:** Does frequent loading/unloading between Ollama and llama.cpp cause VRAM fragmentation that might require periodic engine restarts?

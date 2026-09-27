# NeMo Agent Toolkit (NAT) Workspace

This workspace is configured with NVIDIA's **NeMo Agent Toolkit** (`nvidia-nat`) along with all first-party plugin integrations.

**GitHub Repository:** [shaistamunir1214-eng/NeMo-Agent-Toolkit-ASME-RAG](https://github.com/shaistamunir1214-eng/NeMo-Agent-Toolkit-ASME-RAG)

---

## Environment Information

- **Virtual Environment:** `.venv` (Python 3.12 64-bit)
- **NeMo Agent Toolkit Version:** `1.6.0` (`nvidia-nat`)
- **CLI Executable:** `.venv\Scripts\nat.exe`

### Integrated Frameworks & Modules
- **LangChain / LangGraph:** `1.4.2` / `1.2.12` (`nvidia-nat-langchain`)
- **LlamaIndex:** `0.14.25` (`nvidia-nat-llama-index`)
- **CrewAI:** `0.203.2` (`nvidia-nat-crewai`)
- **Semantic Kernel:** `1.36.0` (`nvidia-nat-semantic-kernel`)
- **FastMCP & MCP:** `3.4.0` / `1.30.0` (`nvidia-nat-fastmcp`, `nvidia-nat-mcp`)
- **Observability & Profiling:** Arize Phoenix, OpenTelemetry, Weave (`nvidia-nat-phoenix`, `nvidia-nat-opentelemetry`, `nvidia-nat-profiler`)
- **Security & Guardrails:** NeMo Guardrails policy, Red-team evaluators (`nvidia-nat-security`)
- **Optimization & Evaluation:** Config/prompt optimizer, ATIF evaluation (`nvidia-nat-config-optimizer`, `nvidia-nat-eval`)

---

## Getting Started

### 1. Activate the Virtual Environment

In Windows PowerShell:
```powershell
$env:PYTHONUTF8 = "1"
.venv\Scripts\activate
```

### 2. Verify CLI & Components

```powershell
# Show version
nat --version

# View all installed CLI commands
nat --help

# List registered components
nat info components
```

### 3. Validate a Workflow Configuration

```powershell
nat validate --config_file verify_config.yml
```

### 4. Run a Workflow

Run via the console front-end:
```powershell
nat run --config_file verify_config.yml --input "Hello from NeMo Agent Toolkit!"
```

Or serve via the FastAPI front-end:
```powershell
nat serve --config_file verify_config.yml --host 127.0.0.1 --port 8000
```

---

## Configuring NVIDIA NIM API Keys & Base URL

The default base URL for hosted NVIDIA NIM models is:
```text
https://integrate.api.nvidia.com/v1
```

### 1. Environment Configuration (`.env`)
In [`.env`](file:///e:/NEMO%20NATO/.env):
```env
NVIDIA_API_KEY=nvapi-your-key-here
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
```
*The NAT CLI automatically loads `.env` upon execution.*

---

## Model Priority & Fallback Hierarchy

The system is configured with **`nvidia/nemotron-3-ultra-550b-a55b`** as the **Primary Model**, backed by an automated 4-tier fallback chain:

1. **Primary:** `nvidia/nemotron-3-ultra-550b-a55b` (Deepest answers)
2. **Fallback 1:** `nvidia/nemotron-3-super-120b-a12b` (Rich answers)
3. **Fallback 2:** `openai/gpt-oss-20b` (Workhorse)
4. **Fallback 3:** `meta/muse-glimmer-30b` (Reliable alternate)
5. **Fallback 4:** `meta/llama-3.2-11b-vision-instruct` (Vision / Fallback)

---

## Example Workflow Configuration (`test_workflow/configs/config.yml`)

```yaml
functions:
  current_datetime:
    _type: current_datetime
  test_workflow:
    _type: test_workflow
    prefix: "Hello:"

llms:
  nim_llm:
    _type: fallback_nim
    primary_model: nvidia/nemotron-3-ultra-550b-a55b
    fallback_models:
      - nvidia/nemotron-3-super-120b-a12b
      - openai/gpt-oss-20b
      - meta/muse-glimmer-30b
      - meta/llama-3.2-11b-vision-instruct
    base_url: https://integrate.api.nvidia.com/v1
    temperature: 0.0
    max_tokens: 512

workflow:
  _type: react_agent
  llm_name: nim_llm
  tool_names: [current_datetime, test_workflow]
```

Run with:
```powershell
nat run --config_file test_workflow/configs/config.yml --input "Echo NATO is fully operational"
```

---

## ASME B31.8-2010 RAG Agent

A specialized **Retrieval-Augmented Generation (RAG) Agent** is configured to answer technical questions, generate summaries, look up formulas, and explain pipeline safety/design rules strictly grounded in the **ASME B31.8-2010 standard** (*Gas Transmission and Distribution Piping Systems*).

### RAG Architecture
- **Document Source:** [`ASME B31.8-2010 .pdf`](file:///e:/NEMO%20NATO/ASME%20B31.8-2010%20.pdf) (212 pages).
- **Index Status:** 984 chunks embedded and persisted in [`data/asme_chroma/`](file:///e:/NEMO%20NATO/data/asme_chroma).
- **Embeddings:** `nvidia/nemotron-3-embed-1b` (2048-dim vectors).
- **LLM Pipeline:** Primary `nvidia/nemotron-3-ultra-550b-a55b` with 4-tier fallback (`fallback_nim`).
- **Tool:** `asme_b31_8_search` (retrieves relevant paragraphs, formulas, tables, and page citations).

### Example RAG Queries

```powershell
# 1. Technical Formula Lookup
nat run --config_file asme_rag_config.yml --input "What is the steel pipe design formula in ASME B31.8, and what do the variables represent?"

# 2. Section Summary
nat run --config_file asme_rag_config.yml --input "Summarize the Class Locations 1, 2, 3, and 4 in ASME B31.8 and explain how they are determined"

# 3. Safety & Testing Requirements
nat run --config_file asme_rag_config.yml --input "What are the pressure test requirements for pipelines operating at hoop stress levels of 30% or more of SMYS?"
```

---

## Serving via FastAPI Web Endpoint

To serve the ASME RAG Agent as a REST API:
```powershell
# Method 1 (Quick script):
.\serve.ps1

# Method 2 (Direct):
.venv\Scripts\Activate.ps1
nat serve --config_file asme_rag_config.yml --host 127.0.0.1 --port 8000
```

- **API Documentation & Swagger UI:** `http://127.0.0.1:8000/docs`
- **Health Check:** `http://127.0.0.1:8000/health`
- **Workflow Endpoint:** `POST http://127.0.0.1:8000/v1/workflow`
- **OpenAI-Compatible Chat Endpoint:** `POST http://127.0.0.1:8000/v1/chat/completions`






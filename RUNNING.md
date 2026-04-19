# Running Guide

This guide explains what an open-source user needs to install, configure, and run.

The intended usage model is:

- you have a hosted InnoEval API URL
- you have an API key for that URL
- you run this demo locally as a client

You do not need to understand or deploy the backend internals in order to use this directory.

## 1. Installation

After cloning the repository:

```bash
cd open-source/demo
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## 2. Requirement Matrix

| Task | API access | LLM | GROBID | Local embedding model | Local reranker model |
| --- | --- | --- | --- | --- | --- |
| `paper_grounding_compare` | Required | Required | Required | Required | Required |
| `topic_trend_review` | Required | Required | Not required | Not required | Not required |
| `related_authors` | Required | Not required | Not required | Not required | Not required |
| `author_research_profile` | Required | Required | Not required | Not required | Not required |
| `idea_generation` | Required | Required | Not required | Not required | Not required |

## 3. Environment Configuration

`run_demo.py` reads `.env` from this directory by default.

### 3.1 Required for all tasks

```env
KG2API_BASE_URL=https://your-api-host.example.com
KG2API_API_KEY=replace-me
KG2API_TIMEOUT=120
```

### 3.2 Required for tasks 1, 2, 4, and 5

```env
OPENAI_API_KEY=replace-me
OPENAI_BASE_URL=https://your-openai-compatible-endpoint/v1
OPENAI_MODEL=your-model-name
```

### 3.3 Required for task 1 only

```env
GROBID_BASE_URL=http://127.0.0.1:8070
OA_API_KEY=
OPENALEX_MAILTO=
```

Notes:

- `OPENAI_BASE_URL` can point to any OpenAI-compatible service.
- Task 1 grounding also uses the credentials from `.env` for its local LLM calls.
- Task 1 grounding derives its chat completions URL from `OPENAI_BASE_URL` unless `GROUNDING_API_URL` is set.
- Task 1 grounding derives its model from `OPENAI_MODEL` unless `query_model` is set in task params.
- Task 1 model paths are not stored in `.env` by default. Pass them with `--params-file` or `--params-json`.

## 4. Task 1 Preparation

Task 1 is the only task that needs local retrieval infrastructure.

Before running `paper_grounding_compare`, make sure:

- a GROBID service is already running and reachable at `GROBID_BASE_URL`
- your embedding model is available locally or resolvable by `sentence-transformers`
- your reranker model is available locally or resolvable by `sentence-transformers`

Practical guidance:

- Use an official GROBID deployment method appropriate for your environment, then expose the service as an HTTP endpoint.
- Keep `GROBID_BASE_URL` in `.env` so the same local configuration can be reused across Task 1 runs.
- Before starting the demo, verify that the GROBID service is reachable and healthy. In a default local setup, `http://127.0.0.1:8070/api/isalive` should respond successfully.
- For reproducibility, local filesystem paths are preferred for the embedding and reranker models, but model identifiers resolvable by `sentence-transformers` are also supported.

A typical params file looks like this:

```json
{
  "embedding_model_path": "/absolute/path/to/your/bge-large-en-v1.5",
  "reranker_model_path": "/absolute/path/to/your/bge-reranker-large"
}
```

A ready-to-copy example is provided at `examples/task1_params.local.example.json`.

Optional Task 1 params you may add when needed:

- `grobid_base_url`: override `GROBID_BASE_URL` from `.env`
- `query_api_url`: override the grounding chat completions endpoint
- `query_model`: override the grounding model name
- `grounding_device`: pin local embedding/reranker execution to a specific device

## 5. Running Tasks

### Task 1: `paper_grounding_compare`

Flow:

1. Call `POST /v1/search`
2. Resolve or download PDFs locally
3. Parse PDFs into TEI/XML via GROBID
4. Run local paragraph grounding
5. Generate an idea evaluation summary with an LLM

Example:

```bash
python3 run_demo.py \
  --task-type paper_grounding_compare \
  --idea-text "Use literature-grounded evidence to evaluate research ideas." \
  --params-file examples/task1_params.local.example.json \
  --pretty
```

Useful params:

- `search_final_top_k`
- `manifest_top_k`
- `grounding_final_top_k`
- `dense_candidate_k`
- `max_paragraphs_per_paper`
- `grobid_base_url`
- `grounding_device`
- `embedding_model_path`
- `reranker_model_path`
- `query_model`
- `query_api_url`

### Task 2: `topic_trend_review`

Flow:

1. Call `POST /v1/search`
2. Sort papers by year
3. Summarize topic evolution with an LLM

Example:

```bash
python3 run_demo.py \
  --task-type topic_trend_review \
  --topic-text "research idea evaluation with large language models" \
  --pretty
```

### Task 3: `related_authors`

Flow:

1. Call `POST /v1/authors/related`
2. Optionally fall back to `POST /v1/search` if query text still needs to be resolved
3. Call `POST /v1/authors/support-papers`

Example:

```bash
python3 run_demo.py \
  --task-type related_authors \
  --idea-text "knowledge-grounded evaluation of scientific research ideas" \
  --pretty
```

### Task 4: `author_research_profile`

Flow:

1. Call `POST /v1/authors/papers`
2. Sample papers locally
3. Summarize the author's trajectory with an LLM

Example:

```bash
python3 run_demo.py \
  --task-type author_research_profile \
  --author-name "Geoffrey Hinton" \
  --pretty
```

### Task 5: `idea_generation`

Flow:

1. Call `POST /v1/search`
2. Summarize retrieved literature into generated ideas with an LLM

Example:

```bash
python3 run_demo.py \
  --task-type idea_generation \
  --topic-text "scientific idea generation with retrieval-augmented large language models" \
  --pretty
```

## 6. Request File Mode

You can also run tasks from a JSON request file:

```bash
python3 run_demo.py --request-file examples/task2_request.json --pretty
python3 run_demo.py --request-file examples/task3_request.json --pretty
python3 run_demo.py --request-file examples/task4_request.json --pretty
python3 run_demo.py --request-file examples/task5_request.json --pretty
```

Task 1 request files usually need a companion params file because local model paths are environment-specific.

## 7. Output Layout

Every run writes a new directory under `runs/<run-id>/`.

Common files:

- `request.json`
- `result.json`
- `result.md`

Task 1 additional artifacts:

- `artifacts/search`
- `artifacts/manifest`
- `artifacts/grounding`
- `artifacts/idea_evaluation`

## 8. Common Issues

- `401 Invalid API key`
  - Check `KG2API_API_KEY`
- `Missing KG2API_BASE_URL` or `Missing KG2API_API_KEY`
  - Check `.env`
- Task 1 fails with GROBID connection errors
  - Make sure `GROBID_BASE_URL` points to a running service and that the service health endpoint responds successfully
- Task 1 fails while loading models
  - Check `embedding_model_path` and `reranker_model_path`
- Tasks 1, 2, 4, or 5 fail with missing LLM credentials
  - Check `OPENAI_API_KEY`, `OPENAI_BASE_URL`, and `OPENAI_MODEL`

## 9. Testing

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

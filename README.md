# InnoEval Open Demo

This directory is the open-source client-side demo for InnoEval.

It is designed for users who have:

- a hosted InnoEval API URL
- an API key for that service

Users do not need to know how the backend service is implemented. This demo does not talk to Neo4j directly. It only calls the public HTTP API and runs a small amount of local processing when a task needs it.

## What This Demo Provides

- A single CLI entrypoint: `run_demo.py`
- Five runnable downstream tasks
- JSON and Markdown outputs for every run
- Optional local PDF/grounding pipeline for Task 1

## Tasks

| Task | Task Type | What it does | Extra local requirements |
| --- | --- | --- | --- |
| 1 | `paper_grounding_compare` | Retrieve papers from the API, resolve PDFs locally, parse them into TEI/XML, run paragraph grounding, then produce an idea evaluation summary | GROBID, embedding model, reranker model, LLM |
| 2 | `topic_trend_review` | Retrieve papers from the API and summarize topic evolution with an LLM | LLM |
| 3 | `related_authors` | Retrieve related authors and supporting papers from the API | None beyond API access |
| 4 | `author_research_profile` | Retrieve an author's papers from the API and summarize their research profile with an LLM | LLM |
| 5 | `idea_generation` | Retrieve papers from the API and generate new research ideas with an LLM | LLM |

## What Users Need

### Required for all tasks

- Python 3.10+
- Access to an InnoEval API endpoint
- An API key for that endpoint

### Required for tasks 1, 2, 4, and 5

- An OpenAI-compatible chat completion endpoint
- A model name and API key for that endpoint

### Required for task 1 only

- A running GROBID service
- A sentence-transformers embedding model
- A reranker model for paragraph reranking
- Optional OpenAlex credentials if PDF fallback downloads are needed

## Quick Start

After cloning the repository:

```bash
cd open-source/demo
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and set at least:

```env
KG2API_BASE_URL=https://your-api-host.example.com
KG2API_API_KEY=replace-me
```

If you want to run tasks 1, 2, 4, or 5, also set:

```env
OPENAI_API_KEY=replace-me
OPENAI_BASE_URL=https://your-openai-compatible-endpoint/v1
OPENAI_MODEL=your-model-name
```

If you want to run task 1, also set:

```env
GROBID_BASE_URL=http://127.0.0.1:8070
OA_API_KEY=
OPENALEX_MAILTO=
```

Task 1 local model paths are usually passed through `--params-file` or `--params-json`, not through `.env`.

## Task 1 Local Preparation

Task 1 is designed to be genuinely runnable in an open-source setting, but it has a small local preparation step.

Before running `paper_grounding_compare`, make sure:

- GROBID is deployed as an HTTP service and reachable at `GROBID_BASE_URL`
- your embedding model is available either as a local path or a resolvable `sentence-transformers` model identifier
- your reranker model is available either as a local path or a resolvable `sentence-transformers` model identifier

Recommended practice:

- keep `GROBID_BASE_URL` in `.env`
- keep machine-specific model paths in a local params file
- keep the hosted API URL and LLM settings in `.env`

The sample params file at `examples/task1_params.local.example.json` intentionally contains only the local model fields. By default, Task 1 derives its grounding LLM endpoint from `OPENAI_BASE_URL` and its grounding model from `OPENAI_MODEL`.

If you deploy GROBID on a non-default host or need a task-specific override, you may still pass `grobid_base_url`, `query_api_url`, or `query_model` through `--params-file`.

## Run Examples

Task 2:

```bash
python3 run_demo.py \
  --task-type topic_trend_review \
  --topic-text "research idea evaluation with large language models" \
  --pretty
```

Task 3:

```bash
python3 run_demo.py \
  --task-type related_authors \
  --idea-text "knowledge-grounded evaluation of scientific research ideas" \
  --pretty
```

Task 4:

```bash
python3 run_demo.py \
  --task-type author_research_profile \
  --author-name "Geoffrey Hinton" \
  --pretty
```

Task 5:

```bash
python3 run_demo.py \
  --task-type idea_generation \
  --topic-text "scientific idea generation with retrieval-augmented large language models" \
  --pretty
```

Task 1 usually needs a params file because it requires local model paths:

```bash
python3 run_demo.py \
  --task-type paper_grounding_compare \
  --idea-text "Use literature-grounded evidence to evaluate research ideas." \
  --params-file examples/task1_params.local.example.json \
  --pretty
```

You can also run any task from a JSON request file:

```bash
python3 run_demo.py --request-file examples/task4_request.json --pretty
```

## Output

Every run creates a folder under `runs/<run-id>/` and writes:

- `request.json`
- `result.json`
- `result.md`

Task 1 also writes intermediate artifacts under:

- `artifacts/search`
- `artifacts/manifest`
- `artifacts/grounding`
- `artifacts/idea_evaluation`

## Stable Usage Notes

- For open-source users, `idea_text` is the safest input mode for tasks that start from search.
- Task 1 and Task 3 CLI also accept `pdf_path`, but whether PDF-based retrieval is supported depends on the hosted API contract you are using.
- No task in this demo requires direct database access.
- For Task 1, GROBID is configured through `GROBID_BASE_URL` in `.env` unless you explicitly override it in task params.

## APIs Used By This Demo

- `POST /v1/search`
- `POST /v1/authors/related`
- `POST /v1/authors/support-papers`
- `POST /v1/authors/papers`

This demo does not require users to call lower-level retrieval endpoints directly.

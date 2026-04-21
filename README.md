<div align="center">
  <h1>InnoEval Open Demo</h1>
</div>
<p align="center">
  Open-source local client demo for running five literature-grounded downstream tasks on top of a hosted KG API.
</p>

This directory is the main runnable open-source demo for InnoEval.
It is a local client that:

- builds structured search plans locally with an LLM
- sends those plans to a hosted `KG2API` service
- performs local post-processing such as paper reranking, PDF parsing, grounding, and report generation

The goal of this README is practical: help you prepare the environment, configure all required dependencies, and successfully run the five downstream tasks.

`RUNNING.md` is kept in the repository for legacy reference, but this `README.md` is now the primary setup and usage guide.

## Table of Contents

- [What This Demo Does](#what-this-demo-does)
- [Tasks](#tasks)
- [Requirements Overview](#requirements-overview)
- [Installation](#installation)
- [Configuration](#configuration)
- [Run The Five Tasks](#run-the-five-tasks)
- [Outputs](#outputs)
- [TODO](#todo)

## What This Demo Does

The demo exposes one CLI entrypoint, [`run_demo.py`](/home/weiyunxiang/yunx/innoeval/open-source/demo/run_demo.py), and supports five downstream tasks:

1. `paper_grounding_compare`
2. `topic_trend_review`
3. `related_authors`
4. `author_research_profile`
5. `idea_generation`

For search-based tasks, the current open workflow is:

1. read `idea_text`, `topic_text`, or `pdf_path`
2. build a structured search `plan` locally with an LLM
3. call the hosted `KG2API`
4. continue task-specific local processing

Important behavior:

- The demo does not talk to Neo4j directly.
- The demo expects a hosted `KG2API` endpoint.
- Task 1 additionally performs local PDF resolution, local paragraph grounding, and local idea evaluation.
- PDF inputs are parsed locally through GROBID before the API call.

## Tasks

| Task | Task Type | Input | What it produces |
| --- | --- | --- | --- |
| 1 | `paper_grounding_compare` | `--idea-text` or `--pdf-path` | literature-grounded evidence, paragraph matches, and idea evaluation |
| 2 | `topic_trend_review` | `--topic-text` | chronological topic summary and representative papers |
| 3 | `related_authors` | `--idea-text` or `--pdf-path` | related authors and supporting papers |
| 4 | `author_research_profile` | `--author-name` | research trajectory summary for one author |
| 5 | `idea_generation` | `--topic-text` | generated research ideas grounded in retrieved papers |

## Requirements Overview

| Requirement | Task 1 | Task 2 | Task 3 | Task 4 | Task 5 |
| --- | --- | --- | --- | --- | --- |
| Python 3.10+ | Required | Required | Required | Required | Required |
| Hosted `KG2API` | Required | Required | Required | Required | Required |
| OpenAI-compatible LLM | Required | Required | Required | Required | Required |
| GROBID | Required | Not required | Only for `--pdf-path` | Not required | Not required |
| Local embedding model | Required | Not required | Not required | Not required | Not required |
| Local reranker model | Required | Not required | Not required | Not required | Not required |
| OpenAlex credentials | Optional but recommended | Not required | Optional for PDF-heavy flows | Not required | Not required |

## Installation

### 1. Enter This Directory

```bash
cd /data2/yunx/innoeval/open-source/demo
```

### 2. Create A Python Environment

`venv`:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

or `conda`:

```bash
conda create -n innoeval-demo python=3.10 -y
conda activate innoeval-demo
```

### 3. Install Python Dependencies

```bash
pip install -U pip
pip install -r requirements.txt
```

The demo depends on:

- `openai` for LLM calls
- `httpx` for the hosted API client
- `pdfplumber` for local PDF text extraction helpers
- `sentence-transformers` for Task 1 dense retrieval and reranking
- `scikit-learn` and `numpy` for local retrieval utilities

### 4. Start GROBID With Docker

GROBID is required for:

- Task 1
- Task 3 when you use `--pdf-path`

Pull and start the container:

```bash
docker pull lfoppiano/grobid:latest
docker run -d --rm \
  --name grobid \
  -p 8070:8070 \
  lfoppiano/grobid:latest
```

Check that it is alive:

```bash
curl http://127.0.0.1:8070/api/isalive
```

If GROBID is healthy, it should return a simple success response such as `true` or `alive`.

If port `8070` is already occupied, change the port mapping and then set the same value in `GROBID_BASE_URL`.

### 5. Download The Hugging Face Models Needed By Task 1

Task 1 grounding needs two local models:

- embedding model: `BAAI/bge-large-en-v1.5`
- reranker model: `BAAI/bge-reranker-large`

Install the Hugging Face CLI if you do not already have it:

```bash
pip install -U "huggingface_hub[cli]"
```

Recommended layout:

```bash
mkdir -p hf-models
```

Download the models:

```bash
huggingface-cli download BAAI/bge-large-en-v1.5 \
  --local-dir ./hf-models/BAAI--bge-large-en-v1.5

huggingface-cli download BAAI/bge-reranker-large \
  --local-dir ./hf-models/BAAI--bge-reranker-large
```

Why this path layout:

- the local grounding pipeline uses `demo/hf-models/BAAI--bge-large-en-v1.5` and `demo/hf-models/BAAI--bge-reranker-large` as its built-in default locations
- if you store the models there, Task 1 can run without explicitly passing model paths

If you want to store the models elsewhere, you can still do that, but then you should provide a Task 1 params file as shown below.

## Configuration

### 1. Create `.env`

Copy the example file:

```bash
cp .env.example .env
```

Then edit `.env` and fill in the values you actually use:

```env
KG2API_BASE_URL=https://your-api-host.example.com
KG2API_API_KEY=replace-me
KG2API_TIMEOUT=120

OPENAI_API_KEY=replace-me
OPENAI_BASE_URL=https://your-openai-compatible-endpoint/v1
OPENAI_MODEL=your-model-name

GROBID_BASE_URL=http://127.0.0.1:8070
OA_API_KEY=
OPENALEX_MAILTO=

# Optional. If omitted, Task 1 grounding derives
# {OPENAI_BASE_URL}/chat/completions automatically.
# GROUNDING_API_URL=https://your-openai-compatible-endpoint/v1/chat/completions
```

### 2. Understand Each Environment Variable

| Variable | Required For | Meaning |
| --- | --- | --- |
| `KG2API_BASE_URL` | all tasks | base URL of your hosted KG API |
| `KG2API_API_KEY` | all tasks | API key sent as `X-API-Key` |
| `KG2API_TIMEOUT` | all tasks | request timeout in seconds |
| `OPENAI_API_KEY` | all tasks | API key for the LLM used by planning, reranking, and summaries |
| `OPENAI_BASE_URL` | all tasks | OpenAI-compatible base URL, usually ending with `/v1` |
| `OPENAI_MODEL` | all tasks | chat model name |
| `GROBID_BASE_URL` | Task 1, Task 3 PDF mode | local or remote GROBID service URL |
| `OA_API_KEY` | optional | OpenAlex API key for PDF fallback acquisition |
| `OPENALEX_MAILTO` | optional | contact email sent to OpenAlex |
| `GROUNDING_API_URL` | optional | explicit chat completions URL for Task 1 grounding |

Configuration notes:

- `OPENAI_BASE_URL` should be the API base URL, not the full `/chat/completions` path.
- `GROUNDING_API_URL` is optional. If omitted, the code derives it automatically from `OPENAI_BASE_URL`.
- All five tasks need both the hosted KG API and an LLM.
- Task 4 does not use GROBID or local sentence-transformers models.

### 3. Optional: Prepare A Task 1 Params File

If your Task 1 models are not stored under the default `demo/hf-models/` paths, create a local params file.

Start from the example:

```bash
cp examples/task1_params.local.example.json examples/task1_params.local.json
```

Then edit it:

```json
{
  "embedding_model_path": "/absolute/path/to/your/bge-large-en-v1.5",
  "reranker_model_path": "/absolute/path/to/your/bge-reranker-large"
}
```

You can also set extra Task 1 controls there, for example:

- `grounding_device`
- `search_api_top_k`
- `search_final_top_k`
- `manifest_top_k`
- `dense_candidate_k`
- `grounding_final_top_k`
- `max_paragraphs_per_paper`

There is also a CPU-oriented example at [`examples/task1_params.cpu.local.json`](/home/weiyunxiang/yunx/innoeval/open-source/demo/examples/task1_params.cpu.local.json).

### 4. Recommended Pre-Run Checklist

Before you run any task, verify:

1. `.venv` or your conda environment is activated.
2. `curl http://127.0.0.1:8070/api/isalive` succeeds if you need GROBID.
3. `.env` contains valid `KG2API_*` and `OPENAI_*` values.
4. For Task 1, the local BGE models are present either in `demo/hf-models/` or in your Task 1 params file.

## Run The Five Tasks

All commands below assume you are already in:

```bash
cd /data2/yunx/innoeval/open-source/demo
source .venv/bin/activate
```

Add `--pretty` if you want formatted JSON on stdout.

### Task 1: `paper_grounding_compare`

Run with idea text:

```bash
python3 run_demo.py \
  --task-type paper_grounding_compare \
  --idea-text "Use literature-grounded evidence to evaluate research ideas." \
  --pretty
```

Run with a custom Task 1 params file:

```bash
python3 run_demo.py \
  --task-type paper_grounding_compare \
  --idea-text "Use literature-grounded evidence to evaluate research ideas." \
  --params-file examples/task1_params.local.json \
  --pretty
```

Run with a PDF input:

```bash
python3 run_demo.py \
  --task-type paper_grounding_compare \
  --pdf-path /absolute/path/to/paper.pdf \
  --params-file examples/task1_params.local.json \
  --pretty
```

Task 1 requires:

- valid `KG2API_*` settings
- valid `OPENAI_*` settings
- running GROBID
- local embedding model
- local reranker model

### Task 2: `topic_trend_review`

```bash
python3 run_demo.py \
  --task-type topic_trend_review \
  --topic-text "research idea evaluation with large language models" \
  --pretty
```

### Task 3: `related_authors`

Run with idea text:

```bash
python3 run_demo.py \
  --task-type related_authors \
  --idea-text "knowledge-grounded evaluation of scientific research ideas" \
  --pretty
```

Run with a PDF:

```bash
python3 run_demo.py \
  --task-type related_authors \
  --pdf-path /absolute/path/to/paper.pdf \
  --pretty
```

Notes:

- Task 3 supports both `--idea-text` and `--pdf-path`.
- GROBID is only needed when Task 3 uses `--pdf-path`.

### Task 4: `author_research_profile`

```bash
python3 run_demo.py \
  --task-type author_research_profile \
  --author-name "Geoffrey Hinton" \
  --pretty
```

### Task 5: `idea_generation`

```bash
python3 run_demo.py \
  --task-type idea_generation \
  --topic-text "scientific idea generation with retrieval-augmented large language models" \
  --pretty
```

### Request File Mode

You can also run the demo from request JSON files:

```bash
python3 run_demo.py --request-file examples/task2_request.json --pretty
python3 run_demo.py --request-file examples/task3_request.json --pretty
python3 run_demo.py --request-file examples/task4_request.json --pretty
python3 run_demo.py --request-file examples/task5_request.json --pretty
```

Task 1 request execution often still needs machine-specific model paths, so a local params file is usually the simplest approach.

## Outputs

Every run creates a new directory under `runs/` and writes:

- `request.json`
- `result.json`
- `result.md`

Typical behavior by task:

- Tasks 1, 2, and 5 write search artifacts under `artifacts/search/`
- Task 3 writes query-planning and author-support artifacts
- Task 4 writes author-profile artifacts
- Task 1 additionally writes `artifacts/manifest/`, `artifacts/grounding/`, and `artifacts/idea_evaluation/`

If you do not specify `--run-id`, the run directory name is generated automatically from timestamp, task type, and input summary.

## TODO

This open demo is still evolving. The main improvement directions are:

- CLI and agent skills: expose more KG retrieval and downstream capabilities as stable CLIs and package the best downstream task practices as reusable agent skills.
- Integrating more knowledge forms: extend beyond paper-centric knowledge to include datasets, code, standards, theorems, and other scientific artifacts with richer links between them.
- Benchmark and evaluation: build dedicated benchmarks and quantitative evaluation protocols for these downstream tasks instead of relying mainly on qualitative demo cases.
- Dynamic update: move from mostly manual or periodic updates toward more systematic and frequent KG refresh workflows.

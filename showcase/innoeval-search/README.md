# InnoEval Search Showcase

`innoeval-search` is the search showcase bundled under `demo/showcase/` for InnoEval.

The code in this directory is kept separate from the runnable open demo CLI in the repository root. It preserves the standalone search-oriented layout and can be set up independently when you want to inspect or run the search stack itself.

This directory is intended for two use cases:

- to make the current retrieval strategy readable as a standalone package
- to preserve a reference implementation of how the search stack is organized around KG, S2, merge, and reranking

The package keeps the current implementation boundary on purpose:

- the main public entry point is `run_combined_search`
- KG search still returns full paper records plus related authors
- the combined output keeps source payloads, deduplication details, and optional reranking artifacts

## What Is Runnable

`innoeval-search` contains both public-facing and environment-specific components.

Runnable in a normal open-source setup:

- Semantic Scholar keyword search from `--idea-text`
- Semantic Scholar PDF flows from `--pdf-path`
- cross-source deduplication logic
- optional LLM-based final reranking

Requires a separately prepared graph environment:

- KG retrieval through Neo4j
- the expected Cypher-compatible graph schema
- the expected fulltext and vector indexes

If you do not have the KG database, run the CLI with `--disable-kg`. This produces a clean S2-only result instead of a partial KG failure.

## Structure

```text
src/innoeval_search/
  combined/
  s2/
  kg/
  shared/
```

## Install

```bash
cd demo/showcase/innoeval-search
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[test]
cp .env.example .env
```

## Environment

Copy `.env.example` to `.env` and fill in only the values required for the flow you want to run.

### Shared LLM settings

These are used by:

- S2 keyword extraction
- KG query understanding
- KG PDF reference selection
- optional final reranking in the combined pipeline

Set:

```env
SEARCH_LLM_API_KEY=replace-me
SEARCH_LLM_API_URL=https://your-openai-compatible-endpoint/v1/chat/completions
SEARCH_LLM_MODEL=your-model-name
```

### Semantic Scholar settings

Required for any S2 flow:

```env
S2-API-KEY=replace-me
```

### KG settings

Required only when KG retrieval is enabled:

```env
NEO4J_URI=bolt://your-neo4j-host:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=replace-me
NEO4J_DATABASE=neo4j
```

You should also prepare the Cypher-side schema and indexes expected by the KG search path before running the combined KG flow.

### Local model settings

The KG path also needs embedding and reranker models. They can be configured either as local paths or model identifiers resolvable by `sentence-transformers`.

## Typical Commands

S2-only idea-text search, without KG:

```bash
innoeval-search \
  --idea-text "research idea evaluation with large language models" \
  --disable-kg \
  --disable-llm-ranking \
  --pretty
```

S2-only PDF search, with GROBID-enabled PDF extraction:

```bash
innoeval-search \
  --pdf-path /absolute/path/to/paper.pdf \
  --disable-kg \
  --s2-mode hybrid \
  --grobid-base-url http://127.0.0.1:8070 \
  --disable-llm-ranking \
  --pretty
```

Combined KG + S2 search, for environments that also have the graph:

```bash
innoeval-search \
  --idea-text "research idea evaluation with large language models" \
  --pretty
```

## Runtime Notes

- `--disable-kg` is the recommended mode for public users without the original Neo4j graph.
- `--disable-s2` is available when you want to inspect KG behavior in isolation.
- `--disable-llm-ranking` disables only the final reranking stage. S2 keyword extraction and KG understanding may still use the configured LLM.
- GROBID is needed only for PDF-based flows. Idea-text S2 search does not require GROBID.
- By default, result artifacts are written under `result/` and cache artifacts under `target/`.

## Python API

```python
from innoeval_search import run_combined_search
```

## Testing

After installation:

```bash
pytest -q
```

# Enterprise AI Operating System

An enterprise-grade AI backend built from scratch, focused on secure document intelligence, retrieval-augmented generation, conversational AI, and enterprise authorization.

## Tech Stack

- FastAPI
- PostgreSQL
- pgvector
- SQLAlchemy
- Alembic
- Pydantic
- Sentence Transformers
- Cross-Encoder reranking
- Ollama / local LLM inference
- Docker

## Current RAG Architecture

User Question
→ Hybrid Retrieval
→ Reranking
→ Evidence Sufficiency
→ Context Construction
→ Local LLM
→ Citations

## Current Capabilities

- JWT authentication
- Refresh tokens
- Database-backed RBAC
- Document upload and extraction
- Document chunking
- Vector embeddings
- pgvector similarity search
- PostgreSQL keyword search
- Hybrid retrieval with Reciprocal Rank Fusion
- Cross-encoder reranking
- Evidence sufficiency gating
- RAG citations
- Conversational chat
- Conversation history
- Active/inactive document filtering

## RAG Safety

The system evaluates retrieved evidence before allowing the request to reach the LLM.

When the evidence is insufficient, the system refuses to generate an unsupported answer.

Example:

> I don't have enough information to answer that question.

## Project Progress

### Day 1 — RAG Evidence Architecture

Completed:

- Hybrid retrieval
- Reranking
- Evidence sufficiency service
- Evidence-gated answer generation
- Unsupported-question refusal
- Conversation persistence after refusal
- Active-document filtering
- Removal of restrictive vector-distance cutoff
- RAG evaluation

Evaluation:

- True positives: 9/9
- False negatives: 0
- True negatives: 6/6
- False positives: 0

## Roadmap

This project is being developed incrementally over 45 focused engineering days.

Upcoming areas include:

- Query understanding
- Conversational query rewriting
- Retrieval optimization
- Metadata-aware retrieval
- Citation validation
- Automated RAG evaluation
- Background document processing
- Redis and workers
- Multi-tenancy
- Enterprise authorization
- Prompt-injection defense
- Observability
- Frontend
- Dockerized deployment
- Production hardening
# Enterprise AI OS

Enterprise AI OS is a document question-answering backend. Users authenticate, upload company documents, and ask questions answered from retrieved evidence with citations. Documents are shared within an organization; retrieval is scoped so one organization cannot search another organization's documents.

## MVP architecture

```text
Document upload → text extraction → chunking → embeddings → PostgreSQL/pgvector
Question → vector + keyword retrieval → reciprocal-rank fusion → reranking
         → evidence sufficiency check → local LLM → answer with citations
```

Authentication and role-based authorization protect API routes. PostgreSQL stores users, organizations, documents, chunks, conversations, and refresh-token state. Ollama runs the local language model. Sentence Transformers provide embeddings and reranking.

## Technology

- Python 3.13, FastAPI, Pydantic
- PostgreSQL 17 with pgvector, SQLAlchemy async, Alembic
- Sentence Transformers and a Cross-Encoder reranker
- Ollama with `qwen2.5:1.5b` by default
- Docker Compose
- TXT, DOCX, and PDF document extraction

## Run locally with Docker Desktop (Windows PowerShell)

Prerequisites: Docker Desktop, Git, and [Ollama](https://ollama.com/) installed on Windows. Start Ollama and download the configured model once:

```powershell
ollama pull qwen2.5:1.5b
```

From the repository root, prepare the backend's local environment file:

```powershell
Set-Location .\backend
Copy-Item .env.example .env
```

Open `backend/.env` and replace `JWT_SECRET_KEY` with a private random value. For example, generate one with:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Paste the generated value into `.env`. Keep `.env` private; Git ignores it. The example database username/password are for local development only. Do not use them for a public deployment or real sensitive data.

Create the named database volume if this is the first run, then build and start the stack:

```powershell
docker volume create backend_postgres_data
docker compose up -d --build
```

Compose starts PostgreSQL and waits for its health check. The backend then applies Alembic migrations before starting the API. The named volume persists database data across container rebuilds. Removing that volume deletes the stored database; do not remove it if you need the data.

On first startup, the backend downloads its Sentence Transformers embedding and reranking models from Hugging Face. This can delay API readiness; watch `docker compose logs -f backend` until model initialization finishes. The downloaded model cache is currently inside the container, so recreating the container can require downloading the models again.

Check the API health and open the interactive API documentation:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Start-Process http://127.0.0.1:8000/docs
```

### Create the first organization administrator

The application does not have public sign-up or an Admin choice on the sign-in page. Create the first administrator from the running backend's private console:

```powershell
docker compose exec backend python seed_rbac.py
```

The script prompts for the organization name, admin name, email, and a unique password of at least 16 characters. The password prompt does not echo the password, and the script never prints it. For the existing local demo database, use `Default Organization` as the organization name. Keep this admin password private. The admin can then create regular-user accounts from the Streamlit **Organization admin · Manage users** panel. Each new user must replace their temporary password with a personal password at first sign-in.

The sign-in page intentionally has no role selector: account roles are assigned by the system and cannot be selected by visitors. Regular users can use document Q&A, but only administrators can list or manage organization accounts.

The health endpoint confirms that the API process is responding. The Docs page lets you authenticate and exercise protected endpoints. The backend container reaches Ollama on the Windows host through `host.docker.internal`; keep Ollama running when asking questions.

### Run the Streamlit frontend

Keep the Docker Compose backend and Ollama running. From the repository root, create the frontend environment, install its dependencies, and start Streamlit:

```powershell
python -m venv .\frontend\.venv
& .\frontend\.venv\Scripts\Activate.ps1
python -m pip install -r .\requirements.txt
python -m streamlit run .\frontend\app.py
```

Open the local URL printed by Streamlit (usually `http://localhost:8501`). The frontend connects to the local API at `http://127.0.0.1:8000` by default. For a hosted frontend, configure `API_URL` using the hosting platform's secret settings; never commit a real `.streamlit/secrets.toml`.

Useful Compose commands (run inside `backend`):

```powershell
docker compose logs -f backend
docker compose ps
docker compose down
```

`docker compose down` stops and removes containers but preserves the named database volume.

## Run the automated tests

Create or activate the project's Python virtual environment, install `backend/requirements.txt`, and make sure the Docker PostgreSQL service is running. From the `backend` directory, point the test process at the host-mapped database port and run:

```powershell
$env:DATABASE_HOST = "localhost"
$env:DATABASE_PORT = "5433"
python -m pytest -q --ignore=test_docx_styles.py
```

The Windows host uses port `5433`; containers use the internal port `5432`. The ignored DOCX style test is excluded because of its environment-specific behavior. On October 24, 2026, this checkout's latest recorded result was **83 passed in 76.97 seconds**, with no warnings. See `TEST_RESULTS_OCT23.md` for the run record.

## Current MVP capabilities

- JWT access and refresh-token authentication
- Database-backed roles and permission checks
- Organization-scoped document listing and retrieval
- Upload and extraction for TXT, DOCX, and PDF
- Document chunking, embeddings, and pgvector storage
- PostgreSQL keyword search and vector search combined through reciprocal-rank fusion
- Cross-Encoder reranking
- Evidence sufficiency checks and refusal when retrieved evidence is insufficient
- Source citations with document and chunk metadata
- Conversations and chat history
- Active-document filtering
- Streamlit frontend for sign-in, organization-admin user management, document upload, search, document Q&A, passage and whole-document summaries, and saved conversations

## Current limitations

- This is a local MVP, not a production deployment. Production use needs deployment-specific secrets, infrastructure, access controls, backups, and operational review.
- New users inherit the organization of the user who creates them; self-service company onboarding and invitations are outside this MVP.
- Organization sharing is implemented; document deletion remains restricted to the uploader or an administrator.
- Retrieval is scoped to the caller's organization, not to a specific filename selected by the caller. Similar documents in one organization can compete for retrieval, and broad summary requests may be refused when evidence sufficiency is not met.
- `/health` reports API responsiveness; it does not independently verify database or Ollama health.

## Project status

This repository contains a locally runnable end-to-end MVP with a FastAPI backend, Streamlit frontend, PostgreSQL/pgvector storage, and Ollama-based generation. It is suitable for local demonstration and interview discussion, but has not had a production security audit or a public production deployment. Agent orchestration, background workers, production observability, and Kubernetes deployment remain future work.

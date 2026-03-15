# Jeopardy API

A REST API for playing Jeopardy trivia with AI-powered answer verification and autonomous AI agents.

---

## Prerequisites

- **Git**
- **Docker Desktop** (includes Docker Compose)
- **Gemini API key** — required for answer verification and AI agents

### Installing Git

| Platform | Command |
|----------|---------|
| macOS | `xcode-select --install` |
| Ubuntu/Debian | `sudo apt-get install git` |
| Windows | Download from [git-scm.com](https://git-scm.com/download/win) |

### Installing Docker

| Platform | Instructions |
|----------|-------------|
| macOS | Download [Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/) and install the `.dmg` |
| Windows | Download [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/). WSL 2 backend is recommended |
| Ubuntu/Debian | `sudo apt-get update && sudo apt-get install docker.io docker-compose-plugin` |
| Other Linux | Follow the [official guide](https://docs.docker.com/engine/install/) for your distro |

Verify both are installed:

```bash
git --version
docker --version
docker compose version
```

> **Linux note**: to run Docker without `sudo`, add your user to the docker group and
> re-login: `sudo usermod -aG docker $USER`

### Getting a Gemini API key

1. Go to [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Click **Create API key** and copy it
3. Paste it into your `.env` file as `GEMINI_API_KEY=...`

---

## Local development

```bash
git clone https://github.com/pavlenanenova/jeopardy.git
cd jeopardy
cp .env.example .env
# Add your GEMINI_API_KEY to .env
docker compose up --build
```

On first run Docker will:

1. Start a `postgres:16` database
2. Run Alembic migrations to create the schema
3. Download the Jeopardy CSV (~25 MB) and save it to a local volume
4. Ingest all questions with values up to `$1,200` into the database (~30 seconds)
5. Start the API on port `8000`

On subsequent runs the CSV download and ingestion are skipped automatically.

The API and interactive docs are available at:
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs

### Restarting after a code change

If you changed Python code only (not `requirements.txt`):
```bash
docker compose up api
```

If you changed `requirements.txt`:
```bash
docker compose up --build api
```

### Wiping all data and starting fresh

```bash
docker compose down -v
docker compose up --build
```

---

## API endpoints

### `GET /question/`

Returns a random question filtered by round and value.

| Parameter | Required | Values |
|-----------|----------|--------|
| `round` | Yes | `Jeopardy!`, `Double Jeopardy!`, `Final Jeopardy!` |
| `value` | No | `$200`, `$400`, `$600`, `$800`, `$1000`, `$1200`. Omit for Final Jeopardy! |

```bash
curl "http://localhost:8000/question/?round=Jeopardy!&value=%24200"
```

```json
{
  "question_id": 3,
  "round": "Jeopardy!",
  "category": "HISTORY",
  "value": "$200",
  "question": "For the last 8 years of his life, Galileo was under house arrest for espousing this man's theory"
}
```

### `POST /verify-answer/`

Checks whether a user's free-text answer is correct using AI. Handles spelling mistakes, partial answers, and phrases like "What is X".

```bash
curl -X POST "http://localhost:8000/verify-answer/" \
  -H "Content-Type: application/json" \
  -d "{\"question_id\": 3, \"user_answer\": \"Copernicus\"}"
```

```json
{
  "is_correct": true,
  "ai_response": "That is correct! Copernicus proposed the heliocentric model that Galileo championed."
}
```

### `POST /agent-play/`

An AI agent attempts to answer a random question. Skill level controls how often it gets the answer right.

| Skill level | Behaviour |
|-------------|-----------|
| `beginner` | Makes frequent mistakes |
| `intermediate` | Occasionally wrong |
| `expert` | Almost always correct |

```bash
curl -X POST "http://localhost:8000/agent-play/" \
  -H "Content-Type: application/json" \
  -d "{\"round\": \"Jeopardy!\", \"value\": \"\$200\", \"skill_level\": \"expert\"}"
```

```json
{
  "agent_name": "Master-Bot",
  "question": "Built in 312 B.C. to link Rome & the South of Italy, it's still in use today",
  "ai_answer": "What is the Appian Way?",
  "is_correct": true
}
```

---

## Environment variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | Yes | — | Gemini API key for AI features |
| `GEMINI_MODEL` | No | `gemini-2.5-flash-lite` | Gemini model to use for AI features |
| `GEMINI_VERIFIER_TEMPERATURE` | No | `0.2` | Temperature for answer verification (low = deterministic) |
| `GEMINI_BEGINNER_TEMPERATURE` | No | `1.0` | Temperature for Rookie-Bot (high = lots of mistakes) |
| `GEMINI_INTERMEDIATE_TEMPERATURE` | No | `0.7` | Temperature for AI-Bot (moderate = occasional mistakes) |
| `GEMINI_EXPERT_TEMPERATURE` | No | `0.3` | Temperature for Master-Bot (low = rarely wrong) |
| `GEMINI_TOP_P` | No | `1` | Nucleus sampling parameter (limits token probability distribution) |
| `GEMINI_TOP_K` | No | `1` | Top-K sampling (only consider top K most likely tokens) |
| `GEMINI_MAX_TOKENS` | No | `1000` | Maximum tokens per response |
| `POSTGRES_USER` | No | `jeopardy` | Database user |
| `POSTGRES_PASSWORD` | No | `jeopardy` | Database password |
| `POSTGRES_DB` | No | `jeopardy` | Database name |
| `DATABASE_URL` | No | `postgresql://jeopardy:jeopardy@db:5432/jeopardy` | Full connection string |
| `DATASET_URL` | No | (see `.env.example`) | URL to download the Jeopardy CSV |
| `DB_POOL_SIZE` | No | `5` | Number of persistent database connections |
| `DB_MAX_OVERFLOW` | No | `10` | Max extra connections above pool size |

---



## AI implementation note

Answer verification and the AI agent are implemented using the **Gemini API** (gemini-2.5-flash-lite). Gemini was chosen over OpenAI because it has a free tier, making the project easy to run without upfront cost.

### Generation config

The Gemini model uses skill-level specific temperatures to create realistic AI agents:

**Answer Verification (deterministic):**
- **Temperature 0.2** — Low randomness ensures consistent correct/incorrect judgments

**AI Agents (skill-based variability):**
- **Rookie-Bot: Temperature 1.0** — Maximum variation, makes frequent mistakes
- **AI-Bot: Temperature 0.7** — Moderate variation, occasionally wrong
- **Master-Bot: Temperature 0.3** — Low variation, rarely makes mistakes

**Sampling parameters:**
- **Top P/K = 1** — Only the highest probability tokens are selected
- **Max tokens = 1000** — Limits response length

All values are customizable via environment variables (see [Environment variables](#environment-variables) above).

### Retry strategy

Both CSV download and Gemini API calls use exponential backoff with up to 3 retries:
- First retry after 1 second
- Second retry after 2 seconds  
- Third retry after 4 seconds

This handles transient API failures gracefully without manual intervention.

Swapping to OpenAI requires only changing `app/services/ai_verifier.py` and `app/services/ai_agent.py` — the rest of the codebase is model-agnostic.

## Testing

Tests use pytest with an in-memory SQLite database — no running containers needed for the test database. AI service calls are mocked so no Gemini API key is required.

Run the full test suite inside the running api container:

```bash
docker compose exec api pytest -v
```

Or spin up a one-off container without starting the full stack:

```bash
docker compose run --rm api pytest -v
```

### Test structure

```
tests/
├── conftest.py             # shared fixtures: in-memory DB, test client, seeded data
├── services/
│   ├── test_ai_verifier.py # unit tests for the answer verification service
│   └── test_ai_agent.py    # unit tests for the AI agent service
└── routes/
    ├── test_question.py    # endpoint tests for GET /question/
    ├── test_answer.py      # endpoint tests for POST /verify-answer/
    └── test_agent.py       # endpoint tests for POST /agent-play/
```

## Deployment

### Single server with Docker

This is the recommended deployment for a single server. The setup is identical to local development except you use a real domain and add HTTPS via a reverse proxy.

**1. Set up a server**

Any Linux VPS works (DigitalOcean, Hetzner, AWS EC2, etc.). Install Docker:

```bash
sudo apt-get update && sudo apt-get install docker.io docker-compose-plugin
sudo usermod -aG docker $USER
```

**2. Clone and configure**

```bash
git clone https://github.com/pavlenanenova/jeopardy.git
cd jeopardy
cp .env.example .env
```

Edit `.env` and set a strong `POSTGRES_PASSWORD` and your `GEMINI_API_KEY`.

**3. Start the services**

```bash
docker compose up --build -d
```

**4. Add HTTPS with Caddy**

Install Caddy and create a `Caddyfile`:

```
your-domain.com {
    reverse_proxy localhost:8000
}
```

Start Caddy:

```bash
caddy start
```

Caddy automatically provisions a free TLS certificate via Let's Encrypt.

### Using a managed database (optional)

To use a managed Postgres instance (Supabase, Railway, AWS RDS, etc.) instead of the Docker container:

1. Update `DATABASE_URL` in `.env` with the managed database connection string
2. Comment out the `db` service in `docker-compose.yml`
3. Run `docker compose up --build -d`

---

## Stopping and cleanup

```bash
# Stop containers, preserve data
docker compose down

# Stop containers and delete all data (database + CSV)
docker compose down -v
```
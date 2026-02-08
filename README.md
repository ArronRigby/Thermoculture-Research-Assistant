# Thermoculture Research Assistant

A web-based research tool for studying UK climate discourse and lived experiences with climate change. This application collects, analyzes, and organizes climate-related discussions to support research into "thermoculture" — how people in the UK experience, discuss, and adapt to climate change in their daily lives.

## Features

### Data Collection
- **Web scraping** from UK news sources (BBC News, The Guardian, regional newspapers)
- **Reddit API** integration for UK climate subreddits
- **Manual entry** for field research and additional sources
- **Automated scheduling** with configurable collection intervals
- **Deduplication** to avoid storing repeated content

### NLP Analysis
- **Sentiment analysis** with climate-specific lexicon adjustments
- **Theme extraction** using TF-IDF and topic modeling (LDA)
- **Discourse classification**: practical adaptation, emotional response, policy discussion, community action, denial/dismissal
- **Geographic entity recognition** for UK locations
- **Word frequency** and n-gram analysis

### Visualizations & Insights
- **Geographic heat map** showing climate discussion distribution across UK regions (Leaflet)
- **Temporal trends** with configurable granularity (daily/weekly/monthly)
- **Theme frequency charts** and word cloud displays
- **Sentiment distribution** and sentiment-over-time analysis
- **Discourse type breakdown** with example quotes

### Research Workspace
- **Markdown note editor** with preview
- **Quote library** with citation generation (APA, MLA, Chicago)
- **Sample linking** — connect notes to specific discourse samples
- **Export** research data in CSV or JSON format

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend API | Python 3.11+, FastAPI, SQLAlchemy (async) |
| Database | PostgreSQL 15+ |
| Task Queue | Celery + Redis |
| NLP | spaCy, scikit-learn, VADER sentiment |
| Frontend | React 18 + TypeScript, Vite, TailwindCSS |
| Visualizations | Recharts, Leaflet (react-leaflet) |
| Infrastructure | Docker, Docker Compose |

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Git

### Launch

```bash
# Clone the repository
git clone <repo-url>
cd thermoculture-research-assistant

# Start all services
docker compose up --build
```

The application will be available at:
- **Frontend**: http://localhost:5173
- **API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **API Docs (ReDoc)**: http://localhost:8000/redoc

### Seed the Database

```bash
# Run the seed script to populate with test data
docker compose exec backend python -m seeds.run_seed
```

This creates:
- 1 test user (researcher@thermoculture.ac.uk / research2024)
- 25 UK locations
- 10 data sources
- 12 climate themes
- 60+ discourse samples with sentiment analysis, classifications, and theme tags
- 2 sample research notes

## Project Structure

```
thermoculture-research-assistant/
├── backend/
│   ├── app/
│   │   ├── api/            # FastAPI route handlers
│   │   ├── core/           # Config, database, security
│   │   ├── models/         # SQLAlchemy ORM models
│   │   ├── schemas/        # Pydantic validation schemas
│   │   ├── services/       # Celery tasks and services
│   │   └── main.py         # FastAPI application entry
│   ├── collectors/         # Data collection modules
│   │   ├── news_collector.py
│   │   ├── reddit_collector.py
│   │   ├── pipeline.py     # Ingestion pipeline
│   │   └── scheduler.py    # Collection job scheduler
│   ├── nlp/                # NLP analysis engine
│   │   ├── sentiment.py    # Sentiment analysis
│   │   ├── classifier.py   # Discourse classification
│   │   ├── theme_extractor.py
│   │   ├── geographic.py   # UK location extraction
│   │   └── analyzer.py     # Analysis orchestrator
│   ├── migrations/         # Alembic database migrations
│   ├── seeds/              # Test data seeders
│   ├── tests/              # Pytest test suite
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/            # API client and endpoints
│   │   ├── components/     # Reusable React components
│   │   ├── hooks/          # Custom React hooks
│   │   ├── pages/          # Page-level components
│   │   └── types/          # TypeScript type definitions
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
├── .env
└── README.md
```

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/auth/register | Register new user |
| POST | /api/v1/auth/login | Login (returns JWT) |

### Sources
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/v1/sources/ | List all sources |
| POST | /api/v1/sources/ | Create source |
| GET | /api/v1/sources/{id} | Get source details |
| PUT | /api/v1/sources/{id} | Update source |
| DELETE | /api/v1/sources/{id} | Delete source |

### Discourse Samples
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/v1/samples/ | List samples (paginated, filterable) |
| POST | /api/v1/samples/ | Create manual entry |
| GET | /api/v1/samples/{id} | Get sample with metadata |
| DELETE | /api/v1/samples/{id} | Delete sample |
| GET | /api/v1/samples/{id}/analysis | Get analysis results |

### Analysis
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/v1/analysis/sentiment-over-time | Sentiment trends |
| GET | /api/v1/analysis/theme-frequency | Theme counts |
| GET | /api/v1/analysis/geographic-distribution | Regional distribution |
| GET | /api/v1/analysis/discourse-types | Classification breakdown |
| GET | /api/v1/analysis/trending-themes | Recent trending themes |
| GET | /api/v1/analysis/timeline | Volume over time |

### Research Notes
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/v1/notes/ | List user's notes |
| POST | /api/v1/notes/ | Create note |
| GET | /api/v1/notes/{id} | Get note |
| PUT | /api/v1/notes/{id} | Update note |
| DELETE | /api/v1/notes/{id} | Delete note |
| POST | /api/v1/notes/{id}/link-sample/{sample_id} | Link sample |
| POST | /api/v1/notes/{id}/unlink-sample/{sample_id} | Unlink sample |

### Export
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/v1/export/samples?format=csv\|json | Export samples |
| GET | /api/v1/export/notes | Export notes |

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| DATABASE_URL | PostgreSQL connection string | postgresql+asyncpg://postgres:postgres@db:5432/thermoculture |
| REDIS_URL | Redis connection string | redis://redis:6379/0 |
| SECRET_KEY | JWT signing key | (change in production) |
| REDDIT_CLIENT_ID | Reddit API client ID | (optional) |
| REDDIT_CLIENT_SECRET | Reddit API secret | (optional) |
| REDDIT_USER_AGENT | Reddit API user agent | thermoculture-research-assistant/1.0 |

### Reddit API Setup (Optional)
1. Create a Reddit application at https://www.reddit.com/prefs/apps
2. Select "script" type
3. Copy client ID and secret to .env file

## Running Tests

```bash
# Run all tests
docker compose exec backend pytest

# Run with coverage
docker compose exec backend pytest --cov=app --cov=nlp --cov=collectors

# Run specific test files
docker compose exec backend pytest tests/test_api.py
docker compose exec backend pytest tests/test_nlp.py
```

## Development

### Backend (without Docker)
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python -m spacy download en_core_web_sm
uvicorn app.main:app --reload
```

### Frontend (without Docker)
```bash
cd frontend
npm install
npm run dev
```

## Research Use Cases

1. **Discourse Pattern Analysis**: Identify how UK climate discourse varies by region, time, and source type
2. **Sentiment Tracking**: Monitor shifts in public sentiment toward climate change over time
3. **Lived Experience Documentation**: Collect and categorize first-person accounts of climate adaptation
4. **Policy Response Analysis**: Track how policy discussions differ from lived experience accounts
5. **Geographic Comparison**: Compare climate discourse across UK regions

## License

This project is for academic research purposes.

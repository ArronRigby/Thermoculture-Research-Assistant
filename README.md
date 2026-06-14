# Thermoculture Research Assistant

A web-based research tool for studying UK climate discourse and lived experiences with climate change. This application collects, analyzes, and organizes climate-related discussions to support research into "thermoculture" — how people in the UK experience, discuss, and adapt to climate change in their daily lives.

## Features

### Data Collection
- **Web scraping** from UK news sources (BBC News, The Guardian, regional newspapers)
- **Reddit API** integration for UK climate subreddits
- **Manual entry** for field research and additional sources
- **Deduplication** to avoid storing repeated content

### NLP Analysis
- **Sentiment analysis** with climate-specific lexicon adjustments
- **Theme extraction** using TF-IDF keywords
- **Discourse classification**: practical adaptation, emotional response, policy discussion, community action, denial/dismissal
- **Geographic location extraction** for UK locations via a built-in gazetteer

### Visualizations & Insights
- **Geographic heat map** showing climate discussion distribution across UK regions (Leaflet)
- **Temporal trends** with configurable granularity (daily/weekly/monthly)
- **Theme frequency charts** and co-occurrence matrices
- **Sentiment distribution** and sentiment-over-time analysis
- **Discourse type breakdown** with example quotes

### Research Workspace
- **Markdown note editor** with preview
- **Quote library** with citation generation (APA, Chicago, MLA 9)
- **Sample linking** — connect notes to specific discourse samples
- **Export** research data in CSV or JSON format

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend API | Python 3.10.x, FastAPI, SQLAlchemy (async) |
| Database | SQLite (via aiosqlite) |
| NLP | scikit-learn, VADER sentiment |
| Frontend | React 18 + TypeScript, Vite, TailwindCSS |
| Visualizations | Recharts, Leaflet (react-leaflet) |
| Infrastructure | Docker, Docker Compose |

> [!NOTE]
> SQLite is the default database. Schema tables are created dynamically at application startup via `Base.metadata.create_all` (no Alembic migrations are used). Any manual schema modifications during development require recreating the database file.

## Quick Start

### Prerequisites
- Python 3.10.x
- Node.js 20+
- Git

### Launch (Local Development)

The easiest way to start both the backend and frontend concurrently is by using the provided batch file:

```bash
run_app.bat
```

Alternatively, you can start the services manually:

**Backend API:**
1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Unix/macOS:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the seed script (this creates the database tables and populates seed data):
   ```bash
   python -m seeds.run_seed
   ```
5. Start the FastAPI development server:
   ```bash
   uvicorn app.main:app --reload
   ```

**Frontend React App:**
1. Navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run the Vite development server:
   ```bash
   npm run dev
   ```

The application will be available at:
- **Frontend**: http://localhost:5173
- **API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **API Docs (ReDoc)**: http://localhost:8000/redoc

### Seeding the Database

To populate the database with test data, run the seed script from the `backend` directory. The seed script dynamically creates all tables and prints the generated credentials for the test user upon completion:

```bash
cd backend
python -m seeds.run_seed
```

### Docker Launch (Secondary option)

You can launch a trimmed stack using Docker Compose:

```bash
docker compose up --build
```

This runs both the frontend and backend containers. The backend mounts the local directory to persist the SQLite database.

## Project Structure

```
thermoculture-research-assistant/
├── backend/
│   ├── app/
│   │   ├── api/            # FastAPI route handlers
│   │   ├── core/           # Config, database, security
│   │   ├── models/         # SQLAlchemy ORM models
│   │   ├── schemas/        # Pydantic validation schemas
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
│   │   └── analyzer.py     # Analysis orchestrator
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
| GET | /api/v1/auth/me | Get current user details |

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

### Analysis & Insights
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/v1/analysis/sentiment-over-time | Sentiment trends |
| GET | /api/v1/analysis/geographic-distribution | Regional distribution |
| GET | /api/v1/analysis/discourse-types | Classification breakdown |
| GET | /api/v1/analysis/trending-themes | Recent trending themes |
| GET | /api/v1/analysis/timeline | Volume over time |
| GET | /api/v1/analysis/sentiment-distribution | Sentiment histogram |
| GET | /api/v1/analysis/map-locations | Leaflet map markers |
| GET | /api/v1/analysis/theme-frequencies | Theme counts |
| GET | /api/v1/analysis/theme-co-occurrence | Co-occurrence matrix |

### Research Notes
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/v1/notes/ | List user's notes |
| POST | /api/v1/notes/ | Create note |
| GET | /api/v1/notes/{id} | Get note details |
| PUT | /api/v1/notes/{id} | Update note |
| DELETE | /api/v1/notes/{id} | Delete note |
| POST | /api/v1/notes/{id}/link-sample/{sample_id} | Link sample to note |
| POST | /api/v1/notes/{id}/unlink-sample/{sample_id} | Unlink sample from note |

### Quote Library
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/v1/quotes/ | List user's saved quotes |
| POST | /api/v1/quotes/ | Save a quote |
| DELETE | /api/v1/quotes/{quote_id} | Delete a saved quote |

### Export
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/v1/export/samples?format=csv\|json | Export samples |
| GET | /api/v1/export/notes | Export notes |

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| DATABASE_URL | SQLite connection URL | sqlite+aiosqlite:///./thermoculture.db |
| SECRET_KEY | JWT signing key | (change in production) |
| REDDIT_CLIENT_ID | Reddit API client ID | (optional) |
| REDDIT_CLIENT_SECRET | Reddit API secret | (optional) |
| REDDIT_USER_AGENT | Reddit API user agent | ThermocultureResearchBot/1.0 |

## Running Tests

```bash
# Navigate to backend and run all tests
cd backend
venv\Scripts\python -m pytest
```

## License

This project is for academic research purposes.

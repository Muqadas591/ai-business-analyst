
# AI Business Analyst

An AI-assisted business analytics platform for turning CSV and Excel
data into validated datasets, interactive analysis, evidence-backed
business insights, and professional reports.

> Status: Phase 0 — product specification and repository foundation.

## Problem

Business users often spend significant time cleaning spreadsheets,
calculating KPIs, exploring trends, and preparing management reports.

AI Business Analyst is designed to bring these activities into one
auditable workflow while keeping numeric calculations deterministic.

## Planned workflow

Upload
-> Validate
-> Clean
-> Explore
-> Visualize
-> Analyze with AI
-> Recommend actions
-> Export PDF and Excel

## Planned capabilities

- CSV and Excel ingestion
- Data quality profiling and validation
- Auditable data cleaning
- KPI calculations and exploratory data analysis
- Interactive Plotly visualizations
- Evidence-grounded AI recommendations
- PDF and Excel report generation
- Multi-user workspaces and access control
- Automated tests and continuous integration

## Technology

- Python
- Pandas and NumPy
- Pandera and Pydantic
- Streamlit and Plotly
- FastAPI
- PostgreSQL
- Hosted LLM API
- Google Colab for AI experiments
- pytest and Ruff
- GitHub Actions

## Architecture principles

1. Deterministic calculations are the source of truth.
2. AI explains calculated evidence; it does not invent metrics.
3. Data cleaning is explicit and auditable.
4. Workspace access is enforced on the server.
5. Uploaded files are untrusted input.
6. AI is optional; standard analytics must remain available.
7. No local AI model or GPU is required.

## Project status

The repository is being developed in phases.

| Phase | Scope | Status |
|---|---|---|
| 0 | Specification and repository foundation | In progress |
| 1 | Data ingestion | Planned |
| 2 | Data validation | Planned |
| 3 | Cleaning and audit | Planned |
| 4 | Analytics and KPIs | Planned |
| 5 | Dashboard | Planned |
| 6 | AI insight engine | Planned |
| 7 | Reports | Planned |
| 8 | API integration | Planned |
| 9 | Hardening and QA | Planned |
| 10 | Deployment and portfolio launch | Planned |

## Development setup

Requires Python 3.12 and Git.

Create a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install development dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Run quality checks:

```powershell
python -m ruff check .
python -m ruff format --check .
python -m pytest
```

## AI experiments

AI model experiments will run in Google Colab. Production AI inference
will use a configured hosted provider. No local AI model is required.

See [notebooks/README.md](notebooks/README.md).

## Security and privacy

Use synthetic data in this public repository. Never commit credentials,
private datasets, employer code, or confidential reports.

See [docs/SECURITY.md](docs/SECURITY.md).

## Documentation

- [Product requirements](docs/PRD.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Security and privacy](docs/SECURITY.md)

## License

See [LICENSE](LICENSE).

## Disclaimer

This project is a software analytics tool, not a substitute for
professional financial, legal, or operational judgment. AI-generated
recommendations require review and should be supported by available data.


# Architecture

## 1. Architectural style

Begin with a modular monolith, separating the UI, API, domain logic,
data processing, AI integration, persistence, and reporting.

Avoid microservices until there is a measured operational need.

## 2. Main components

### Presentation
Streamlit UI for upload, quality review, analytics, charts, and exports.

### API
FastAPI endpoints for authentication integration, workspace-scoped
resources, pipeline execution, and report downloads.

### Ingestion
Controlled CSV/XLSX parsing with resource limits and normalized results.

### Validation and cleaning
Explicit validation rules, quality reports, user-approved transformations,
and an auditable transformation history.

### Analytics
Deterministic calculations for descriptive statistics, KPIs, trends,
segments, and outlier indicators.

### AI service
Provider abstraction, bounded evidence payloads, structured outputs,
timeouts, retries, cost controls, and graceful fallback.

### Reporting
PDF and Excel generators using the same analysis result models.

### Persistence
PostgreSQL for users, workspaces, dataset metadata, analysis jobs,
audit events, and report metadata.

### Object storage
Private storage for uploaded files and generated artifacts.

## 3. Multi-tenant security

Every protected resource must have an ownership or workspace relationship.

The server must authorize the current user for the requested workspace
before accessing its records, files, analysis jobs, or reports.

Never trust a client-supplied workspace ID as authorization.

Apply least-privilege database access and consider PostgreSQL row-level
security as an additional control.

## 4. Data flow

Upload
-> file checks
-> parsing
-> validation
-> cleaning preview
-> approved transformations
-> deterministic analytics
-> optional AI analysis
-> report generation
-> authorized download

## 5. AI boundary

The analytics layer calculates values.

The AI layer receives a minimized structured summary and produces
candidate explanations and recommendations.

Validate the response against a schema and verify that referenced
evidence exists in the analysis result.

## 6. Failure handling

AI provider unavailable:
Return deterministic analytics without AI insights.

Invalid file:
Reject it with a safe, actionable error.

Report failure:
Record the failure and allow a controlled retry.

Unauthorized resource:
Return an appropriate authorization error without exposing data.

## 7. Deployment

Deploy the UI and API in an architecture supported by the chosen host.
Use managed PostgreSQL and private object storage when required.

Store credentials in platform-managed secrets.

Use health checks, structured logs, resource limits, and CI.

## 8. Architectural evolution

Add background jobs for long-running analyses when synchronous processing
becomes unreliable.

Add caching only when invalidation and workspace isolation are defined.

Add more AI providers through the provider interface rather than coupling
business logic to a single vendor.

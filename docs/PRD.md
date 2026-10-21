
# Product Requirements Document

## 1. Product

AI Business Analyst

## 2. Problem

Business users spend time validating, cleaning, analyzing, and reporting
on CSV and Excel datasets. Manual workflows are repetitive and may
produce inconsistent calculations or unsupported conclusions.

## 3. Vision

Provide a secure workspace where business users can turn tabular data
into reproducible analytics, evidence-backed insights, and professional
reports.

## 4. Target users

- Business analysts
- Operations managers
- Sales and finance analysts
- Small and medium-sized businesses
- Data professionals who prepare recurring reports

## 5. Primary workflow

1. Authenticate and select a workspace.
2. Upload a CSV file or Excel workbook.
3. Validate the file and inspect data quality.
4. Preview and approve cleaning transformations.
5. Calculate descriptive statistics and business KPIs.
6. Explore interactive visualizations.
7. Request AI-assisted analysis.
8. Review evidence and limitations.
9. Export PDF and Excel reports.

## 6. Functional requirements

FR-01: Support CSV and XLSX ingestion.

FR-02: Enforce upload size, row, column, and parsing limits.

FR-03: Report missing values, duplicate records, type problems,
and other applicable quality issues.

FR-04: Provide explicit, configurable cleaning operations.

FR-05: Record cleaning actions and before/after statistics.

FR-06: Calculate metrics using deterministic Python functions.

FR-07: Generate interactive charts and segment comparisons.

FR-08: Generate AI insights from a bounded, structured evidence summary.

FR-09: Distinguish verified findings from hypotheses and limitations.

FR-10: Export consistent PDF and Excel reports.

FR-11: Require authorization for protected resources.

FR-12: Enforce workspace-level isolation for datasets, analyses,
reports, and associated jobs.

FR-13: Handle unavailable AI providers without breaking basic analytics.

FR-14: Provide health checks, structured errors, logs, and automated tests.

## 7. Non-functional requirements

Security:
- No secrets in source control.
- Server-side authorization on every protected operation.
- Private file storage.
- Input validation and resource limits.
- Safe handling of temporary files.

Reliability:
- Deterministic analytics for the same data and configuration.
- Clear error responses and recoverable failures.
- No silent data-cleaning operations.

Maintainability:
- Modular Python package.
- Typed interfaces and documented public functions.
- Automated tests and continuous integration.

Performance:
- Establish benchmark datasets and latency targets.
- Avoid unbounded file reads and synchronous long-running requests.
- Introduce background jobs when workload requires them.

Privacy:
- Do not send raw datasets to the AI provider by default.
- Minimize the information sent to external services.
- Document retention and deletion behavior.

## 8. AI principles

- Python is the source of truth for calculated metrics.
- AI explanations must reference computed evidence.
- Correlation must not be described as causation.
- Unsupported claims must be identified or omitted.
- AI failure must not disable non-AI analytics.
- Provider, model, prompt version, and evaluation results
  should be traceable where appropriate.

## 9. Initial release acceptance criteria

- A user can upload a supported synthetic CSV or XLSX dataset.
- Invalid files receive controlled and understandable errors.
- Data quality issues are inspectable.
- Cleaning operations are explicit and auditable.
- KPI calculations pass known-answer tests.
- Charts use the calculated results.
- AI insights can be disabled and are validated when enabled.
- PDF and Excel exports agree with the underlying analysis.
- Users cannot access another workspace's resources.
- CI runs the automated test suite successfully.
- Setup and deployment instructions are reproducible.

## 10. Out of scope

- Direct production banking or ERP integration.
- Autonomous execution of business transactions.
- Custom foundation-model training.
- Guaranteed causal inference.
- Enterprise SSO and billing in the initial release.

## 11. Success measures

Measure:
- Successful ingestion rate on the test corpus.
- Validation and cleaning correctness.
- KPI agreement with expected values.
- AI evidence-grounding and schema-validity rates.
- Report consistency.
- Cross-workspace authorization test results.
- Pipeline latency and memory use at documented dataset sizes.

Numerical service-level targets will be set after baseline measurements.

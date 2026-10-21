
# Security and Privacy

## Data handling

- Use synthetic datasets for the public demonstration.
- Do not commit real customer, financial, banking, or employer data.
- Keep uploads and reports in private storage.
- Apply configured file-size, row, column, and processing limits.
- Do not execute uploaded code, macros, or spreadsheet formulas.
- Treat uploaded content as untrusted input.
- Avoid logging file contents, credentials, or personal information.

## Authentication and authorization

- Use a well-supported identity solution.
- Validate authentication on the server.
- Enforce workspace membership for every protected operation.
- Protect dataset, analysis, and report endpoints independently.
- Test attempts to access resources from another workspace.
- Never use a client-provided identifier as proof of ownership.

## Secrets

- Keep .env out of Git.
- Use .env.example only for placeholders.
- Use hosted secret management in production.
- Rotate credentials if exposure is suspected.
- Do not put secrets into notebooks or screenshots.

## AI privacy

- AI is disabled until a provider is configured.
- Do not send raw datasets by default.
- Send only the minimum necessary structured evidence.
- Review the provider's retention and data-use terms before production use.
- Enforce output validation, timeouts, and cost limits.
- Treat model output as untrusted data.

## Files and exports

- Store files outside public web roots.
- Generate server-controlled filenames.
- Verify authorization before downloads.
- Define retention and deletion policies.
- Ensure temporary files are cleaned up.
- Treat CSV formula injection and spreadsheet content as potential risks.

## Incident response

Document how to:
1. Disable AI provider access.
2. Revoke exposed credentials.
3. Investigate security-relevant logs.
4. Remove affected files and artifacts.
5. Notify affected parties when required.
6. Restore service safely.

## Production readiness

This document defines planned controls. It does not claim that the
controls are implemented until their implementation and tests are complete.

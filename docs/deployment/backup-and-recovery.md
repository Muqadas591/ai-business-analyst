# AI Business Analyst — Backup and Recovery Runbook

## 1. Purpose

This document describes how to prepare for database failures, failed deployments, accidental data loss, and unsuccessful schema migrations.

## 2. Data That Must Be Protected

Protect the following application data:

- Application user accounts and password hashes.
- Workspace records and membership records.
- Dataset metadata and associated records.
- Any persistent analysis results, audit records, or application data stored in the database.
- Required application configuration, excluding secrets from source control.

Uploaded files and generated reports must also be included in the recovery plan if they are stored outside the database.

## 3. Before a Deployment

1. Confirm that the automated test suite passes.
2. Verify the current Alembic revision.
3. Create a database backup using the database provider's supported backup mechanism.
4. Confirm that the backup completed successfully.
5. Record the current application release and database revision.
6. Review pending migrations before applying them.
7. Never run destructive database operations against production without a verified recovery path.

## 4. Database Backup

For a managed PostgreSQL deployment:

1. Identify the provider's backup and restore capabilities.
2. Enable automated backups if the selected plan supports them.
3. Determine the backup retention period.
4. Create an additional backup before significant schema changes when supported.
5. Restrict backup access to authorized administrators.
6. Never commit database dumps or credentials to Git.

For a local development database, use the database's appropriate backup utility. Do not assume that copying a database file is a valid backup method for every database engine.

## 5. Restore Procedure

1. Stop application writes if necessary.
2. Identify the latest verified backup from before the incident.
3. Restore the backup to a separate database or recovery environment first, when possible.
4. Verify that the restored database contains the expected tables and records.
5. Confirm the Alembic revision of the restored database.
6. Run the application's database connectivity and smoke tests.
7. Verify authentication, workspace isolation, dataset access, and report generation.
8. Switch the application to the recovered database only after verification.
9. Document the incident and any data loss.

Never restore a backup over the only remaining copy of a database before validating the recovery process.

## 6. Failed Migration Recovery

1. Record the current database revision and deployment error.
2. Check whether the migration was committed successfully.
3. Inspect the database schema and migration history.
4. Restore from backup if necessary.
5. Prefer a tested forward migration when appropriate.
6. Do not manually change the Alembic revision marker to hide a schema mismatch.
7. Re-run schema checks and tests before resuming normal writes.

## 7. Deployment Rollback

Rolling back application code does not necessarily roll back database changes.

Use backward-compatible schema changes wherever practical. If a migration is destructive or incompatible with the previous application version, use a separately tested recovery plan before deploying.

## 8. Verification Checklist

- [ ] A backup exists.
- [ ] Backup access is restricted.
- [ ] The backup date and database revision are recorded.
- [ ] The restore procedure is documented.
- [ ] A test restore has been performed where the hosting plan allows it.
- [ ] Application tests pass after recovery.
- [ ] Authentication and workspace isolation work after recovery.
- [ ] No credentials or database dumps are committed to Git.

## 9. Known Limitations

Backup availability, retention, point-in-time recovery, and restore permissions depend on the selected database provider and hosting plan. These capabilities must be confirmed before production deployment.
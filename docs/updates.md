# Updates & Rollbacks

The `update.sh` script handles zero-downtime updates with automatic database backups.

```bash
# Update to the latest release tag
./scripts/update.sh

# Update to a specific version
./scripts/update.sh v0.2.0

# Check for available updates without applying
./scripts/update.sh --check

# List all available release versions
./scripts/update.sh --list

# Roll back to the previously deployed version
./scripts/update.sh --rollback
```

**What the script does:**

1. Creates a compressed PostgreSQL backup (`backups/*.sql.gz`, last 5 retained)
2. Fetches release tags from GitHub
3. Checks out the target version
4. Rebuilds and restarts Docker containers
5. Waits for the backend health check (Alembic migrations run automatically in `entrypoint.sh`)
6. Records the deployed version in `.deploy-version` for future rollback

> For updating a specific isolated instance (production, demo, staging), see [Multi-Instance Deployment](./multi-instance.md#updating-a-specific-instance).
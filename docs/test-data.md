# Generating Test Data

To see charts and tables in action before real donations arrive, seed the database with demo transactions:

```bash
# Generate 150 random transactions for a test fund
./scripts/test-data.sh --count=150

# Use with the dev environment
./scripts/test-data.sh --dev --count=100

# Seed multi-wallet demo data (3 wallets × 2 funds + transactions)
./scripts/test-data.sh --multi
```

The script creates a test fund if none exists and appends new rows on every run — existing data is never deleted.
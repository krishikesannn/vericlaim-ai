# Local data directory

This directory is intentionally excluded from Git because it can contain:

- the Kaggle vehicle-insurance image dataset;
- customer-uploaded evidence;
- the local SQLite account, claim and Claim Passport store; and
- derived caches that can be regenerated.

Download the public training dataset with:

```bash
python scripts/download_dataset.py --output data
```

Never commit insurer, claimant, policy or uploaded-evidence data. The demo
creates its local database automatically when `server.py` starts.


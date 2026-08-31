# Repository structure

```text
vericlaim-ai/
|-- app/static/              Browser application and portal UI
|-- assets/                  Architecture and presentation assets
|-- data/                    Local-only dataset, evidence and SQLite state
|-- docs/                    Architecture, model card and operating guides
|-- models/                  Runtime artifacts and experiment metrics
|-- output/                  Curated notebook, final deck and comparison data
|-- scripts/                 Dataset, documentation and deployment utilities
|-- src/vericlaim/           Feature, model, training and validation packages
|-- tests/                   Automated unit and evidence-matching tests
|-- server.py                Local web/API entry point
|-- Dockerfile               Container build
|-- azure.yaml               Azure deployment configuration
|-- pyproject.toml           Python package metadata
|-- requirements*.txt        Runtime and deep-learning dependencies
`-- .github/workflows/       Continuous-integration test workflow
```

## Version-control policy

Source, tests, documentation, metric reports, the final notebook, final deck
and the two demo runtime model directories are versioned. Personal data,
datasets, caches, environments, logs, temporary render files, duplicate decks
and experimental fold checkpoints are not versioned.

This policy keeps a clone runnable while avoiding accidental publication of
claimant evidence and avoiding a repository dominated by reproducible binary
checkpoints.


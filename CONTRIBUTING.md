# Contributing

1. Create a focused branch and keep changes scoped to one concern.
2. Do not commit datasets, customer evidence, local databases or credentials.
3. Run the tests before opening a pull request:

   ```bash
   PYTHONPATH=src python -m unittest discover -s tests -v
   ```

4. For model changes, report the split protocol, threshold-selection method,
   confusion matrix, fraud precision/recall/F1, PR-AUC and calibration metric.
5. Do not promote a challenger unless it improves the leakage-aware validation
   criteria documented in `docs/model_card.md`.
6. Keep the user-facing result framed as investigation support, never proof of
   fraud or an automatic claim decision.


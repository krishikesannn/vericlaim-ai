# VeriClaim AI - Frontend Developer Packet

This folder is the learning and reference workspace for the frontend developer. It contains focused copies of the interface code; make implementation changes in the canonical project, not in these copies.

## Recommended learning order

1. Read `01_learning/VeriClaim_AI_Frontend_Developer_Master_Guide.pdf`.
2. Read `STUDY_GUIDE.md` for the role-specific project tasks.
3. Open `project_files/app/static/index.html` to understand the page structure.
4. Open `project_files/app/static/styles.css` to understand the design system and responsive rules.
5. Open `project_files/app/static/app.js` to understand state, views, event binding and API calls.
6. Read `project_files/server.py` only for the frontend-backend API contract.
7. Run the canonical project and test one customer, one staff and one Model Lab flow.

## Folder map

```text
01_learning/
  VeriClaim_AI_Frontend_Developer_Master_Guide.pdf  - chapter-based learning book
STUDY_GUIDE.md / STUDY_GUIDE.pdf                    - original role assignment guide
project_files/
  app/static/index.html                             - semantic screen shells
  app/static/styles.css                             - visual design and responsive CSS
  app/static/app.js                                 - browser state, rendering and API calls
  server.py                                         - JSON endpoints and static-file server
  docs/                                             - architecture, demo and model context
  assets/                                           - visual project assets
```

## Run the real application

From the canonical project root:

```powershell
.venv\Scripts\python.exe server.py
```

Then open `http://127.0.0.1:8080/`.

Use the customer and staff demo credentials from the canonical project `README.md`. The packet copies are for study; the running application uses the canonical source.

## First practice tasks

- Find the `state` object in `app.js` and describe every field.
- Trace the Model Lab request from file selection to `POST /api/model-test`.
- Find the claim form's optional incident type and explain why it is not a model feature.
- Add no code at first: use browser DevTools Network tab to inspect `/api/portal` and `/api/model-test` responses.

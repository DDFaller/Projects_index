# Faller / Index API

The API is the first vertical slice of the rebranded portfolio: a versioned,
typed project catalogue with relevance-ranked search.

## Run locally

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r api/requirements.txt
uvicorn api.app:app --reload
```

The API is available at `http://localhost:8000`. Interactive OpenAPI
documentation is available at `http://localhost:8000/docs`.

## Example requests

```bash
curl http://localhost:8000/health
curl 'http://localhost:8000/api/v1/projects?q=webgl'
curl 'http://localhost:8000/api/v1/projects?category=computer-vision'
curl http://localhost:8000/api/v1/projects/cloth-simulation
```

The catalogue is intentionally JSON-backed in this first slice. The API
contract is ready for the next step: moving project records to PostgreSQL and
adding authenticated editing without changing the public response shape.

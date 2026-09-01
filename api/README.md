# Faller / Index API

The API is the backend slice of the rebranded portfolio: a versioned, typed
project catalogue with relevance-ranked search and a URL shortener with click
analytics.

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
Prometheus metrics are available at `http://localhost:8000/metrics`.

When running through Vercel, the same deployment also serves the portfolio
homepage at `/`, its stylesheet and browser client, and the `/images` assets.

## Example requests

```bash
curl http://localhost:8000/health
curl http://localhost:8000/metrics
curl 'http://localhost:8000/api/v1/projects?q=webgl'
curl 'http://localhost:8000/api/v1/projects?category=computer-vision'
curl http://localhost:8000/api/v1/projects/cloth-simulation

curl -X POST http://localhost:8000/api/v1/short-links \
  -H 'content-type: application/json' \
  -d '{"target_url":"https://example.com/docs","alias":"docs-1"}'
curl -i http://localhost:8000/r/docs-1
curl http://localhost:8000/api/v1/short-links/docs-1/stats
curl -X POST http://localhost:8000/api/v1/short-links/docs-1/disable
```

## URL shortener contract

- `POST /api/v1/short-links` creates a generated code or a unique custom alias.
- `GET /r/{code}` returns a `307` redirect and records a click event.
- `GET /api/v1/short-links/{code}/stats` returns click totals, last-click time,
  referrers, and user-agent counts without exposing IP addresses.
- `POST /api/v1/short-links/{code}/disable` invalidates a link and evicts it
  from the redirect cache.
- Missing links return `404`; expired and disabled links return `410`.
- Creation, redirect, stats, and disable requests use a fixed-window per-IP
  rate limit. Set `SHORTENER_RATE_LIMIT` to change the default of 60 requests
  per minute.

The first implementation keeps links, events, and the hot redirect cache in
the process so it works on Vercel without external services. This is suitable
for a demo but not durable across serverless instances or cold starts. The
next production step is to replace `InMemoryLinkRepository` with PostgreSQL
and `RedirectCache` with Redis; the route and response contracts do not need
to change.

## Click shortener Grafana dashboard

Start the API on a host address so the observability containers can scrape it:

```bash
uvicorn api.app:app --host 0.0.0.0 --port 8000
docker compose -f observability/docker-compose.yml up -d
```

Then open [Grafana](http://localhost:3000). The provisioned dashboard is
called `Faller / Index — Click Shortener`; the default login is
`admin`/`admin`. Prometheus is available at [localhost:9090](http://localhost:9090).

The dashboard flows from overview to user impact, performance, and traffic. It
shows link creation, active process-local links, redirect success, missing or
inactive links, p50/p95 request latency, HTTP status rates, and rate-limit
pressure. Its educational storage panel explains why Vercel cold starts reset
the process-local demo state.
The metrics endpoint should be protected or scraped privately before using
this setup in production.

For a public portfolio demo, use Grafana Cloud Free instead of the local
containers: add the deployed `https://YOUR-VERCEL-DOMAIN.vercel.app/metrics`
URL through Grafana Cloud's Metrics Endpoint integration, then publish the
versioned resources in `observability/grafana/resources/` with `gcx`. The
folder resource is `Faller / Index`; the dashboard resource preserves UID
`faller-index-observability` and uses Cloud datasource UID `grafanacloud-prom`.
Share the dashboard externally as read-only and paste the resulting HTTPS URL
into the `observability-dashboard-url` meta tag in `index.html` to enable the
portfolio navigation link. Because the API uses process-local metrics,
counters can reset when Vercel starts a new function instance.

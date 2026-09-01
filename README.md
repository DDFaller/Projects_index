# Faller / Index

Faller / Index is Daniel Faller's searchable engineering portfolio: a living
catalogue of backend, fullstack, computer-vision, and visual-computing work.

The repository is being remade in small vertical slices. The backend now has a
typed FastAPI catalogue, relevance-ranked search, and a compact URL shortener
with redirect analytics, while the static portfolio remains usable when the
API is offline.



🧠 Currently studying Software Engineering in a post-graduate program in PUC-RIO

👯‍♀️ Last company: OLX.

🤔 Graduated in Computer Science PUC-RIO.

📫 Contact: danielmfaller@hotmail.com

🪪 Linkedin: https://www.linkedin.com/in/daniel-machado-carneiro-faller-2b7545158/

## Run the catalogue API

```bash
python -m venv venv
source venv/bin/activate
pip install -r api/requirements.txt
uvicorn api.app:app --reload
```

Open `http://localhost:8000/docs` for the interactive API documentation. The
portfolio frontend will use the live catalogue when served through the API;
otherwise it falls back to its cached project data.

## Deploy to Vercel

The repository is prepared for Vercel's Python runtime. Push the repository to
GitHub, import it at [vercel.com/new](https://vercel.com/new), and keep the
project root as the root directory. Vercel detects the FastAPI application in
`api/app.py` and installs the production dependencies from the root-level
`requirements.txt`.

The deployed catalogue will be available at `/api/v1/projects`, with API
documentation at `/docs` and the health check at `/health`.

The URL shortener endpoints are also available on the deployment:

```bash
curl -X POST https://your-domain.vercel.app/api/v1/short-links \
  -H 'content-type: application/json' \
  -d '{"target_url":"https://example.com","alias":"hello-1"}'
curl -i https://your-domain.vercel.app/r/hello-1
curl https://your-domain.vercel.app/api/v1/short-links/hello-1/stats
```

The demo uses in-memory storage and cache, so links are not durable across
Vercel cold starts. PostgreSQL and Redis are the intended production adapters.

## Backend observability

The API exposes Prometheus metrics at `/metrics` and includes a preconfigured
Grafana dashboard. For a local dashboard, start the API with `--host
0.0.0.0`, then run:

```bash
docker compose -f observability/docker-compose.yml up -d
```

Open [Grafana](http://localhost:3000) to view redirect outcomes, request
latency, HTTP status rates, link creation, and rate-limit pressure.

For a public, zero-cost dashboard, create a Grafana Cloud Free stack and add
the deployed metrics URL as a Metrics Endpoint scrape job:

```text
https://YOUR-VERCEL-DOMAIN.vercel.app/metrics
```

Import `observability/grafana/dashboards/faller-index.json`, create a
read-only externally shared dashboard, and paste its URL into the
`observability-dashboard-url` meta tag in `index.html`. The portfolio will
then show an `Observability` link in its navigation. Grafana Cloud's Metrics
Endpoint integration scrapes public Prometheus endpoints directly; the free
tier has limited retention and active-series capacity.

## Portfolio modes

The same website can be shared with a role-specific focus by adding a query
parameter:

- `/?portfolio=backend`
- `/?portfolio=frontend`
- `/?portfolio=fullstack`
- `/?portfolio=machine-learning`
- `/?portfolio=computer-vision`

Mode names are case-insensitive. The mode changes the hero copy, metadata, and
visible project categories while preserving the same search and project URLs.

## Thesis 🎓

Project Name: "Tracking Applications Classifying Human Actions in a Sports Context"

Description: In recent years, tracking applications have become increasingly popular in various fields, including sports. These applications utilize advanced technologies to monitor and classify human actions in a sports context, providing valuable insights for athletes, coaches, and spectators.


https://github.com/DDFaller/Projects_index/assets/49894740/e85646e7-2bb5-4324-8861-cce8523a744e


## MDPrognosys 🩺

Project Name: "MDPrognosys"

Description:
MDPrognosys" was a Ph.D. endeavor, developed using Meta 2, an augmented reality device. The primary objective was to create an immersive scenario where doctors could explore 3D models generated from tomographies to gain valuable insights into the patient's anatomy before any physical procedures.

Through the innovative use of Meta 2's augmented reality capabilities, the project aimed to revolutionize medical practices by providing physicians with a comprehensive understanding of the patient's anatomy. By visualizing 3D models derived from tomography scans, doctors could explore intricate details of the patient's anatomy in a realistic and interactive manner.

The significance of "MDPrognosys" extended beyond its technological prowess; it showcased the potential of augmented reality to enhance medical diagnosis and treatment planning. By offering doctors a unique and interactive way to examine the patient's body non-invasively, the project aimed to optimize medical procedures, improve patient outcomes, and drive advancements in the field of healthcare.

[TV report ](https://www.youtube.com/watch?v=mSjrowjVavk&ab_channel=TVBrasil)
## WEBGL Rendering

Project Name: "WEBGL loading models"

Description: This was a delightful little project where I set out to render multiple objects in WebGL and, as an added bonus, incorporated some basic camera movement.

In this endeavor, I dived into the world of WebGL, eager to explore its possibilities. Although the project might seem simple in scope, it quickly became a playground of creativity and technical ingenuity.


https://github.com/DDFaller/Projects_index/assets/49894740/a2fbf0be-1eec-4cf0-a045-61c836fe1f86



## Pathfinding algorithm

Project Name: "AI Pathfinding"

Description:During my time at university, while taking AI classes, I had the opportunity to develop a pathfinding algorithm using Processing.py.

The pathfinding algorithm I crafted aimed to find the most efficient path between two points on a grid, simulating real-world navigation scenarios. I poured my heart into fine-tuning the algorithm's logic and optimizing its performance, ensuring that it would produce accurate and swift results.



https://github.com/DDFaller/Projects_index/assets/49894740/fc34665c-df2b-4fc0-a4d2-723063a572e0



## Minor projects of AI

Projects: Tic-Tac-Toe

Description:
Developed Tic Tac Toe AI taking the game to a whole new level. The intelligent AI game master learns, adapts, and strategizes against its human opponents. Powered by advanced algorithms, the AI analyzes the board, predicts potential moves, and makes optimal decisions to create an engaging and formidable challenge.



https://github.com/DDFaller/Projects_index/assets/49894740/883cbdb9-10f9-45c5-8bd1-96cc73c10471
![TIC-TAC-TOE_data](https://github.com/DDFaller/Projects_index/assets/49894740/eda0b53b-3ca2-4029-96c2-3cbb1c8a0169)



Projects: Battleship
 to be awed as the AI meticulously analyzes your moves, deduces your ship placements, and executes devastating attacks with precision. With each encounter, you'll find yourself devising cunning strategies to outmaneuver your AI rival, making every game a captivating and suspenseful experience.

![Strategies](https://github.com/DDFaller/Projects_index/assets/49894740/e5c860d5-0f87-4762-99c1-ce49d4c06c97)
![Score screen](https://github.com/DDFaller/Projects_index/assets/49894740/bed054f0-59aa-4adb-aab7-02d0b5e63fc3)



## Others

Projects: Extending OIT in Unity

Description:
OIT is a fundamental technique in computer graphics that enables the rendering of complex scenes with transparent objects, such as glass, water, and foliage, while preserving accurate visual representation. 
[Project](https://github.com/DDFaller/ExtendingOIT)

Projects: Superpixel Segmentation with SLIC

Description:
Superpixels play a pivotal role in image processing by grouping pixels with similar characteristics, reducing computational complexity, and enhancing object boundary preservation. SLIC, in particular, excels in this domain, offering an elegant and intuitive approach to generating compact and visually coherent superpixels.

[Colab](https://colab.research.google.com/drive/1jq_qOJAPTn5RXVBCCy1E86kUx20V_c9i)

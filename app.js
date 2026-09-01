const PROJECTS_API = window.FALLER_INDEX_API || "/api/v1/projects";

const portfolioModes = {
  all: {
    label: "All work",
    kicker: "01 / PROJECT CATALOGUE",
    title: "Selected work",
    intro: "Search across experiments, interfaces, systems, and visual computing projects.",
    hero: "Software engineer building reliable systems, useful data products, and computer-vision tools.",
    description: "Faller / Index — Daniel Faller's software engineering portfolio.",
    categories: [],
  },
  backend: {
    label: "Backend focus",
    kicker: "01 / BACKEND SYSTEMS",
    title: "Systems behind the interface",
    intro: "APIs, search, data contracts, and the engineering decisions that make products dependable.",
    hero: "Backend engineer building reliable APIs, search services, and production-minded systems.",
    description: "Faller / Index — Daniel Faller's backend engineering portfolio.",
    categories: ["backend", "fullstack"],
  },
  frontend: {
    label: "Frontend focus",
    kicker: "01 / FRONTEND EXPERIENCES",
    title: "Interfaces with a point of view",
    intro: "Responsive interfaces, accessible interactions, and visual systems connected to real project data.",
    hero: "Frontend engineer building accessible interfaces for complex technical work.",
    description: "Faller / Index — Daniel Faller's frontend engineering portfolio.",
    categories: ["frontend", "fullstack"],
  },
  fullstack: {
    label: "Fullstack focus",
    kicker: "01 / FULLSTACK PRODUCTS",
    title: "From data model to interface",
    intro: "End-to-end products connecting thoughtful APIs, durable data, and clear user experiences.",
    hero: "Fullstack engineer taking products from data model to polished interface.",
    description: "Faller / Index — Daniel Faller's fullstack engineering portfolio.",
    categories: ["fullstack", "frontend", "backend"],
  },
  "machine-learning": {
    label: "Machine learning focus",
    kicker: "01 / MACHINE LEARNING",
    title: "Models connected to useful systems",
    intro: "Computer-vision and machine-learning work presented with attention to inputs, outputs, and real use.",
    hero: "Machine-learning engineer working across computer vision, tracking, and usable software.",
    description: "Faller / Index — Daniel Faller's machine-learning portfolio.",
    categories: ["machine-learning", "computer-vision"],
  },
  "computer-vision": {
    label: "Computer vision focus",
    kicker: "01 / COMPUTER VISION",
    title: "Seeing systems differently",
    intro: "Detection, tracking, depth, and visual computing projects with a path toward deployable tools.",
    hero: "Computer-vision engineer building tools that connect visual data to useful action.",
    description: "Faller / Index — Daniel Faller's computer-vision portfolio.",
    categories: ["computer-vision", "machine-learning"],
  },
};

const fallbackProjects = [
  {
    slug: "url-shortener-analytics",
    title: "URL Shortener and Redirect Analytics API",
    eyebrow: "Fast redirects + reliable click events",
    description: "A compact backend service that creates short links, handles expiration and disablement, and records privacy-conscious usage summaries.",
    technologies: ["Python", "FastAPI", "REST API", "Caching", "Rate Limiting"],
    categories: ["backend", "fullstack"],
    repo_url: "https://github.com/DDFaller/Projects_index",
    featured: true,
  },
  {
    slug: "faller-index-api",
    title: "Faller / Index API",
    eyebrow: "FastAPI catalogue + ranked search",
    description: "A versioned API that powers this searchable portfolio with validated project data and relevance-ranked queries.",
    technologies: ["Python", "FastAPI", "REST API", "Search"],
    categories: ["backend", "fullstack"],
    repo_url: "https://github.com/DDFaller/Projects_index",
    featured: true,
  },
  {
    slug: "rgb-d-object-detection",
    title: "4-Channel Object Detection",
    eyebrow: "YOLO + depth integration",
    description: "Modified an object-detection pipeline to process RGB images together with depth captured by an Azure Kinect sensor.",
    technologies: ["YOLO", "Computer Vision", "Azure Kinect"],
    categories: ["computer-vision", "machine-learning"],
    embed_url: "https://www.youtube.com/embed/GB_UXOOXPUo",
    demo_url: "https://youtube.com/shorts/GB_UXOOXPUo?feature=share",
    featured: true,
  },
  {
    slug: "mdprognosys",
    title: "MDPrognosys",
    eyebrow: "Augmented reality in medicine",
    description: "Created an immersive medical visualisation experience using 3D tomography models and a Meta 2 augmented-reality device.",
    technologies: ["Augmented Reality", "3D Visualisation", "Healthcare"],
    categories: ["computer-graphics", "fullstack"],
    embed_url: "https://www.youtube.com/embed/mSjrowjVavk",
    demo_url: "https://www.youtube.com/watch?v=mSjrowjVavk",
    featured: true,
  },
  {
    slug: "cloth-simulation",
    title: "Cloth Simulation",
    eyebrow: "Real-time 3D rendering",
    description: "Reproduced a real-time cloth-simulation paper as an interactive Three.js and WebGL demo.",
    technologies: ["Three.js", "WebGL", "3D Simulation"],
    categories: ["frontend", "computer-graphics"],
    embed_url: "https://ig-3-d-cloth-render.vercel.app/",
    demo_url: "https://ig-3-d-cloth-render.vercel.app/",
    featured: true,
  },
  {
    slug: "sports-action-tracking-thesis",
    title: "Sports Action Tracking Thesis",
    eyebrow: "Tracking and action classification",
    description: "Studied how tracking applications can monitor and classify human actions in a sports context.",
    technologies: ["Data Analysis", "AI/ML", "Sports Tracking"],
    categories: ["machine-learning", "computer-vision"],
    image_url: "./images/tracking.jpg",
    demo_url: "https://github.com/DDFaller/Projects_index/assets/49894740/e85646e7-2bb5-4324-8861-cce8523a744e",
  },
];

const projectGrid = document.querySelector("#project-grid");
const projectSearch = document.querySelector("#project-search");
const searchInput = document.querySelector("#project-query");
const categorySelect = document.querySelector("#project-category");
const projectStatus = document.querySelector("#project-status");
const observabilityLink = document.querySelector("#observability-link");
const modeElements = {
  hero: document.querySelector("#hero-focus"),
  kicker: document.querySelector("#portfolio-kicker"),
  title: document.querySelector("#portfolio-title"),
  intro: document.querySelector("#portfolio-intro"),
};

const params = new URLSearchParams(window.location.search);
const requestedMode = params.get("portfolio") || params.get("mode") || params.get("") || "all";
const normalizedMode = requestedMode.toLowerCase().trim().replaceAll("_", "-").replaceAll(" ", "-");
const activeMode = portfolioModes[normalizedMode] || portfolioModes.all;

function trackAnalyticsEvent(name, data = {}) {
  if (typeof window.va !== "function") return;
  window.va("event", { name, data });
}

function trackPortfolioMode() {
  const mode = Object.hasOwn(portfolioModes, normalizedMode) ? normalizedMode : "all";
  trackAnalyticsEvent("portfolio_mode_view", { mode });
}

function configureObservabilityLink() {
  const dashboardUrl = document.querySelector('meta[name="observability-dashboard-url"]')?.content.trim();
  if (!observabilityLink || !dashboardUrl || !dashboardUrl.startsWith("https://")) return;
  observabilityLink.href = dashboardUrl;
  observabilityLink.hidden = false;
}

function applyPortfolioMode() {
  modeElements.hero.textContent = activeMode.hero;
  modeElements.kicker.textContent = activeMode.kicker;
  modeElements.title.textContent = activeMode.title;
  modeElements.intro.textContent = activeMode.intro;
  document.title = `${activeMode.label} | Faller / Index`;
  document.querySelector('meta[name="description"]').setAttribute("content", activeMode.description);
}

function projectMatchesMode(project) {
  return !activeMode.categories.length || activeMode.categories.some((category) => project.categories.includes(category));
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderProjects(projects) {
  if (!projects.length) {
    projectGrid.innerHTML = '<p class="project-empty">No projects matched that search.</p>';
    return;
  }

  projectGrid.innerHTML = projects.map((project) => {
    const media = project.embed_url
      ? `<iframe class="work__video" src="${escapeHtml(project.embed_url)}" title="${escapeHtml(project.title)}" loading="lazy" allowfullscreen></iframe>`
      : `<img class="work__image" src="${escapeHtml(project.image_url || "./images/header2.jpg")}" alt="${escapeHtml(project.title)} preview" loading="lazy" />`;
    const links = [];
    if (project.demo_url) links.push(`<a href="${escapeHtml(project.demo_url)}" target="_blank" rel="noreferrer" class="link__text" data-analytics-destination="demo">View project <span>&rarr;</span></a>`);
    if (project.repo_url) links.push(`<a href="${escapeHtml(project.repo_url)}" target="_blank" rel="noreferrer" class="link__text" data-analytics-destination="repo">Repository <span>&rarr;</span></a>`);

    return `<article class="work__box project-card" data-analytics-project="${escapeHtml(project.slug)}">
      <div class="work__image-box">${media}</div>
      <div class="work__text">
        <p class="project-card__eyebrow">${escapeHtml(project.eyebrow)}</p>
        <h3>${escapeHtml(project.title)}</h3>
        <p>${escapeHtml(project.description)}</p>
        <ul class="work__list">${project.technologies.map((technology) => `<li>${escapeHtml(technology)}</li>`).join("")}</ul>
        <div class="work__links">${links.join("")}</div>
      </div>
    </article>`;
  }).join("");
}

async function loadProjects() {
  const query = new URLSearchParams({ page_size: "50" });
  if (searchInput.value.trim()) query.set("q", searchInput.value.trim());
  if (categorySelect.value) query.set("category", categorySelect.value);

  projectStatus.textContent = "Searching the catalogue…";
  try {
    const response = await fetch(`${PROJECTS_API}?${query.toString()}`);
    if (!response.ok) throw new Error(`API returned ${response.status}`);
    const payload = await response.json();
    const visibleProjects = payload.results.filter(projectMatchesMode);
    renderProjects(visibleProjects);
    projectStatus.textContent = `${visibleProjects.length} project${visibleProjects.length === 1 ? "" : "s"} · ${activeMode.label}`;
  } catch (error) {
    const queryValue = searchInput.value.trim().toLowerCase();
    const categoryValue = categorySelect.value;
    const visibleProjects = fallbackProjects.filter((project) => {
      const haystack = [project.title, project.eyebrow, project.description, ...project.technologies, ...project.categories].join(" ").toLowerCase();
      return projectMatchesMode(project) && (!queryValue || haystack.includes(queryValue)) && (!categoryValue || project.categories.includes(categoryValue));
    });
    renderProjects(visibleProjects);
    projectStatus.textContent = `Showing cached catalogue data · ${activeMode.label} — start the API for live search.`;
  }
}

projectSearch.addEventListener("submit", (event) => {
  event.preventDefault();
  trackAnalyticsEvent("project_search", {
    has_query: Boolean(searchInput.value.trim()),
    category: categorySelect.value || "all",
  });
  loadProjects();
});

categorySelect.addEventListener("change", loadProjects);
projectGrid.addEventListener("click", (event) => {
  const link = event.target.closest("a[data-analytics-destination]");
  if (!link) return;
  const project = link.closest("[data-analytics-project]");
  if (!project) return;
  trackAnalyticsEvent("project_link_click", {
    project: project.dataset.analyticsProject,
    destination: link.dataset.analyticsDestination,
  });
});
applyPortfolioMode();
configureObservabilityLink();
trackPortfolioMode();
loadProjects();

const PROJECTS_API = window.FALLER_INDEX_API || "/api/v1/projects";

const fallbackProjects = [
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
    const link = project.demo_url
      ? `<a href="${escapeHtml(project.demo_url)}" target="_blank" rel="noreferrer" class="link__text">View project <span>&rarr;</span></a>`
      : "";

    return `<article class="work__box project-card">
      <div class="work__image-box">${media}</div>
      <div class="work__text">
        <p class="project-card__eyebrow">${escapeHtml(project.eyebrow)}</p>
        <h3>${escapeHtml(project.title)}</h3>
        <p>${escapeHtml(project.description)}</p>
        <ul class="work__list">${project.technologies.map((technology) => `<li>${escapeHtml(technology)}</li>`).join("")}</ul>
        <div class="work__links">${link}</div>
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
    renderProjects(payload.results);
    projectStatus.textContent = `${payload.total} project${payload.total === 1 ? "" : "s"} in the catalogue`;
  } catch (error) {
    const queryValue = searchInput.value.trim().toLowerCase();
    const categoryValue = categorySelect.value;
    const visibleProjects = fallbackProjects.filter((project) => {
      const haystack = [project.title, project.eyebrow, project.description, ...project.technologies, ...project.categories].join(" ").toLowerCase();
      return (!queryValue || haystack.includes(queryValue)) && (!categoryValue || project.categories.includes(categoryValue));
    });
    renderProjects(visibleProjects);
    projectStatus.textContent = "Showing cached catalogue data — start the API for live search.";
  }
}

projectSearch.addEventListener("submit", (event) => {
  event.preventDefault();
  loadProjects();
});

categorySelect.addEventListener("change", loadProjects);
loadProjects();

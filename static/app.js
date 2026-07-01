const grid = document.getElementById("grid");
const statusLine = document.getElementById("status-line");
const searchForm = document.getElementById("search-form");
const searchInput = document.getElementById("search-input");
const methodBtns = document.querySelectorAll(".method-btn");

const lightbox = document.getElementById("lightbox");
const lightboxImg = document.getElementById("lightbox-img");
const lightboxCaption = document.getElementById("lightbox-caption");
const lightboxClose = document.getElementById("lightbox-close");
const findSimilarBtn = document.getElementById("find-similar-btn");

let method = "semantic";
let currentLightboxFile = null;
let debounceTimer = null;

function renderResults(results, label) {
  grid.innerHTML = "";
  if (results.length === 0) {
    grid.innerHTML = `<div class="empty-state">No matches found${label ? ` for “${label}”` : ""}.</div>`;
    return;
  }
  for (const r of results) {
    const card = document.createElement("div");
    card.className = "card";
    card.innerHTML = `
      <img src="${r.thumb_url}" loading="lazy" alt="${r.filename}" />
      <span class="score-badge">${(r.score * 100).toFixed(0)}%</span>
    `;
    card.addEventListener("click", () => openLightbox(r));
    grid.appendChild(card);
  }
}

async function loadAllImages() {
  statusLine.textContent = "Loading images…";
  const res = await fetch("/api/images");
  const data = await res.json();
  renderResults(data);
  statusLine.textContent = `${data.length} image${data.length === 1 ? "" : "s"} indexed. Type a query above to search.`;
}

async function runSearch(query) {
  if (!query.trim()) {
    return loadAllImages();
  }
  statusLine.textContent = `Searching (${method}) for “${query}”…`;
  const res = await fetch(`/api/search?q=${encodeURIComponent(query)}&method=${method}`);
  const data = await res.json();
  renderResults(data, query);
  statusLine.textContent = `${data.length} result${data.length === 1 ? "" : "s"} for “${query}” (${method} search).`;
}

function openLightbox(result) {
  currentLightboxFile = result.filename;
  lightboxImg.src = result.image_url;
  lightboxCaption.textContent = result.filename;
  lightbox.classList.remove("hidden");
}

function closeLightbox() {
  lightbox.classList.add("hidden");
  lightboxImg.src = "";
  currentLightboxFile = null;
}

findSimilarBtn.addEventListener("click", async () => {
  if (!currentLightboxFile) return;
  const file = currentLightboxFile;
  closeLightbox();
  statusLine.textContent = `Finding images similar to ${file}…`;
  const res = await fetch(`/api/similar/${encodeURIComponent(file)}`);
  const data = await res.json();
  renderResults(data, file);
  statusLine.textContent = `${data.length} image${data.length === 1 ? "" : "s"} similar to ${file}.`;
  searchInput.value = "";
});

lightboxClose.addEventListener("click", closeLightbox);
lightbox.querySelector(".lightbox-backdrop").addEventListener("click", closeLightbox);
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") closeLightbox();
});

methodBtns.forEach((btn) => {
  btn.addEventListener("click", () => {
    methodBtns.forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    method = btn.dataset.method;
    if (searchInput.value.trim()) runSearch(searchInput.value);
  });
});

searchForm.addEventListener("submit", (e) => {
  e.preventDefault();
  clearTimeout(debounceTimer);
  runSearch(searchInput.value);
});

searchInput.addEventListener("input", () => {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => runSearch(searchInput.value), 350);
});

loadAllImages();

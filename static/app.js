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

async function fetchJSON(url) {
  let res;
  try {
    res = await fetch(url);
  } catch {
    throw new Error("Network error — is the server running?");
  }
  if (!res.ok) {
    let message = res.statusText || `HTTP ${res.status}`;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") message = body.detail;
      else if (Array.isArray(body.detail)) {
        message = body.detail.map((d) => d.msg).join("; ");
      }
    } catch {
      // body wasn't JSON, keep the statusText fallback
    }
    throw new Error(message);
  }
  return res.json();
}

function renderResults(results, label) {
  grid.innerHTML = "";
  if (results.length === 0) {
    grid.classList.remove("grid--ranked");
    grid.innerHTML = `<div class="empty-state">No matches found${label ? ` for “${label}”` : ""}.</div>`;
    return;
  }

  const ranked = results.every((r) => typeof r.score === "number");
  grid.classList.toggle("grid--ranked", ranked);

  results.forEach((r, i) => {
    const card = document.createElement("div");
    if (ranked) {
      card.className = "result-row";
      const pct = Math.round(r.score * 100);
      card.innerHTML = `
        <span class="result-rank">${i + 1}</span>
        <img class="result-thumb" src="${r.thumb_url}" loading="lazy" alt="${r.filename}" />
        <div class="result-info">
          <div class="result-filename">${r.filename}</div>
          <div class="result-score-bar"><div class="result-score-fill" style="width:${pct}%"></div></div>
          <div class="result-score-label">${pct}% match</div>
        </div>
      `;
    } else {
      card.className = "card";
      card.innerHTML = `<img src="${r.thumb_url}" loading="lazy" alt="${r.filename}" />`;
    }
    card.addEventListener("click", () => openLightbox(r));
    grid.appendChild(card);
  });
}

async function loadAllImages() {
  statusLine.textContent = "Loading images…";
  try {
    const data = await fetchJSON("/api/images");
    renderResults(data);
    statusLine.textContent = `${data.length} image${data.length === 1 ? "" : "s"} indexed. Type a query above to search.`;
  } catch (err) {
    statusLine.textContent = `Couldn't load images: ${err.message}`;
  }
}

async function runSearch(query) {
  if (!query.trim()) {
    return loadAllImages();
  }
  statusLine.textContent = `Searching (${method}) for “${query}”…`;
  try {
    const data = await fetchJSON(`/api/search?q=${encodeURIComponent(query)}&method=${method}`);
    renderResults(data, query);
    statusLine.textContent = `${data.length} result${data.length === 1 ? "" : "s"} for “${query}” (${method} search).`;
  } catch (err) {
    statusLine.textContent = `Search failed: ${err.message}`;
  }
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
  try {
    const data = await fetchJSON(`/api/similar/${encodeURIComponent(file)}`);
    renderResults(data, file);
    statusLine.textContent = `${data.length} image${data.length === 1 ? "" : "s"} similar to ${file}.`;
    searchInput.value = "";
  } catch (err) {
    statusLine.textContent = `Couldn't find similar images: ${err.message}`;
  }
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

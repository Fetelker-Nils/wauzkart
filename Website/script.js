const shots = document.querySelectorAll(".shot");
const preview = document.querySelector("#preview-image");

for (const shot of shots) {
  shot.addEventListener("click", () => {
    for (const other of shots) {
      other.classList.remove("active");
    }
    shot.classList.add("active");
    preview.src = shot.dataset.image;
  });
}

function ratingBars(speed, acceleration) {
  return `
    <div class="rating-row"><span>Speed</span><meter min="0" max="10" value="${speed}"></meter><b>${speed}/10</b></div>
    <div class="rating-row"><span>Beschl.</span><meter min="0" max="10" value="${acceleration}"></meter><b>${acceleration}/10</b></div>
  `;
}

function createCharacterCard(character) {
  return `
    <article class="roster-card">
      <div class="driver-mark" style="--mark:${character.color}"></div>
      <div>
        <span class="pill">${character.unlock}</span>
        <h3>${character.name}</h3>
        <p>${character.role}</p>
        ${ratingBars(character.speed, character.acceleration)}
      </div>
    </article>
  `;
}

function createCarCard(car) {
  return `
    <article class="roster-card car-card">
      <div class="kart-shape"><span>${car.tag}</span></div>
      <div>
        <span class="pill">${car.unlock}</span>
        <h3>${car.name}</h3>
        <p>${car.note}</p>
        ${ratingBars(car.speed, car.acceleration)}
      </div>
    </article>
  `;
}

function createInfoCard(entry) {
  return `
    <article>
      <span class="feature-icon">${entry.kind || entry.name.slice(0, 2).toUpperCase()}</span>
      <h3>${entry.name}</h3>
      <p>${entry.effect || entry.description}</p>
    </article>
  `;
}

function createTrackRows(tracks) {
  return `
    <div class="track-row track-head"><span>Strecke</span><span>Typ</span><span>Level</span><span>Beschreibung</span></div>
    ${tracks.map(track => `
      <div class="track-row">
        <strong>${track.name}</strong>
        <span>${track.type}</span>
        <span>Level ${track.unlockLevel}</span>
        <p>${track.description}</p>
      </div>
    `).join("")}
  `;
}

async function loadWikiData() {
  const needsData = document.querySelector("#character-grid, #car-grid, #item-grid, #mode-grid, #track-table");
  if (!needsData) {
    return;
  }

  const response = await fetch("/data/wiki-data.json");
  if (!response.ok) {
    throw new Error("Wiki-Daten konnten nicht geladen werden.");
  }
  const data = await response.json();

  const characterGrid = document.querySelector("#character-grid");
  if (characterGrid) {
    characterGrid.innerHTML = data.characters.map(createCharacterCard).join("");
  }

  const carGrid = document.querySelector("#car-grid");
  if (carGrid) {
    carGrid.innerHTML = data.cars.map(createCarCard).join("");
  }

  const itemGrid = document.querySelector("#item-grid");
  if (itemGrid) {
    itemGrid.innerHTML = data.items.map(createInfoCard).join("");
  }

  const modeGrid = document.querySelector("#mode-grid");
  if (modeGrid) {
    modeGrid.innerHTML = data.modes.map(createInfoCard).join("");
  }

  const trackTable = document.querySelector("#track-table");
  if (trackTable) {
    trackTable.innerHTML = createTrackRows(data.tracks);
  }
}

loadWikiData().catch((error) => {
  console.error(error);
});

// Initialize Vercel Speed Insights
(function initSpeedInsights() {
  // Initialize queue for Speed Insights
  if (!window.si) {
    window.si = function() {
      (window.siq = window.siq || []).push(arguments);
    };
  }

  // Create and inject the Speed Insights script
  const script = document.createElement('script');
  script.src = 'https://va.vercel-scripts.com/v1/speed-insights/script.js';
  script.defer = true;
  
  script.onerror = function() {
    console.log('[Vercel Speed Insights] Failed to load script. Please check if any content blockers are enabled.');
  };
  
  document.head.appendChild(script);
})();

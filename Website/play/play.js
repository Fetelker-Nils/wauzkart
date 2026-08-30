const canvas = document.querySelector("#game");
const ctx = canvas.getContext("2d");
const overlay = document.querySelector("#overlay");
const startButton = document.querySelector("#start-button");
const overlayTitle = overlay.querySelector("strong");
const overlayText = overlay.querySelector(".overlay-text");
const hudScore = document.querySelector("#hud-score");
const hudItem = document.querySelector("#hud-item");
const hudTime = document.querySelector("#hud-time");

const keys = new Set();
const track = {
  cx: 640,
  cy: 360,
  rx: 430,
  ry: 210,
  width: 94,
  start: 0,
};
const totalLaps = 3;
const characters = [
  { id: "wauz", name: "Wauz", color: "#36d8ff" },
  { id: "mauz", name: "Mauz", color: "#f3c744" },
];
const cars = [
  { id: "sport", name: "Sport", color: "#ef3e32", max: 0.225, accel: 0.155, turn: 76 },
  { id: "rally", name: "Rally", color: "#4ade80", max: 0.205, accel: 0.145, turn: 96 },
];
const boxes = [
  { progress: 0.16, lane: -18, wait: 0 },
  { progress: 0.41, lane: 20, wait: 0 },
  { progress: 0.68, lane: -10, wait: 0 },
];

let selectedCharacter = 0;
let selectedCar = 0;
let running = false;
let raceTime = 0;
let lastFrame = 0;
let heldItem = "";

const player = makeRacer("DU", true, 0, 0, -24);
const ai = makeRacer("KI", false, 1, 1, 24);
const racers = [player, ai];

function makeRacer(name, human, characterIndex, carIndex, lane) {
  return {
    name,
    human,
    characterIndex,
    carIndex,
    progress: track.start,
    previousProgress: track.start,
    lane,
    targetLane: lane,
    speed: 0,
    lap: 0,
    place: 1,
    finished: false,
    finishTime: 0,
    boost: 0,
    stun: 0,
    wobble: 0,
  };
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function lerp(a, b, t) {
  return a + (b - a) * t;
}

function wrapProgress(value) {
  let next = value % 1;
  if (next < 0) next += 1;
  return next;
}

function trackPoint(progress, lane = 0) {
  const angle = (progress - track.start) * Math.PI * 2 - Math.PI / 2;
  const x = track.cx + Math.cos(angle) * track.rx;
  const y = track.cy + Math.sin(angle) * track.ry;
  const tx = -Math.sin(angle) * track.rx;
  const ty = Math.cos(angle) * track.ry;
  const len = Math.hypot(tx, ty) || 1;
  const nx = -ty / len;
  const ny = tx / len;
  return {
    x: x + nx * lane,
    y: y + ny * lane,
    rot: Math.atan2(ty, tx),
  };
}

function resetRacer(racer, lane) {
  racer.progress = track.start;
  racer.previousProgress = track.start;
  racer.lane = lane;
  racer.targetLane = lane;
  racer.speed = 0;
  racer.lap = 0;
  racer.place = 1;
  racer.finished = false;
  racer.finishTime = 0;
  racer.boost = 0;
  racer.stun = 0;
  racer.wobble = 0;
}

function resetGame() {
  running = true;
  raceTime = 0;
  heldItem = "";
  overlayTitle.textContent = "WAUZ KART RENNEN";
  overlayText.textContent = "3 Runden fahren, KI schlagen, Items nutzen.";
  startButton.textContent = "SPIEL STARTEN";
  player.characterIndex = selectedCharacter;
  player.carIndex = selectedCar;
  ai.characterIndex = selectedCharacter === 0 ? 1 : 0;
  ai.carIndex = selectedCar === 0 ? 1 : 0;
  resetRacer(player, -26);
  resetRacer(ai, 26);
  boxes.forEach((box) => {
    box.wait = 0;
  });
  overlay.classList.add("hidden");
  canvas.focus();
}

function finishRacer(racer) {
  if (racer.finished) return;
  racer.finished = true;
  racer.finishTime = raceTime;
  racer.speed = Math.min(racer.speed, 0.08);
}

function updateLap(racer) {
  if (racer.finished) return;
  if (racer.previousProgress > 0.92 && racer.progress < 0.08 && racer.speed > 0.02) {
    racer.lap += 1;
    if (racer.lap >= totalLaps) {
      finishRacer(racer);
    }
  }
  racer.previousProgress = racer.progress;
}

function updatePlayer(dt) {
  const spec = cars[player.carIndex];
  const gas = keys.has("ArrowUp") || keys.has("w") || keys.has("W");
  const brake = keys.has("ArrowDown") || keys.has("s") || keys.has("S");
  const left = keys.has("ArrowLeft") || keys.has("a") || keys.has("A");
  const right = keys.has("ArrowRight") || keys.has("d") || keys.has("D");

  if (player.finished) {
    player.speed = lerp(player.speed, 0.09, dt * 1.4);
  } else if (player.stun > 0) {
    player.stun -= dt;
    player.speed *= 0.94;
    player.wobble += dt * 18;
  } else {
    if (gas) player.speed += spec.accel * dt;
    if (brake) player.speed -= spec.accel * 1.35 * dt;
    if (!gas && !brake) player.speed *= Math.pow(0.9, dt);
    if (left) player.targetLane -= spec.turn * dt;
    if (right) player.targetLane += spec.turn * dt;
  }

  const speedLimit = spec.max + (player.boost > 0 ? 0.07 : 0);
  player.speed = clamp(player.speed, -0.045, speedLimit);
  player.targetLane = clamp(player.targetLane, -track.width * 0.35, track.width * 0.35);
  player.lane = lerp(player.lane, player.targetLane, clamp(dt * 8, 0, 1));
}

function updateAi(dt) {
  const spec = cars[ai.carIndex];
  if (ai.finished) {
    ai.speed = lerp(ai.speed, 0.085, dt * 1.3);
  } else if (ai.stun > 0) {
    ai.stun -= dt;
    ai.speed *= 0.93;
    ai.wobble += dt * 17;
  } else {
    const laneWave = Math.sin(raceTime * 1.15 + ai.progress * 8) * 18;
    const catchUp = player.lap + player.progress > ai.lap + ai.progress + 0.12 ? 0.018 : 0;
    const leadSlow = ai.lap + ai.progress > player.lap + player.progress + 0.1 ? 0.018 : 0;
    ai.targetLane = clamp(laneWave, -track.width * 0.3, track.width * 0.3);
    ai.lane = lerp(ai.lane, ai.targetLane, clamp(dt * 3.5, 0, 1));
    ai.speed = lerp(ai.speed, spec.max * 0.88 + catchUp - leadSlow, dt * 1.7);
  }
  ai.speed = clamp(ai.speed, 0, spec.max * 0.98);
}

function moveRacer(racer, dt) {
  racer.boost = Math.max(0, racer.boost - dt);
  racer.previousProgress = racer.progress;
  racer.progress = wrapProgress(racer.progress + racer.speed * dt);
  updateLap(racer);
}

function updateItems(dt) {
  boxes.forEach((box) => {
    box.wait = Math.max(0, box.wait - dt);
    if (heldItem || box.wait > 0 || player.finished) return;
    const distance = Math.abs(player.progress - box.progress);
    const wrappedDistance = Math.min(distance, 1 - distance);
    if (wrappedDistance < 0.012 && Math.abs(player.lane - box.lane) < 34) {
      heldItem = Math.random() > 0.45 ? "TURBO" : "SCHOCK";
      box.wait = 6;
    }
  });

  if ((keys.has(" ") || keys.has("Space")) && heldItem) {
    if (heldItem === "TURBO") {
      player.boost = 1.4;
      player.speed += 0.04;
    }
    if (heldItem === "SCHOCK" && !ai.finished) {
      ai.stun = 0.8;
      ai.speed *= 0.45;
    }
    heldItem = "";
    keys.delete(" ");
    keys.delete("Space");
  }
}

function updatePlaces() {
  const sorted = racers.slice().sort((a, b) => {
    if (a.finished && b.finished) return a.finishTime - b.finishTime;
    if (a.finished) return -1;
    if (b.finished) return 1;
    return b.lap + b.progress - (a.lap + a.progress);
  });
  sorted.forEach((racer, index) => {
    racer.place = index + 1;
  });
}

function update(dt) {
  if (!running) return;
  raceTime += dt;
  updatePlayer(dt);
  updateAi(dt);
  racers.forEach((racer) => moveRacer(racer, dt));
  updateItems(dt);
  updatePlaces();

  if (racers.every((racer) => racer.finished)) {
    running = false;
    const winner = racers.slice().sort((a, b) => a.finishTime - b.finishTime)[0];
    overlayTitle.textContent = "RENNEN BEENDET";
    overlayText.textContent = `${winner.name} gewinnt in ${winner.finishTime.toFixed(2)}s`;
    startButton.textContent = "NOCHMAL FAHREN";
    overlay.classList.remove("hidden");
  }
}

function drawTrack() {
  const sky = ctx.createLinearGradient(0, 0, 0, canvas.height);
  sky.addColorStop(0, "#131b2b");
  sky.addColorStop(0.45, "#1b2638");
  sky.addColorStop(1, "#142112");
  ctx.fillStyle = sky;
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  ctx.fillStyle = "#17391b";
  ctx.fillRect(0, 255, canvas.width, canvas.height);

  for (let i = 0; i < 18; i += 1) {
    const x = i * 82 - 40;
    ctx.fillStyle = i % 2 ? "#ef3e32" : "#ffe16a";
    ctx.fillRect(x, 226, 54, 22);
    ctx.fillStyle = "rgba(0,0,0,0.45)";
    ctx.fillRect(x, 248, 54, 9);
  }

  ctx.strokeStyle = "#23272e";
  ctx.lineWidth = track.width;
  ctx.beginPath();
  ctx.ellipse(track.cx, track.cy, track.rx, track.ry, 0, 0, Math.PI * 2);
  ctx.stroke();

  ctx.strokeStyle = "#ef3e32";
  ctx.lineWidth = 12;
  ctx.setLineDash([26, 18]);
  ctx.beginPath();
  ctx.ellipse(track.cx, track.cy, track.rx + track.width * 0.5, track.ry + track.width * 0.24, 0, 0, Math.PI * 2);
  ctx.stroke();
  ctx.beginPath();
  ctx.ellipse(track.cx, track.cy, track.rx - track.width * 0.5, track.ry - track.width * 0.24, 0, 0, Math.PI * 2);
  ctx.stroke();
  ctx.setLineDash([]);

  ctx.strokeStyle = "#f7f3dc";
  ctx.lineWidth = 4;
  ctx.beginPath();
  ctx.ellipse(track.cx, track.cy, track.rx + track.width * 0.5, track.ry + track.width * 0.24, 0, 0, Math.PI * 2);
  ctx.stroke();
  ctx.beginPath();
  ctx.ellipse(track.cx, track.cy, track.rx - track.width * 0.5, track.ry - track.width * 0.24, 0, 0, Math.PI * 2);
  ctx.stroke();

  ctx.strokeStyle = "rgba(255,255,255,0.42)";
  ctx.lineWidth = 4;
  ctx.setLineDash([26, 24]);
  ctx.beginPath();
  ctx.ellipse(track.cx, track.cy, track.rx, track.ry, 0, 0, Math.PI * 2);
  ctx.stroke();
  ctx.setLineDash([]);

  const start = trackPoint(track.start, 0);
  ctx.save();
  ctx.translate(start.x, start.y);
  ctx.rotate(start.rot + Math.PI / 2);
  for (let i = 0; i < 10; i++) {
    ctx.fillStyle = i % 2 ? "#101010" : "#f7f7f7";
    ctx.fillRect(-track.width * 0.5 + i * track.width * 0.1, -9, track.width * 0.1, 18);
  }
  ctx.restore();
}

function drawBoxes() {
  boxes.forEach((box) => {
    if (box.wait > 0) return;
    const p = trackPoint(box.progress, box.lane);
    ctx.save();
    ctx.translate(p.x, p.y);
    ctx.rotate(performance.now() / 650);
    ctx.fillStyle = "#101827";
    ctx.fillRect(-15, -15, 30, 30);
    ctx.strokeStyle = "#36d8ff";
    ctx.lineWidth = 4;
    ctx.strokeRect(-15, -15, 30, 30);
    ctx.fillStyle = "#ffe16a";
    ctx.font = "900 18px Arial";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText("?", 0, 1);
    ctx.restore();
  });
}

function drawRacer(racer) {
  const point = trackPoint(racer.progress, racer.lane);
  const char = characters[racer.characterIndex];
  const car = cars[racer.carIndex];
  const wobble = racer.stun > 0 ? Math.sin(racer.wobble) * 0.38 : 0;

  ctx.save();
  ctx.translate(point.x, point.y);
  ctx.rotate(point.rot + wobble);
  ctx.shadowColor = "rgba(0,0,0,0.55)";
  ctx.shadowBlur = 12;
  ctx.fillStyle = "#080a0e";
  ctx.fillRect(-25, -14, 50, 28);
  ctx.shadowBlur = 0;
  ctx.fillStyle = car.color;
  ctx.fillRect(-20, -11, 40, 22);
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(9, -7, 8, 14);
  ctx.fillStyle = char.color;
  ctx.beginPath();
  ctx.arc(-5, 0, 8, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillStyle = "#111";
  ctx.fillRect(-22, -17, 12, 7);
  ctx.fillRect(-22, 10, 12, 7);
  ctx.fillRect(10, -17, 12, 7);
  ctx.fillRect(10, 10, 12, 7);
  if (racer.boost > 0) {
    ctx.fillStyle = "#ffe16a";
    ctx.fillRect(-37, -5, 14, 10);
  }
  ctx.restore();

  ctx.fillStyle = "#ffffff";
  ctx.font = "900 13px Arial";
  ctx.textAlign = "center";
  ctx.fillText(`${racer.name} ${char.name}`, point.x, point.y - 34);
}

function drawHud() {
  hudScore.textContent = `Runde ${Math.min(player.lap + 1, totalLaps)}/${totalLaps} | Platz ${player.place}`;
  hudItem.textContent = `Item ${heldItem || "-"}`;
  hudTime.textContent = `${raceTime.toFixed(1)}s`;
}

function draw() {
  drawTrack();
  drawBoxes();
  racers.forEach(drawRacer);
  drawHud();
}

function frame(time) {
  const dt = Math.min(0.035, (time - lastFrame) / 1000 || 0);
  lastFrame = time;
  update(dt);
  draw();
  requestAnimationFrame(frame);
}

function setSelection(group, index) {
  if (group === "character") selectedCharacter = index;
  if (group === "car") selectedCar = index;
  document.querySelectorAll(`[data-select="${group}"]`).forEach((button, buttonIndex) => {
    button.classList.toggle("active", buttonIndex === index);
  });
}

window.addEventListener("keydown", (event) => {
  keys.add(event.key);
  if (["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", " "].includes(event.key)) {
    event.preventDefault();
  }
});

window.addEventListener("keyup", (event) => {
  keys.delete(event.key);
});

document.querySelectorAll("[data-key]").forEach((button) => {
  const key = button.dataset.key;
  const down = (event) => {
    event.preventDefault();
    keys.add(key);
  };
  const up = (event) => {
    event.preventDefault();
    keys.delete(key);
  };
  button.addEventListener("pointerdown", down);
  button.addEventListener("pointerup", up);
  button.addEventListener("pointerleave", up);
  button.addEventListener("pointercancel", up);
});

document.querySelectorAll("[data-select]").forEach((button) => {
  button.addEventListener("click", () => {
    setSelection(button.dataset.select, Number(button.dataset.index));
  });
});

startButton.addEventListener("click", resetGame);
setSelection("character", 0);
setSelection("car", 0);
draw();
requestAnimationFrame(frame);

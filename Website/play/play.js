const canvas = document.querySelector("#game");
const ctx = canvas.getContext("2d");
const overlay = document.querySelector("#overlay");
const startButton = document.querySelector("#start-button");
const hudScore = document.querySelector("#hud-score");
const hudItem = document.querySelector("#hud-item");
const hudTime = document.querySelector("#hud-time");

const keys = new Set();
const center = { x: 640, y: 360 };
const track = { rx: 430, ry: 210, width: 92, startAngle: Math.PI / 2 };
const totalLaps = 3;
const characters = [
  { id: "wauz", name: "Wauz", color: "#36d8ff" },
  { id: "mauz", name: "Mauz", color: "#f3c744" },
];
const carTypes = [
  { id: "sport", name: "Sport", color: "#ef3e32", max: 420, accel: 760, turn: 3.45 },
  { id: "rally", name: "Rally", color: "#4ade80", max: 385, accel: 700, turn: 3.9 },
];
const itemBoxes = [
  { angle: 0.48, wait: 0 },
  { angle: 2.72, wait: 0 },
  { angle: 4.28, wait: 0 },
];

let selectedCharacter = 0;
let selectedCar = 0;
let running = false;
let lastTime = 0;
let winnerText = "";
let heldItem = "";
let raceTime = 0;

const player = makeRacer("DU", 0, 0, true);
const ai = makeRacer("KI", 1, 1, false);
const racers = [player, ai];

function makeRacer(name, characterIndex, carIndex, human) {
  const p = pointOnTrack(track.startAngle + (human ? 0.015 : -0.03));
  return {
    name,
    characterIndex,
    carIndex,
    human,
    x: p.x + (human ? -22 : 22),
    y: p.y + (human ? 18 : -18),
    rot: -Math.PI / 2,
    speed: 0,
    lap: 0,
    progress: 0,
    lastProgress: 0,
    place: 1,
    finished: false,
    finishTime: 0,
    boost: 0,
    stun: 0,
  };
}

function resetRacer(racer, lane) {
  const p = pointOnTrack(track.startAngle + lane * 0.01);
  racer.x = p.x + lane * 26;
  racer.y = p.y - lane * 18;
  racer.rot = -Math.PI / 2;
  racer.speed = 0;
  racer.lap = 0;
  racer.progress = 0;
  racer.lastProgress = 0;
  racer.place = 1;
  racer.finished = false;
  racer.finishTime = 0;
  racer.boost = 0;
  racer.stun = 0;
}

function resetGame() {
  running = true;
  raceTime = 0;
  heldItem = "";
  winnerText = "";
  player.characterIndex = selectedCharacter;
  player.carIndex = selectedCar;
  ai.characterIndex = selectedCharacter === 0 ? 1 : 0;
  ai.carIndex = selectedCar === 0 ? 1 : 0;
  resetRacer(player, -0.45);
  resetRacer(ai, 0.45);
  itemBoxes.forEach((box) => {
    box.wait = 0;
  });
  overlay.classList.add("hidden");
  canvas.focus();
}

function clamp(v, min, max) {
  return Math.max(min, Math.min(max, v));
}

function pointOnTrack(angle, lane = 0) {
  const rx = track.rx + lane;
  const ry = track.ry + lane * 0.48;
  return {
    x: center.x + Math.cos(angle) * rx,
    y: center.y + Math.sin(angle) * ry,
  };
}

function nearestTrackAngle(x, y) {
  return Math.atan2((y - center.y) / track.ry, (x - center.x) / track.rx);
}

function normalizedProgress(angle) {
  let p = (angle - track.startAngle) / (Math.PI * 2);
  p = 1 - p;
  while (p < 0) p += 1;
  while (p >= 1) p -= 1;
  return p;
}

function angleDiff(a, b) {
  let diff = a - b;
  while (diff > Math.PI) diff -= Math.PI * 2;
  while (diff < -Math.PI) diff += Math.PI * 2;
  return diff;
}

function turnToward(racer, target, amount) {
  const diff = angleDiff(target, racer.rot);
  racer.rot += clamp(diff, -amount, amount);
  return Math.abs(diff);
}

function updatePlayer(dt) {
  if (player.finished) {
    player.speed *= 0.985;
    return;
  }
  if (player.stun > 0) {
    player.stun -= dt;
    player.speed *= 0.92;
    return;
  }
  const spec = carTypes[player.carIndex];
  const gas = keys.has("ArrowUp") || keys.has("w") || keys.has("W");
  const brake = keys.has("ArrowDown") || keys.has("s") || keys.has("S");
  const left = keys.has("ArrowLeft") || keys.has("a") || keys.has("A");
  const right = keys.has("ArrowRight") || keys.has("d") || keys.has("D");
  const maxSpeed = spec.max + (player.boost > 0 ? 120 : 0);
  if (gas) player.speed += spec.accel * dt;
  if (brake) player.speed -= spec.accel * 0.72 * dt;
  if (!gas && !brake) player.speed *= 0.985;
  player.speed = clamp(player.speed, -120, maxSpeed);
  const steer = spec.turn * dt * clamp(Math.abs(player.speed) / 260, 0.25, 1);
  if (left) player.rot -= player.speed >= 0 ? steer : -steer;
  if (right) player.rot += player.speed >= 0 ? steer : -steer;
}

function updateAi(dt) {
  if (ai.finished) {
    ai.speed *= 0.985;
    return;
  }
  const spec = carTypes[ai.carIndex];
  const targetProgress = (ai.progress + 0.045) % 1;
  const targetAngle = track.startAngle - targetProgress * Math.PI * 2;
  const lane = Math.sin(raceTime * 1.4) * 18;
  const target = pointOnTrack(targetAngle, lane);
  const wantedRot = Math.atan2(target.y - ai.y, target.x - ai.x);
  const diff = turnToward(ai, wantedRot, spec.turn * 0.9 * dt);
  const targetSpeed = spec.max * (diff > 1.0 ? 0.58 : 0.92);
  ai.speed += spec.accel * 0.78 * dt;
  ai.speed = clamp(ai.speed, 0, targetSpeed);
}

function keepOnTrack(racer) {
  const a = nearestTrackAngle(racer.x, racer.y);
  const p = pointOnTrack(a);
  const dx = racer.x - p.x;
  const dy = racer.y - p.y;
  const d = Math.hypot(dx, dy);
  const half = track.width * 0.5;
  if (d <= half) return;
  const nx = dx / Math.max(0.001, d);
  const ny = dy / Math.max(0.001, d);
  racer.x = p.x + nx * half;
  racer.y = p.y + ny * half;
  racer.speed *= 0.78;
}

function moveRacer(racer, dt) {
  racer.boost = Math.max(0, racer.boost - dt);
  racer.x += Math.cos(racer.rot) * racer.speed * dt;
  racer.y += Math.sin(racer.rot) * racer.speed * dt;
  keepOnTrack(racer);
  updateProgress(racer);
}

function updateProgress(racer) {
  const angle = nearestTrackAngle(racer.x, racer.y);
  const p = normalizedProgress(angle);
  if (racer.lastProgress > 0.82 && p < 0.18 && racer.speed > 80 && !racer.finished) {
    racer.lap += 1;
    if (racer.lap >= totalLaps) {
      racer.finished = true;
      racer.finishTime = raceTime;
      racer.speed *= 0.55;
    }
  }
  racer.lastProgress = p;
  racer.progress = p;
}

function updateItems(dt) {
  itemBoxes.forEach((box) => {
    box.wait = Math.max(0, box.wait - dt);
    const pos = pointOnTrack(box.angle, 4);
    if (box.wait <= 0 && !heldItem && distance(player, pos) < 34) {
      heldItem = Math.random() > 0.42 ? "TURBO" : "SCHOCK";
      box.wait = 7;
    }
  });
  if ((keys.has(" ") || keys.has("Space")) && heldItem) {
    if (heldItem === "TURBO") player.boost = 1.55;
    if (heldItem === "SCHOCK" && !ai.finished) {
      ai.stun = 0.85;
      ai.speed *= 0.35;
    }
    heldItem = "";
  }
}

function distance(a, b) {
  return Math.hypot(a.x - b.x, a.y - b.y);
}

function updatePlaces() {
  const sorted = [...racers].sort((a, b) => {
    if (a.finished && b.finished) return a.finishTime - b.finishTime;
    if (a.finished) return -1;
    if (b.finished) return 1;
    return (b.lap + b.progress) - (a.lap + a.progress);
  });
  sorted.forEach((racer, idx) => {
    racer.place = idx + 1;
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
    winnerText = `${winner.name} gewinnt in ${winner.finishTime.toFixed(2)}s`;
    overlay.querySelector("strong").textContent = "RENNEN BEENDET";
    overlay.querySelector("span").textContent = winnerText;
    startButton.textContent = "NOCHMAL FAHREN";
    overlay.classList.remove("hidden");
  }
}

function drawTrack() {
  const grd = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
  grd.addColorStop(0, "#111824");
  grd.addColorStop(0.55, "#17202d");
  grd.addColorStop(1, "#0a0d12");
  ctx.fillStyle = grd;
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  ctx.fillStyle = "#123817";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.strokeStyle = "#2b2f34";
  ctx.lineWidth = track.width;
  ctx.beginPath();
  ctx.ellipse(center.x, center.y, track.rx, track.ry, 0, 0, Math.PI * 2);
  ctx.stroke();
  ctx.strokeStyle = "#d9d6c6";
  ctx.lineWidth = 5;
  ctx.beginPath();
  ctx.ellipse(center.x, center.y, track.rx + track.width * 0.5, track.ry + track.width * 0.24, 0, 0, Math.PI * 2);
  ctx.stroke();
  ctx.beginPath();
  ctx.ellipse(center.x, center.y, track.rx - track.width * 0.5, track.ry - track.width * 0.24, 0, 0, Math.PI * 2);
  ctx.stroke();

  ctx.strokeStyle = "rgba(255,255,255,0.35)";
  ctx.setLineDash([28, 28]);
  ctx.lineWidth = 4;
  ctx.beginPath();
  ctx.ellipse(center.x, center.y, track.rx, track.ry, 0, 0, Math.PI * 2);
  ctx.stroke();
  ctx.setLineDash([]);

  const start = pointOnTrack(track.startAngle);
  ctx.save();
  ctx.translate(start.x, start.y);
  ctx.rotate(0);
  for (let i = 0; i < 10; i++) {
    ctx.fillStyle = i % 2 ? "#101010" : "#f8f8f8";
    ctx.fillRect(-track.width * 0.5 + i * (track.width / 10), -8, track.width / 10, 16);
  }
  ctx.restore();
}

function drawBoxes() {
  itemBoxes.forEach((box) => {
    if (box.wait > 0) return;
    const pos = pointOnTrack(box.angle, 4);
    ctx.save();
    ctx.translate(pos.x, pos.y);
    ctx.rotate(performance.now() / 650);
    ctx.fillStyle = "#111824";
    ctx.fillRect(-16, -16, 32, 32);
    ctx.strokeStyle = "#36d8ff";
    ctx.lineWidth = 4;
    ctx.strokeRect(-16, -16, 32, 32);
    ctx.fillStyle = "#f3c744";
    ctx.font = "900 18px Arial";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText("?", 0, 1);
    ctx.restore();
  });
}

function drawRacer(racer) {
  const char = characters[racer.characterIndex];
  const spec = carTypes[racer.carIndex];
  ctx.save();
  ctx.translate(racer.x, racer.y);
  ctx.rotate(racer.rot);
  ctx.shadowColor = "rgba(0,0,0,0.55)";
  ctx.shadowBlur = 12;
  ctx.fillStyle = "#07090d";
  ctx.fillRect(-24, -14, 48, 28);
  ctx.shadowBlur = 0;
  ctx.fillStyle = spec.color;
  ctx.fillRect(-19, -11, 38, 22);
  ctx.fillStyle = char.color;
  ctx.beginPath();
  ctx.arc(-3, 0, 8, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(9, -7, 8, 14);
  ctx.fillStyle = "#111";
  ctx.fillRect(-21, -17, 11, 7);
  ctx.fillRect(-21, 10, 11, 7);
  ctx.fillRect(10, -17, 11, 7);
  ctx.fillRect(10, 10, 11, 7);
  if (racer.boost > 0) {
    ctx.fillStyle = "#ffe16a";
    ctx.fillRect(-35, -5, 12, 10);
  }
  ctx.restore();

  ctx.fillStyle = "#fff";
  ctx.font = "900 13px Arial";
  ctx.textAlign = "center";
  ctx.fillText(`${racer.name} ${char.name}`, racer.x, racer.y - 32);
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

function frame(t) {
  const dt = Math.min(0.033, (t - lastTime) / 1000 || 0);
  lastTime = t;
  update(dt);
  draw();
  requestAnimationFrame(frame);
}

function setSelection(group, index) {
  if (group === "character") selectedCharacter = index;
  if (group === "car") selectedCar = index;
  document.querySelectorAll(`[data-select="${group}"]`).forEach((button, i) => {
    button.classList.toggle("active", i === index);
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

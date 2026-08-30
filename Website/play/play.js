const canvas = document.querySelector("#game");
const ctx = canvas.getContext("2d");
const overlay = document.querySelector("#overlay");
const startButton = document.querySelector("#start-button");
const hudScore = document.querySelector("#hud-score");
const hudItem = document.querySelector("#hud-item");
const hudTime = document.querySelector("#hud-time");

const keys = new Set();
const arena = { w: 1280, h: 720, pad: 74 };
const boxSpawns = [
  { x: 180, y: 160 },
  { x: 1100, y: 160 },
  { x: 180, y: 560 },
  { x: 1100, y: 560 },
];

let running = false;
let lastTime = 0;
let timeLeft = 90;
let holder = -1;
let item = "";
let cooldown = 0;
let winnerText = "";

const player = makeCar(640, 540, -Math.PI / 2, "#f3c744", "DU");
const cars = [
  player,
  makeCar(310, 200, 0.4, "#36d8ff", "KI 1"),
  makeCar(980, 220, 2.8, "#ef3e32", "KI 2"),
  makeCar(640, 160, 1.4, "#4ade80", "KI 3"),
];
const boxes = boxSpawns.map((p) => ({ ...p, wait: 0 }));
const insignia = { x: 640, y: 360, spin: 0 };

function makeCar(x, y, rot, color, name) {
  return {
    x,
    y,
    px: x,
    py: y,
    rot,
    speed: 0,
    color,
    name,
    score: 0,
    boost: 0,
    stun: 0,
  };
}

function resetGame() {
  running = true;
  timeLeft = 90;
  holder = -1;
  item = "";
  cooldown = 0;
  winnerText = "";
  const starts = [
    [640, 540, -Math.PI / 2],
    [310, 200, 0.4],
    [980, 220, 2.8],
    [640, 160, 1.4],
  ];
  cars.forEach((car, i) => {
    car.x = starts[i][0];
    car.y = starts[i][1];
    car.px = car.x;
    car.py = car.y;
    car.rot = starts[i][2];
    car.speed = 0;
    car.score = 0;
    car.boost = 0;
    car.stun = 0;
  });
  boxes.forEach((box) => {
    box.wait = 0;
  });
  insignia.x = 640;
  insignia.y = 360;
  overlay.classList.add("hidden");
  canvas.focus();
}

function clamp(v, min, max) {
  return Math.max(min, Math.min(max, v));
}

function angleTo(from, to) {
  return Math.atan2(to.y - from.y, to.x - from.x);
}

function turnToward(car, target, amount) {
  let diff = target - car.rot;
  while (diff > Math.PI) diff -= Math.PI * 2;
  while (diff < -Math.PI) diff += Math.PI * 2;
  car.rot += clamp(diff, -amount, amount);
  return Math.abs(diff);
}

function dist(a, b) {
  const dx = a.x - b.x;
  const dy = a.y - b.y;
  return Math.hypot(dx, dy);
}

function updatePlayer(dt) {
  if (player.stun > 0) {
    player.stun -= dt;
    player.speed *= 0.91;
    return;
  }
  const gas = keys.has("ArrowUp") || keys.has("w") || keys.has("W");
  const brake = keys.has("ArrowDown") || keys.has("s") || keys.has("S");
  const left = keys.has("ArrowLeft") || keys.has("a") || keys.has("A");
  const right = keys.has("ArrowRight") || keys.has("d") || keys.has("D");
  const maxSpeed = player.boost > 0 ? 520 : 390;
  if (gas) player.speed += 740 * dt;
  if (brake) player.speed -= 610 * dt;
  if (!gas && !brake) player.speed *= 0.985;
  player.speed = clamp(player.speed, -170, maxSpeed);
  const steer = (player.speed >= 0 ? 1 : -1) * 3.25 * dt * clamp(Math.abs(player.speed) / 250, 0.25, 1);
  if (left) player.rot -= steer;
  if (right) player.rot += steer;
}

function updateAi(car, dt) {
  if (car.stun > 0) {
    car.stun -= dt;
    car.speed *= 0.9;
    return;
  }
  const hasBadge = cars[holder] === car;
  let target;
  if (hasBadge) {
    const nearest = cars.filter((c) => c !== car).sort((a, b) => dist(car, a) - dist(car, b))[0];
    const away = Math.atan2(car.y - nearest.y, car.x - nearest.x);
    target = {
      x: car.x + Math.cos(away) * 280,
      y: car.y + Math.sin(away) * 280,
    };
  } else if (holder >= 0) {
    target = cars[holder];
  } else {
    target = insignia;
  }

  target = {
    x: clamp(target.x, arena.pad + 38, arena.w - arena.pad - 38),
    y: clamp(target.y, arena.pad + 38, arena.h - arena.pad - 38),
  };

  const diff = turnToward(car, angleTo(car, target), 3.1 * dt);
  const limit = hasBadge ? 310 : 350;
  car.speed += 540 * dt;
  car.speed = clamp(car.speed, 0, limit * (diff > 1.2 ? 0.58 : 1));
}

function moveCar(car, dt) {
  car.boost = Math.max(0, car.boost - dt);
  car.px = car.x;
  car.py = car.y;
  car.x += Math.cos(car.rot) * car.speed * dt;
  car.y += Math.sin(car.rot) * car.speed * dt;
  if (car.x < arena.pad || car.x > arena.w - arena.pad) {
    car.x = clamp(car.x, arena.pad, arena.w - arena.pad);
    car.speed *= -0.35;
  }
  if (car.y < arena.pad || car.y > arena.h - arena.pad) {
    car.y = clamp(car.y, arena.pad, arena.h - arena.pad);
    car.speed *= -0.35;
  }
}

function updateItems(dt) {
  boxes.forEach((box) => {
    box.wait = Math.max(0, box.wait - dt);
    if (box.wait <= 0 && dist(player, box) < 38 && !item) {
      item = Math.random() > 0.45 ? "TURBO" : "BLITZ";
      box.wait = 5.5;
    }
  });
  if ((keys.has(" ") || keys.has("Space")) && item) {
    if (item === "TURBO") player.boost = 1.8;
    if (item === "BLITZ") {
      const target = cars.filter((c) => c !== player).sort((a, b) => dist(player, a) - dist(player, b))[0];
      if (target && dist(player, target) < 340) {
        target.stun = 1.0;
        if (holder >= 0 && cars[holder] === target) holder = 0;
      }
    }
    item = "";
  }
}

function updateInsignia(dt) {
  cooldown = Math.max(0, cooldown - dt);
  insignia.spin += dt * 5;
  if (holder < 0) {
    cars.forEach((car, i) => {
      if (holder < 0 && dist(car, insignia) < 42) holder = i;
    });
    return;
  }
  const h = cars[holder];
  insignia.x = h.x;
  insignia.y = h.y;
  h.score += dt;
  cars.forEach((car, i) => {
    if (i !== holder && cooldown <= 0 && dist(car, h) < 34) {
      holder = i;
      cooldown = 1.0;
    }
  });
}

function update(dt) {
  if (!running) return;
  timeLeft -= dt;
  updatePlayer(dt);
  cars.slice(1).forEach((car) => updateAi(car, dt));
  cars.forEach((car) => moveCar(car, dt));
  updateItems(dt);
  updateInsignia(dt);
  if (timeLeft <= 0 || cars.some((car) => car.score >= 20)) {
    running = false;
    const winner = [...cars].sort((a, b) => b.score - a.score)[0];
    winnerText = `${winner.name} gewinnt mit ${Math.floor(winner.score)} Punkten`;
    overlay.querySelector("strong").textContent = "RENNEN BEENDET";
    overlay.querySelector("span").textContent = winnerText;
    startButton.textContent = "NOCHMAL SPIELEN";
    overlay.classList.remove("hidden");
  }
}

function drawArena() {
  const grd = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
  grd.addColorStop(0, "#151b25");
  grd.addColorStop(0.45, "#202630");
  grd.addColorStop(1, "#101219");
  ctx.fillStyle = grd;
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  ctx.fillStyle = "#2b2f34";
  ctx.fillRect(arena.pad, arena.pad, arena.w - arena.pad * 2, arena.h - arena.pad * 2);
  for (let x = arena.pad; x <= arena.w - arena.pad; x += 60) {
    for (let y = arena.pad; y <= arena.h - arena.pad; y += 60) {
      ctx.fillStyle = (x / 60 + y / 60) % 2 ? "rgba(255,255,255,0.035)" : "rgba(0,0,0,0.08)";
      ctx.fillRect(x, y, 60, 60);
    }
  }

  ctx.strokeStyle = "#f3c744";
  ctx.lineWidth = 8;
  ctx.strokeRect(arena.pad, arena.pad, arena.w - arena.pad * 2, arena.h - arena.pad * 2);
  ctx.strokeStyle = "rgba(54,216,255,0.65)";
  ctx.lineWidth = 3;
  ctx.strokeRect(arena.pad + 16, arena.pad + 16, arena.w - arena.pad * 2 - 32, arena.h - arena.pad * 2 - 32);

  ctx.strokeStyle = "rgba(243,199,68,0.5)";
  ctx.lineWidth = 5;
  ctx.beginPath();
  ctx.moveTo(420, 360);
  ctx.lineTo(860, 360);
  ctx.moveTo(640, 160);
  ctx.lineTo(640, 560);
  ctx.stroke();
}

function drawBox(box) {
  if (box.wait > 0) return;
  ctx.save();
  ctx.translate(box.x, box.y);
  ctx.rotate(performance.now() / 550);
  ctx.fillStyle = "#141a23";
  ctx.fillRect(-18, -18, 36, 36);
  ctx.strokeStyle = "#36d8ff";
  ctx.lineWidth = 4;
  ctx.strokeRect(-18, -18, 36, 36);
  ctx.fillStyle = "#f3c744";
  ctx.font = "900 20px Arial";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText("?", 0, 1);
  ctx.restore();
}

function drawInsignia() {
  ctx.save();
  ctx.translate(insignia.x, insignia.y);
  ctx.rotate(insignia.spin);
  ctx.shadowColor = "#ffe16a";
  ctx.shadowBlur = 22;
  ctx.fillStyle = "#f3c744";
  star(0, 0, 26, 12, 8);
  ctx.fill();
  ctx.shadowBlur = 0;
  ctx.strokeStyle = "#fff0a3";
  ctx.lineWidth = 3;
  ctx.stroke();
  ctx.restore();
}

function star(x, y, outer, inner, points) {
  ctx.beginPath();
  for (let i = 0; i < points * 2; i++) {
    const a = -Math.PI / 2 + (i * Math.PI) / points;
    const r = i % 2 ? inner : outer;
    const px = x + Math.cos(a) * r;
    const py = y + Math.sin(a) * r;
    if (i === 0) ctx.moveTo(px, py);
    else ctx.lineTo(px, py);
  }
  ctx.closePath();
}

function drawCar(car, index) {
  ctx.save();
  ctx.translate(car.x, car.y);
  ctx.rotate(car.rot);
  ctx.shadowColor = "rgba(0,0,0,0.55)";
  ctx.shadowBlur = 12;
  ctx.fillStyle = "#07090d";
  ctx.fillRect(-22, -13, 44, 26);
  ctx.shadowBlur = 0;
  ctx.fillStyle = car.color;
  ctx.fillRect(-18, -10, 36, 20);
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(7, -7, 8, 14);
  ctx.fillStyle = "#111";
  ctx.fillRect(-19, -16, 10, 7);
  ctx.fillRect(-19, 9, 10, 7);
  ctx.fillRect(9, -16, 10, 7);
  ctx.fillRect(9, 9, 10, 7);
  if (holder === index) {
    ctx.strokeStyle = "#ffe16a";
    ctx.lineWidth = 4;
    ctx.beginPath();
    ctx.arc(0, 0, 29, 0, Math.PI * 2);
    ctx.stroke();
  }
  ctx.restore();

  ctx.fillStyle = "#fff";
  ctx.font = "900 13px Arial";
  ctx.textAlign = "center";
  ctx.fillText(car.name, car.x, car.y - 30);
}

function drawHud() {
  hudScore.textContent = `Score ${Math.floor(player.score)}/20`;
  hudItem.textContent = `Item ${item || "-"}`;
  hudTime.textContent = `${Math.max(0, Math.ceil(timeLeft))}s`;
}

function draw() {
  drawArena();
  boxes.forEach(drawBox);
  drawInsignia();
  cars.forEach(drawCar);
  drawHud();
}

function frame(t) {
  const dt = Math.min(0.033, (t - lastTime) / 1000 || 0);
  lastTime = t;
  update(dt);
  draw();
  requestAnimationFrame(frame);
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

startButton.addEventListener("click", resetGame);
draw();
requestAnimationFrame(frame);

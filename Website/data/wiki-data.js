const characters = [
  {
    name: "Mauz",
    unlock: "Start",
    speed: 7,
    acceleration: 8,
    color: "#f2d12e",
    role: "Ausgewogen und stark beim Starten."
  },
  {
    name: "Wauz",
    unlock: "Start",
    speed: 8,
    acceleration: 7,
    color: "#bf8c40",
    role: "Etwas schneller, bleibt aber leicht kontrollierbar."
  },
  {
    name: "Fuchs",
    unlock: "Level-Freischaltung",
    speed: 9,
    acceleration: 6,
    color: "#ff7426",
    role: "Sehr schnell, braucht aber saubere Kurven."
  },
  {
    name: "Hase",
    unlock: "Level-Freischaltung",
    speed: 6,
    acceleration: 9,
    color: "#ececec",
    role: "Top Beschleunigung nach Items, Crashs und engen Kurven."
  },
  {
    name: "Baer",
    unlock: "Level-Freischaltung",
    speed: 5,
    acceleration: 8,
    color: "#8c5c33",
    role: "Ruhiger Fahrer fuer stabile Linien."
  },
  {
    name: "Bot",
    unlock: "Level-Freischaltung",
    speed: 8,
    acceleration: 8,
    color: "#8cbff2",
    role: "Technisch stark und sehr gleichmaessig."
  }
];

const cars = [
  {
    name: "Standard",
    unlock: "Start",
    speed: 7,
    acceleration: 7,
    tag: "Allrounder",
    note: "Guter Einstieg fuer jede Strecke."
  },
  {
    name: "Sport",
    unlock: "Level-Freischaltung",
    speed: 9,
    acceleration: 7,
    tag: "Speed",
    note: "Schneller auf Geraden und gut fuer Oval oder lange Kurven."
  },
  {
    name: "Offroad",
    unlock: "Level-Freischaltung",
    speed: 6,
    acceleration: 9,
    tag: "Grip",
    note: "Stark beim Herausbeschleunigen nach engen Kurven."
  },
  {
    name: "Retro",
    unlock: "Level-Freischaltung",
    speed: 7,
    acceleration: 6,
    tag: "Classic",
    note: "Ein ruhiger alter Kart-Stil fuer sauberes Fahren."
  }
];

const tracks = [
  {
    name: "Oval",
    unlockLevel: 1,
    type: "Rennen",
    description: "Klassische ovale Strecke mit sanften Kurven, perfekt zum Lernen."
  },
  {
    name: "Quad",
    unlockLevel: 2,
    type: "Rennen",
    description: "Rechteckiges Layout mit scharfen Ecken und klaren Bremszonen."
  },
  {
    name: "Dreieck",
    unlockLevel: 3,
    type: "Rennen",
    description: "Drei extreme Kurven und viel Risiko beim Einlenken."
  },
  {
    name: "Acht",
    unlockLevel: 4,
    type: "Rennen",
    description: "Acht-foermige Strecke mit zwei Schleifen und wechselndem Rhythmus."
  },
  {
    name: "Chicane",
    unlockLevel: 5,
    type: "Rennen",
    description: "Viele Richtungswechsel fuer Fahrer mit gutem Timing."
  },
  {
    name: "Slalom",
    unlockLevel: 6,
    type: "Rennen",
    description: "Hindernis-Parcours mit Slalom-Toren und engen Entscheidungen."
  },
  {
    name: "Raeuber & Bulle",
    unlockLevel: 1,
    type: "Teammodus",
    description: "Offene Team-Map mit Gefaengnis, Befreiungsknopf und Rollen."
  }
];

const items = [
  {
    name: "Abknaller",
    kind: "Angriff",
    effect: "Fliegt hektisch zum Gegner, schiesst ihn kurz hoch und dreht ihn einmal um die Y-Achse."
  },
  {
    name: "Wirbler",
    kind: "Angriff",
    effect: "Trifft einen Gegner und laesst ihn einmal um die X-Achse wirbeln."
  },
  {
    name: "Turbo",
    kind: "Boost",
    effect: "Gibt kurz mehr Geschwindigkeit fuer Ueberholen oder Rettung nach Fehlern."
  },
  {
    name: "Schild",
    kind: "Schutz",
    effect: "Blockt eingehende Angriffe fuer kurze Zeit."
  },
  {
    name: "Frost",
    kind: "Angriff",
    effect: "Verlangsamt einen Gegner und stoert seine Linie."
  },
  {
    name: "Oelspur",
    kind: "Falle",
    effect: "Legt eine rutschige Stelle auf die Strecke."
  }
];

const modes = [
  {
    name: "Rennen",
    description: "Rundenrennen mit Items, KI, Minimap, Ghost-Fahrt nach dem Ziel und Highlight-Replay."
  },
  {
    name: "Raeuber & Bulle",
    description: "Teamspiel mit Raeubern, Bullen, Gefaengnis und Befreiungsknopf."
  }
];

module.exports = {
  characters,
  cars,
  tracks,
  items,
  modes
};

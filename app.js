const fs = require("fs");
const path = require("path");
const express = require("express");
const wikiData = require("./data/wiki-data");

function createApp(options = {}) {
  const app = express();
  const siteRoot = options.siteRoot || __dirname;
  const assetsDir = path.join(siteRoot, "assets");
  const indexFile = path.join(siteRoot, "index.html");
  const garageFile = path.join(siteRoot, "garage.html");
  const wikiFile = path.join(siteRoot, "wiki.html");
  const exeFile = path.join(assetsDir, "wauzkart.exe");
  const releaseDownloadUrl = process.env.WAUZKART_DOWNLOAD_URL || "https://github.com/Fetelker-Nils/wauzkart/releases/latest/download/wauzkart.exe";

  app.disable("x-powered-by");

  app.get("/api/health", (_req, res) => {
    res.json({
      ok: true,
      name: "Wauz Kart",
      download: "/download/wauzkart"
    });
  });

  app.get("/api/wiki", (_req, res) => {
    res.json(wikiData);
  });

  app.get("/download/wauzkart", (_req, res) => {
    if (!fs.existsSync(exeFile)) {
      res.redirect(302, releaseDownloadUrl);
      return;
    }

    res.download(exeFile, "wauzkart.exe");
  });

  app.get("/garage", (_req, res) => {
    res.sendFile(garageFile);
  });

  app.get("/wiki", (_req, res) => {
    res.sendFile(wikiFile);
  });

  app.use(
    "/assets",
    express.static(assetsDir, {
      maxAge: "1h",
      setHeaders(res, filePath) {
        if (filePath.endsWith(".exe")) {
          res.setHeader("Content-Type", "application/octet-stream");
          res.setHeader("Cache-Control", "public, max-age=300");
        }
      }
    })
  );

  app.use(
    express.static(siteRoot, {
      index: false,
      maxAge: "10m"
    })
  );

  app.get("*", (_req, res) => {
    res.sendFile(indexFile);
  });

  return app;
}

module.exports = createApp;

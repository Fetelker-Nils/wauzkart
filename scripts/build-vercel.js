const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const website = path.join(root, "Website");
const out = path.join(root, "dist");

function resetDir(dir) {
  fs.rmSync(dir, { recursive: true, force: true });
  fs.mkdirSync(dir, { recursive: true });
}

function copyFile(src, dst) {
  fs.mkdirSync(path.dirname(dst), { recursive: true });
  fs.copyFileSync(src, dst);
}

function copyDir(src, dst, shouldCopy = () => true) {
  if (!fs.existsSync(src)) {
    return;
  }
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    const srcPath = path.join(src, entry.name);
    const dstPath = path.join(dst, entry.name);
    if (!shouldCopy(srcPath, entry)) {
      continue;
    }
    if (entry.isDirectory()) {
      copyDir(srcPath, dstPath, shouldCopy);
    } else {
      copyFile(srcPath, dstPath);
    }
  }
}

resetDir(out);

for (const file of [
  "index.html",
  "garage.html",
  "wiki.html",
  "hilfe.html",
  "agb.html",
  "style.css",
  "script.js",
  "robots.txt",
  "sitemap.xml",
  "README.md",
  "RELEASE_NOTES.md"
]) {
  copyFile(path.join(website, file), path.join(out, file));
}

copyDir(path.join(website, "data"), path.join(out, "data"));
copyDir(path.join(website, "assets"), path.join(out, "assets"), (srcPath, entry) => {
  if (!entry.isFile()) {
    return true;
  }
  return path.extname(srcPath).toLowerCase() !== ".exe";
});

console.log("Wauz Kart static website copied to root dist");

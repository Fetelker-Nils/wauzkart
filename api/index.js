const path = require("path");
const createApp = require("../app");

module.exports = createApp({
  siteRoot: path.join(__dirname, "..")
});

import { readFile } from "node:fs/promises";

const supported = "2026.7.0";
const testBaseline = "2026.9.0";
const hacs = JSON.parse(await readFile("hacs.json", "utf8"));
const requirements = await readFile("requirements-dev.in", "utf8");
const documentation = await readFile("docs/compatibility.md", "utf8");

if (hacs.homeassistant !== supported) {
  throw new Error(`hacs.json must declare Home Assistant ${supported}`);
}
if (!requirements.includes(`homeassistant==${testBaseline}`)) {
  throw new Error(`requirements-dev.in must pin Home Assistant ${testBaseline}`);
}
if (!documentation.includes(`Home Assistant ${supported} or newer`)) {
  throw new Error("Compatibility documentation is out of sync");
}

console.log(
  `Home Assistant support floor is ${supported}; development/test baseline is ${testBaseline}`,
);

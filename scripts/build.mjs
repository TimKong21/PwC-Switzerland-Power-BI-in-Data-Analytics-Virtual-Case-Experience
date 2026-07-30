import { cp, mkdir, readFile, rm, stat } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const sourceDirectory = path.join(root, "site");
const outputDirectory = path.join(root, "dist");
const evidenceDirectory = path.join(root, "README assests");
const requiredPages = [
  "index.html",
  "service-operations.html",
  "customer-retention.html",
  "diversity-inclusion.html"
];

await rm(outputDirectory, { recursive: true, force: true });
await cp(sourceDirectory, outputDirectory, { recursive: true });
await mkdir(path.join(outputDirectory, "assets"), { recursive: true });
await cp(evidenceDirectory, path.join(outputDirectory, "assets", "evidence"), { recursive: true });

for (const page of requiredPages) {
  const pagePath = path.join(outputDirectory, page);
  await stat(pagePath);
  const markup = await readFile(pagePath, "utf8");
  if (/\b(?:href|src)\s*=\s*["']\//i.test(markup)) {
    throw new Error(`${page} contains a root-relative asset or link. Use relative URLs so the site works under its GitHub Pages project path.`);
  }
}

console.log(`Built static site in ${path.relative(root, outputDirectory)} for project-path hosting.`);

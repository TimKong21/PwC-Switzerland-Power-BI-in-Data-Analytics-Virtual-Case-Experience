import { createReadStream } from "node:fs";
import { access, stat } from "node:fs/promises";
import http from "node:http";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const outputDirectory = path.join(root, "dist");
const projectPath = `/${path.basename(root)}/`;
const port = Number(process.env.PORT || 4173);
const contentTypes = {
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".png": "image/png",
  ".svg": "image/svg+xml",
  ".webmanifest": "application/manifest+json"
};

await access(outputDirectory);

const server = http.createServer(async (request, response) => {
  const requestPath = decodeURIComponent(new URL(request.url, `http://${request.headers.host}`).pathname);
  if (!requestPath.startsWith(projectPath)) {
    response.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
    response.end(`Open the site at ${projectPath}`);
    return;
  }

  const relativePath = requestPath.slice(projectPath.length) || "index.html";
  const candidate = path.resolve(outputDirectory, relativePath);
  if (!candidate.startsWith(`${outputDirectory}${path.sep}`) && candidate !== outputDirectory) {
    response.writeHead(403, { "Content-Type": "text/plain; charset=utf-8" });
    response.end("Forbidden");
    return;
  }

  try {
    const details = await stat(candidate);
    const filePath = details.isDirectory() ? path.join(candidate, "index.html") : candidate;
    response.writeHead(200, { "Content-Type": contentTypes[path.extname(filePath)] || "application/octet-stream" });
    createReadStream(filePath).pipe(response);
  } catch {
    response.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
    response.end("Not found");
  }
});

server.listen(port, "127.0.0.1", () => {
  console.log(`Previewing production build at http://127.0.0.1:${port}${projectPath}`);
});

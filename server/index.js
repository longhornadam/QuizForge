// Node wrapper around the Python orchestrator.
// Accepts TXT/JSON/MD upload or pasted text, runs engine/orchestrator in a temp job,
// zips Finished_Exports, streams it, and cleans up.

const path = require("path");
const fs = require("fs");
const os = require("os");
const { spawn } = require("child_process");
const express = require("express");
const cors = require("cors");
const multer = require("multer");
const archiver = require("archiver");

const app = express();
const upload = multer({ storage: multer.memoryStorage() });
const PORT = process.env.PORT || 8000;
const PYTHON_BIN = process.env.PYTHON_BIN || "python";
const PROJECT_ROOT = path.resolve(__dirname, "..");
const STATIC_DIR =
  process.env.STATIC_DIR || path.join(__dirname, "dist"); // populated in container build
const HAS_STATIC = fs.existsSync(STATIC_DIR);

const BUILD_INFO = {
  sha: process.env.BUILD_SHA || "unknown",
  ref: process.env.BUILD_REF || "unknown",
  time: process.env.BUILD_TIME || "unknown",
};
const ALLOWED_UPLOAD_EXTENSIONS = [".txt", ".json", ".md"];

app.use(cors());
app.use(express.urlencoded({ extended: true }));
app.use(express.json({ limit: "2mb" }));

app.get("/api/health", (_req, res) => {
  res.json({ status: "ok", build: BUILD_INFO });
});

app.post("/api/quiz", upload.single("file"), async (req, res, next) => {
  let jobRoot;
  try {
    jobRoot = await fs.promises.mkdtemp(path.join(os.tmpdir(), "quizforge_job_"));
    const dropzone = path.join(jobRoot, "DropZone");
    const finished = path.join(jobRoot, "Finished_Exports");
    await fs.promises.mkdir(dropzone, { recursive: true });
    await fs.promises.mkdir(finished, { recursive: true });

    const inputPath = await persistInput(dropzone, req);
    await runOrchestrator(jobRoot);

    // If processing failed, return the fail prompt immediately instead of a download
    const failPrompt = await findFailPrompt(finished);
    if (failPrompt) {
      await fs.promises.rm(jobRoot, { recursive: true, force: true }).catch(() => {});
      return res
        .status(400)
        .json({ detail: failPrompt, note: "Processing failed; send this back to the AI to fix." });
    }

    await postProcessOutputs(finished);

    // Surface warnings (if any) from the main log
    const warnings = await extractWarnings(finished);

    // Prefer the quiz folder name for the ZIP filename
    const quizFolder = await findFirstSubfolder(finished);
    const zipName = sanitizeFilename(
      quizFolder ? `${quizFolder}.zip` : `${path.parse(inputPath).name}_quizforge.zip`
    );

    res.setHeader("Content-Type", "application/zip");
    res.setHeader("Content-Disposition", `attachment; filename="${zipName}"`);
    if (warnings.length) {
      const payload = encodeURIComponent(JSON.stringify(warnings));
      res.setHeader("X-QuizForge-Warnings", payload);
    }

    const archive = archiver("zip", { zlib: { level: 9 } });
    // Zip only the contents (avoid nesting in Finished_Exports/)
    archive.directory(finished, false);
    archive.on("error", (err) => {
      throw err;
    });

    // Cleanup after response flushes
    const cleanup = () => fs.promises.rm(jobRoot, { recursive: true, force: true });
    res.on("close", cleanup);
    res.on("error", cleanup);

    archive.pipe(res);
    archive.finalize();
  } catch (err) {
    if (jobRoot) {
      fs.promises.rm(jobRoot, { recursive: true, force: true }).catch(() => {});
    }
    next(err);
  }
});

// Serve built web assets when present (single-container deployment)
if (HAS_STATIC) {
  app.use(express.static(STATIC_DIR, { index: "index.html", maxAge: "1h" }));
  // Serve SPA index for any non-API route (GET/POST/etc.) so proxies that POST to "/" still get the app
  app.all("*", (req, res, next) => {
    if (req.path.startsWith("/api")) return next();
    res.sendFile(path.join(STATIC_DIR, "index.html"));
  });
} else {
  // Fallback root when static assets are missing
  app.all("*", (_req, res) => {
    res.json({
      status: "ok",
      message: "Static assets not found in container (SPA not bundled).",
      build: BUILD_INFO,
    });
  });
}

app.use((err, req, res, _next) => {
  console.error("QuizForge API error:", err);
  const message =
    typeof err?.message === "string"
      ? err.message
      : "QuizForge failed to process the request.";
  res.status(400).json({ detail: message });
});

app.listen(PORT, () => {
  console.log(`QuizForge API listening on ${PORT}`);
  if (HAS_STATIC) {
    console.log(`Serving static web UI from ${STATIC_DIR}`);
  }
});

function persistInput(dropzone, req) {
  return new Promise((resolve, reject) => {
    if (req.file && req.file.buffer?.length) {
      let filename;
      try {
        filename = normalizeUploadName(req.file.originalname);
      } catch (err) {
        return reject(err);
      }
      const target = path.join(dropzone, filename);
      fs.writeFile(target, req.file.buffer, (err) => {
        if (err) return reject(err);
        resolve(target);
      });
      return;
    }

    const text = (req.body?.text || "").trim();
    if (text.length) {
      const target = path.join(dropzone, "pasted_quiz.txt");
      fs.writeFile(target, text, { encoding: "utf-8" }, (err) => {
        if (err) return reject(err);
        resolve(target);
      });
      return;
    }

    reject(new Error(uploadRequirementMessage()));
  });
}

function runOrchestrator(jobRoot) {
  return new Promise((resolve, reject) => {
    const args = ["-m", "engine.orchestrator", jobRoot];
    const proc = spawn(PYTHON_BIN, args, { cwd: PROJECT_ROOT });

    let stderr = "";
    proc.stderr.on("data", (chunk) => {
      stderr += chunk.toString();
    });

    proc.on("close", (code) => {
      if (code === 0) return resolve();
      reject(new Error(stderr.trim() || `Orchestrator exited with code ${code}`));
    });

    proc.on("error", (err) => {
      reject(err);
    });
  });
}

function sanitizeFilename(name) {
  return name.replace(/[^a-zA-Z0-9._-]/g, "_");
}

function normalizeUploadName(originalName) {
  const fallback = "uploaded_quiz.txt";
  const safeName = sanitizeFilename(originalName || fallback);
  const ext = path.extname(safeName).toLowerCase();

  if (!ext) {
    return `${safeName}.txt`;
  }

  if (!ALLOWED_UPLOAD_EXTENSIONS.includes(ext)) {
    throw new Error(uploadRequirementMessage());
  }

  return safeName;
}

function uploadRequirementMessage() {
  const allowed = [...ALLOWED_UPLOAD_EXTENSIONS];
  if (allowed.length === 1) return `Provide a ${allowed[0]} file or paste quiz text.`;
  const last = allowed.pop();
  return `Provide a ${allowed.join(", ")} or ${last} file, or paste quiz text.`;
}

async function findFirstSubfolder(dir) {
  const entries = await fs.promises.readdir(dir, { withFileTypes: true });
  const folder = entries.find((e) => e.isDirectory());
  return folder ? folder.name : null;
}

async function findFailPrompt(dir) {
  const entries = await fs.promises.readdir(dir, { withFileTypes: true });
  for (const entry of entries) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      const nested = await findFailPrompt(full);
      if (nested) return nested;
    } else if (
      entry.isFile() &&
      entry.name.toUpperCase().endsWith("_FAIL_REVISE_WITH_AI.TXT")
    ) {
      return fs.promises.readFile(full, { encoding: "utf-8" });
    }
  }
  return null;
}

async function postProcessOutputs(finishedDir) {
  // Remove noisy .log files; keep user-facing TXT logs
  const entries = await fs.promises.readdir(finishedDir, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = path.join(finishedDir, entry.name);
    if (entry.isDirectory()) {
      await postProcessOutputs(fullPath);
    } else if (entry.isFile()) {
      if (entry.name.toLowerCase().endsWith(".log")) {
        await fs.promises.rm(fullPath).catch(() => {});
      } else if (
        entry.name.toLowerCase().endsWith(".docx") &&
        !entry.name.toUpperCase().includes("_KEY") &&
        !entry.name.toUpperCase().includes("_RATIONALE") &&
        !entry.name.toUpperCase().includes("_PRINT")
      ) {
        const { name, dir } = path.parse(fullPath);
        const newName = `${name}_PRINT.docx`;
        await fs.promises.rename(fullPath, path.join(dir, newName)).catch(() => {});
      }
    }
  }
}

async function extractWarnings(finishedDir) {
  // Find the main quiz folder and log_<STATUS>_FIXED.txt, then parse WARNINGS block
  const warnings = [];
  const quizFolder = await findFirstSubfolder(finishedDir);
  if (!quizFolder) return warnings;

  const folderPath = path.join(finishedDir, quizFolder);
  const entries = await fs.promises.readdir(folderPath, { withFileTypes: true });
  const logEntry = entries.find(
    (e) => e.isFile() && e.name.toLowerCase().startsWith("log_") && e.name.toLowerCase().endsWith(".txt")
  );
  if (!logEntry) return warnings;

  const logPath = path.join(folderPath, logEntry.name);
  const text = await fs.promises.readFile(logPath, { encoding: "utf-8" });
  const lines = text.split(/\r?\n/);
  const start = lines.findIndex((l) => l.trim().toUpperCase().startsWith("WARNINGS:"));
  if (start === -1) return warnings;
  for (let i = start + 1; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line || line.startsWith("===")) break;
    if (/^\d+\.\s+/g.test(line)) {
      warnings.push(line.replace(/^\d+\.\s+/, "").trim());
    }
  }
  return warnings;
}

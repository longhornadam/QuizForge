// Node wrapper around the Python orchestrator.
// Accepts TXT upload or pasted text, runs engine/orchestrator in a temp job,
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

app.use(cors());
app.use(express.urlencoded({ extended: true }));
app.use(express.json({ limit: "2mb" }));

app.get("/api/health", (_req, res) => {
  res.json({ status: "ok" });
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

    await postProcessOutputs(finished);

    // Prefer the quiz folder name for the ZIP filename
    const quizFolder = await findFirstSubfolder(finished);
    const zipName = sanitizeFilename(
      quizFolder ? `${quizFolder}.zip` : `${path.parse(inputPath).name}_quizforge.zip`
    );

    res.setHeader("Content-Type", "application/zip");
    res.setHeader("Content-Disposition", `attachment; filename="${zipName}"`);

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
  app.get("*", (req, res, next) => {
    if (req.path.startsWith("/api")) return next();
    res.sendFile(path.join(STATIC_DIR, "index.html"));
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
      const filename = sanitizeFilename(req.file.originalname || "uploaded_quiz.txt");
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

    reject(new Error("Provide a .txt file or paste quiz text."));
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

async function findFirstSubfolder(dir) {
  const entries = await fs.promises.readdir(dir, { withFileTypes: true });
  const folder = entries.find((e) => e.isDirectory());
  return folder ? folder.name : null;
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
